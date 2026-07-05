"""FraudEngine — the SentinelPulse mule-detection engine (WP-5M).

Blends two independent voices into one 0-100 mule-risk score per account:

  * a **typology leg** — the 8 deterministic detectors in ``typologies.py``, each
    carrying the concrete transaction evidence that triggered it (the citation
    backbone WP-5A gates on);
  * an **anomaly leg** — an Isolation Forest over a BADNESS-oriented behavioural
    space, scored as EXCESS over the clearly-genuine cohort. This mirrors the
    platform's ``app/ml/models/anomaly.py`` pattern exactly: features oriented so
    a benign account sits at the origin, "normal" anchored at the 90th percentile
    of the zero-badness set so only true outliers rise.

    mule_risk = 0.55 * typology_max_blend + 0.45 * (100 * anomaly_excess)

The typology leg leads (interpretable, evidence-bearing) while the unsupervised
leg gives a meaningful independent say. Bands: Alert >= 65, Review >= 45,
Clear < 45. Ring discovery (``expand_ring``) is pure-python BFS over suspicious
edges (shared device OR account-to-account high-volume link) with a deterministic
circular layout — NO networkx (constraint D5).

The engine reads ONLY the two engine-input CSVs; it never touches the eval
labels file. ``STATE_VERSION`` guards the prefit pickle (ScoringEngine pattern).
"""
from __future__ import annotations

import pickle
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from ..data_gen.build import ACCOUNTS_CSV, DATA_DIR, TRANSACTIONS_CSV
from . import features as F
from . import typologies as TY
from .typologies import TypologyHit

# ---- blend + band constants (tuned once on the synthetic desk, see report) ----
W_TYPOLOGY = 0.55          # weight on the interpretable, evidence-bearing leg
W_ANOMALY = 0.45           # weight on the unsupervised cross-check
BAND_ALERT = 65.0
BAND_REVIEW = 45.0

# BFS edge thresholds for ring expansion.
_LINK_MIN_TXNS = 2         # >=2 transfers between two accounts = a suspicious link
_LINK_MIN_AMOUNT = 20_000  # or a single high-value transfer
_MAX_RING_NODES = 40       # safety cap on a discovered component


# --------------------------------------------------------------------------- #
# anomaly leg — badness-oriented, genuine-anchored (mirrors app/ml/models/anomaly)
# --------------------------------------------------------------------------- #
def _badness_frame(fm: pd.DataFrame) -> pd.DataFrame:
    """Behavioural signals oriented so 0 = benign and higher = an active mule tell.

    Deliberately continuous (velocity/ratio flavoured) so the leg is a genuine
    second opinion to the discrete typology rules rather than a copy of them.
    """
    idx = fm.index
    b = pd.DataFrame(index=idx)
    b["b_passthrough"] = fm["passthrough_share"].clip(0, 1)
    b["b_threshold"] = fm["threshold_hug_share"].clip(0, 1)
    b["b_round"] = fm["round_amount_share"].clip(0, 1)
    b["b_odd"] = fm["odd_hours_share"].clip(0, 1)
    b["b_dormancy"] = fm["dormancy_burst_score"].clip(0, 1)
    b["b_device"] = (fm["device_sharing_degree"] / 6.0).clip(0, 1)
    # KYC throughput badness only for personal accounts (business turnover is
    # legitimately high) — matches the typology detector's stance.
    personal = fm["is_current"] < 0.5
    b["b_kyc"] = np.where(personal,
                          ((fm["kyc_mismatch_ratio"] - 3.0) / 7.0).clip(0, 1), 0.0)
    # consolidation badness: many payers in, few sinks out
    b["b_consolidation"] = np.where(
        (fm["fan_in_degree"] >= 10) & (fm["fan_out_degree"] <= 8),
        ((fm["consolidation_ratio"] - 2.5) / 5.0).clip(0, 1), 0.0)
    # young account carrying volume
    b["b_newvel"] = np.where(fm["age_days"] < 30,
                             (fm["txn_per_active_day"] / 6.0).clip(0, 1), 0.0)
    return b.fillna(0.0)


class _AnomalyLeg:
    def __init__(self, n_estimators: int = 300, seed: int = 42):
        self.n_estimators = n_estimators
        self.seed = seed
        self.scaler = StandardScaler()
        self.model: Optional[IsolationForest] = None
        self.features_: List[str] = []
        self._normal_hi = 0.0
        self._anom_hi = 1.0

    def fit(self, fm: pd.DataFrame) -> "_AnomalyLeg":
        B = _badness_frame(fm)
        self.features_ = list(B.columns)
        Xs = self.scaler.fit_transform(B)
        self.model = IsolationForest(n_estimators=self.n_estimators,
                                     random_state=self.seed).fit(Xs)
        anom = -self.model.score_samples(Xs)
        genuine = B.sum(axis=1).to_numpy() < 1e-9
        base = anom[genuine] if genuine.any() else anom
        self._normal_hi = float(np.percentile(base, 90))
        self._anom_hi = float(np.percentile(anom, 99))
        if self._anom_hi <= self._normal_hi:
            self._anom_hi = self._normal_hi + 1e-6
        return self

    def excess(self, fm: pd.DataFrame) -> np.ndarray:
        B = _badness_frame(fm)
        anom = -self.model.score_samples(self.scaler.transform(B))
        return np.clip((anom - self._normal_hi) / (self._anom_hi - self._normal_hi),
                       0.0, 1.0)


# --------------------------------------------------------------------------- #
# typology leg blend
# --------------------------------------------------------------------------- #
def typology_max_blend(hits: List[TypologyHit]) -> float:
    """0-100 typology strength: the strongest signal, reinforced by the second.

    A single strong tell shouldn't be diluted, but two corroborating typologies
    are stronger evidence than one — so blend the top two (0.75 / 0.25).
    """
    if not hits:
        return 0.0
    scores = sorted((h.score for h in hits), reverse=True)
    top1 = scores[0]
    top2 = scores[1] if len(scores) > 1 else 0.0
    return float(min(100.0, 0.75 * top1 + 0.25 * top2))


class FraudEngine:
    # Bump when the pickled shape changes so a stale pickle is refit, not crashed.
    STATE_VERSION = 1

    def __init__(self, seed: int = 42):
        self.seed = seed
        self.anomaly = _AnomalyLeg(seed=seed)
        self.feature_matrix: pd.DataFrame | None = None
        self._ledgers: Dict[str, F.AccountLedger] = {}
        self._device_accounts: Dict[str, set] = {}
        self._hits: Dict[str, List[TypologyHit]] = {}
        self._scored: pd.DataFrame | None = None
        self._link_index: Dict[str, Dict[str, dict]] = {}
        self._accounts: set = set()

    # ------------------------------------------------------------------ fit
    def fit(self, data_dir: Path | str = DATA_DIR) -> "FraudEngine":
        data_dir = Path(data_dir)
        accounts = pd.read_csv(data_dir / ACCOUNTS_CSV, dtype=str)
        transactions = pd.read_csv(data_dir / TRANSACTIONS_CSV)
        return self.fit_frames(accounts, transactions)

    def fit_frames(self, accounts: pd.DataFrame,
                   transactions: pd.DataFrame) -> "FraudEngine":
        self._accounts = set(accounts["account_id"].astype(str))
        self._ledgers = F.prepare_ledgers(accounts, transactions)

        # global device -> accounts map + per-account sharing degree
        dev_accts: Dict[str, set] = {}
        tx_dev = transactions[["account_id", "device_id"]].astype(str)
        for dev, g in tx_dev.groupby("device_id"):
            dev_accts[dev] = set(g["account_id"])
        self._device_accounts = dev_accts
        degree: Dict[str, int] = {}
        for aid, led in self._ledgers.items():
            co = set()
            for dev in np.unique(led.device):
                co |= dev_accts.get(dev, set())
            co.discard(aid)
            degree[aid] = len(co)

        self.feature_matrix = F.build_feature_matrix(self._ledgers, degree)
        self.anomaly.fit(self.feature_matrix)

        # typology hits per account (evidence retained for citation gating)
        ctx = {"device_accounts": self._device_accounts}
        self._hits = {aid: TY.detect_all(led, ctx)
                      for aid, led in self._ledgers.items()}

        # account-to-account link index (for ring BFS) — intra-universe edges only
        self._build_link_index(transactions)

        self._scored = self._score_all()
        return self

    # --------------------------------------------------------------- scoring
    def _score_all(self) -> pd.DataFrame:
        fm = self.feature_matrix
        excess = self.anomaly.excess(fm)
        excess_by = dict(zip(fm.index, excess))
        rows = []
        for aid in fm.index:
            hits = self._hits.get(aid, [])
            typ = typology_max_blend(hits)
            anom = float(excess_by[aid])
            score = W_TYPOLOGY * typ + W_ANOMALY * (100.0 * anom)
            score = float(np.clip(score, 0.0, 100.0))
            rows.append({
                "account": aid,
                "score": round(score, 1),
                "band": self._band(score),
                "typology_component": round(typ, 1),
                "anomaly_component": round(100.0 * anom, 1),
                "n_typologies": len(hits),
                "typologies": [h.name for h in hits],
            })
        df = pd.DataFrame(rows).set_index("account", drop=False)
        return df.sort_values("score", ascending=False)

    @staticmethod
    def _band(score: float) -> str:
        if score >= BAND_ALERT:
            return "Alert"
        if score >= BAND_REVIEW:
            return "Review"
        return "Clear"

    def score_accounts(self) -> pd.DataFrame:
        """Account-indexed scores. Columns: account, score, band,
        typology_component, anomaly_component, n_typologies, typologies (list)."""
        if self._scored is None:
            raise RuntimeError("FraudEngine.fit() must run before score_accounts()")
        return self._scored.copy()

    def typology_hits(self, account_id: str) -> List[TypologyHit]:
        """The fired ``TypologyHit`` objects (with evidence) for one account."""
        return list(self._hits.get(account_id, []))

    def account_row(self, account_id: str) -> dict:
        """Single account's score row as a plain dict (score/band/components)."""
        return self._scored.loc[account_id].to_dict()

    # --------------------------------------------------------- ring expansion
    def _build_link_index(self, transactions: pd.DataFrame) -> None:
        """Aggregate account-to-account edges: count + total amount + shared device."""
        tx = transactions.copy()
        tx["account_id"] = tx["account_id"].astype(str)
        tx["counterparty_id"] = tx["counterparty_id"].astype(str)
        intra = tx[tx["counterparty_id"].isin(self._accounts)]
        idx: Dict[str, Dict[str, dict]] = {}
        for (a, b), g in intra.groupby(["account_id", "counterparty_id"]):
            if a == b:
                continue
            idx.setdefault(a, {})[b] = {
                "count": int(len(g)),
                "amount": float(g["amount"].sum()),
                "devices": set(g["device_id"].astype(str)),
            }
        self._link_index = idx

    def _suspicious_neighbours(self, aid: str) -> Dict[str, dict]:
        """Neighbour account -> edge attrs, for edges deemed suspicious."""
        out: Dict[str, dict] = {}
        led = self._ledgers.get(aid)
        my_devs = set(np.unique(led.device)) if led is not None else set()
        # device-shared neighbours (accounts on a >=3-account device)
        for dev in my_devs:
            accts = self._device_accounts.get(dev, set())
            if len(accts) >= 3:
                for other in accts:
                    if other != aid:
                        e = out.setdefault(other, {"type": set(), "weight": 0.0})
                        e["type"].add("device")
                        e["weight"] += 1.0
        # high-volume transfer neighbours (either direction)
        for other, attr in self._link_index.get(aid, {}).items():
            if attr["count"] >= _LINK_MIN_TXNS or attr["amount"] >= _LINK_MIN_AMOUNT:
                e = out.setdefault(other, {"type": set(), "weight": 0.0})
                e["type"].add("transfer")
                e["weight"] += attr["amount"]
        for a2, nbrs in self._link_index.items():
            if aid in nbrs:
                attr = nbrs[aid]
                if attr["count"] >= _LINK_MIN_TXNS or attr["amount"] >= _LINK_MIN_AMOUNT:
                    e = out.setdefault(a2, {"type": set(), "weight": 0.0})
                    e["type"].add("transfer")
                    e["weight"] += attr["amount"]
        return out

    def expand_ring(self, account_id: str) -> dict:
        """Pure-python BFS over suspicious edges from ``account_id``.

        Returns::

            {
              "seed": account_id,
              "members": [account_id, ...],          # component (incl. seed)
              "edges": [{"source","target","type","weight"}, ...],
              "layout": {account_id: {"x": float, "y": float}, ...},
            }

        Edges: a shared device (>=3-account cluster) OR an account-to-account
        high-volume transfer link. Deterministic circular layout (seed centred).
        """
        seen = {account_id}
        order = [account_id]
        queue = [account_id]
        edges: List[dict] = []
        edge_seen = set()
        while queue and len(order) < _MAX_RING_NODES:
            cur = queue.pop(0)
            for nb, attr in sorted(self._suspicious_neighbours(cur).items()):
                key = tuple(sorted((cur, nb)))
                if key not in edge_seen:
                    edge_seen.add(key)
                    edges.append({"source": key[0], "target": key[1],
                                  "type": "device" if "device" in attr["type"] else "transfer",
                                  "weight": round(float(attr["weight"]), 2)})
                if nb not in seen and len(order) < _MAX_RING_NODES:
                    seen.add(nb)
                    order.append(nb)
                    queue.append(nb)
        members = sorted(order)
        layout = self._layout(account_id, members)
        # keep only edges whose endpoints are both in the membership
        mset = set(members)
        edges = [e for e in edges if e["source"] in mset and e["target"] in mset]
        return {"seed": account_id, "members": members,
                "edges": sorted(edges, key=lambda e: (e["source"], e["target"])),
                "layout": layout}

    @staticmethod
    def _layout(seed: str, members: List[str]) -> Dict[str, dict]:
        """Deterministic circular layout: seed at the centre, others on a ring."""
        others = [m for m in members if m != seed]
        coords: Dict[str, dict] = {seed: {"x": 0.0, "y": 0.0}}
        n = max(len(others), 1)
        for i, m in enumerate(others):
            theta = 2.0 * np.pi * i / n
            coords[m] = {"x": round(float(np.cos(theta)), 6),
                         "y": round(float(np.sin(theta)), 6)}
        return coords

    # ------------------------------------------------------------- persistence
    def __getstate__(self):
        state = self.__dict__.copy()
        state["_state_version"] = FraudEngine.STATE_VERSION
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def save(self, path: Path | str = None) -> "FraudEngine":
        path = Path(path) if path else ENGINE_PICKLE
        with open(path, "wb") as fh:
            pickle.dump(self, fh)
        return self


ENGINE_PICKLE = DATA_DIR / "fraud_engine.pkl"

_ENGINE: FraudEngine | None = None


def _load_prefit() -> FraudEngine | None:
    """Load the build-time pre-fit engine iff it isn't stale vs the input CSVs."""
    tx = DATA_DIR / TRANSACTIONS_CSV
    try:
        if not (ENGINE_PICKLE.exists() and tx.exists()):
            return None
        if ENGINE_PICKLE.stat().st_mtime < tx.stat().st_mtime:
            return None
        with open(ENGINE_PICKLE, "rb") as fh:
            obj = pickle.load(fh)
        if getattr(obj, "_state_version", None) != FraudEngine.STATE_VERSION:
            return None
        return obj
    except Exception:
        return None


def get_engine() -> FraudEngine:
    """Cached singleton: pre-fit pickle when fresh, else fit from the CSVs."""
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = _load_prefit() or FraudEngine().fit()
    return _ENGINE


def prefit() -> FraudEngine:
    """Fit and pickle the engine next to the data (build-time warm). Idempotent:
    skips the fit when a fresh, current-version pickle already exists."""
    existing = _load_prefit()
    if existing is not None:
        return existing
    return FraudEngine().fit().save()


# WP-5A: alias so central wiring can warm this like the other engines.
warm = prefit
