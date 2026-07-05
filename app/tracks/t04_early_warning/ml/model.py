"""EWSEngine — Track-04 portfolio early-warning model (WP-4M spec §Build.3).

Mirrors the shape of `app.ml.engine.ScoringEngine` (fit / STATE_VERSION pickle /
version-guarded prefit load) but over the monthly loan panel rather than the
cross-sectional cohort. Two models share one snapshot pipeline and one banding
rule so the comparison is honest:

  * **EWS** — monotonic LightGBM on repayment + alt-data features, `default_within_12m`.
  * **baseline** — the "internal SAJAG-style stand-in": the SAME pipeline but
    repayment-features-only and `default_within_3m`. It can only see EMIs bounce,
    so it lights up late; EWS reads the alt-data footprint and warns early.

Both reuse the platform ML kit read-only: `MonotonicGBM` (monotone constraints +
`PostHocCalibrator` wired inside it). We override the GBM's `health_dirs` instance
attribute with the EWS direction table (core is not modified).

Leakage discipline: features come from `features.build_snapshots` (causal window
guard); labels are attached HERE from the eval-only labels file and never leak
into the feature matrix; post-default snapshots are dropped; the train/holdout
split is entity-level with an asserted empty intersection.
"""
from __future__ import annotations

import pickle
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.ml.models.gbm import MonotonicGBM

from ..data_gen import paths
from .features import (BASELINE_FEATURES, FEATURE_COLS, FEATURE_DIRECTIONS,
                       FEATURE_LABELS, build_snapshots)
from . import ews_metrics

# Demo archetypes are forced into TRAIN so they are never silently used to report
# holdout metrics (same subtle-leakage guard as app.ml.eval.holdout).
ARCHETYPE_IDS = {
    "TEXTILE_MANUFACTURER", "RETAIL_KIRANA", "RESTAURANT",
    "IT_SERVICES", "AUTO_COMPONENTS", "LOGISTICS",
}
_SEED = 42


def _load_tables(data_dir=None) -> Dict[str, pd.DataFrame]:
    """Read the four panel CSVs (building them first if missing)."""
    from ..data_gen import build as _build
    _build.ensure_panel()
    d = data_dir or paths.DATA_DIR
    return {
        "loan_book": pd.read_csv(d / "loan_book.csv"),
        "repayment_history": pd.read_csv(d / "repayment_history.csv"),
        "altdata_monthly": pd.read_csv(d / "altdata_monthly.csv"),
        "default_labels": pd.read_csv(d / "default_labels.csv"),
    }


def _entity_split(entities: List[str], test_size: float = 0.3, seed: int = _SEED):
    """Entity-level split; demo archetypes are pinned into train."""
    ents = sorted(entities)
    demo = [e for e in ents if e in ARCHETYPE_IDS]
    pool = [e for e in ents if e not in ARCHETYPE_IDS]
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(pool))
    n_hold = int(round(len(pool) * test_size))
    hold = {pool[i] for i in perm[:n_hold]}
    train = set(pool) - hold
    train |= set(demo)
    return train, hold


class EWSEngine:
    # Bump when the pickled state shape changes (see _load_prefit()).
    STATE_VERSION = 1

    # Band thresholds on the CALIBRATED PD (tunable constants; WP-4M §Build.3).
    # Same rule applied to both models — the comparison is "same alerting policy,
    # EWS just sees more signal". Tuned once against the synthetic book to give a
    # sensible demo mix (~7% Red / ~13% Amber on live loans): Red stays at the
    # spec's 0.30 (the high-PD cluster). Amber is dropped from 0.12 to 0.10 because
    # isotonic calibration parks the "elevated" cohort on a ~0.113 plateau that
    # would otherwise fall just under a 0.12 cut, leaving Amber empty. See report.
    RED_THRESHOLD = 0.30
    AMBER_THRESHOLD = 0.10

    def __init__(self, red: Optional[float] = None, amber: Optional[float] = None):
        self.red = float(self.RED_THRESHOLD if red is None else red)
        self.amber = float(self.AMBER_THRESHOLD if amber is None else amber)
        self.feature_cols = list(FEATURE_COLS)
        self.baseline_cols = list(BASELINE_FEATURES)

        self.gbm = MonotonicGBM()
        self.gbm.health_dirs = dict(FEATURE_DIRECTIONS)          # override core map
        self.baseline = MonotonicGBM()
        self.baseline.health_dirs = {k: FEATURE_DIRECTIONS[k] for k in BASELINE_FEATURES}

        # populated by fit()
        self._snaps: pd.DataFrame | None = None
        self._loan_book: pd.DataFrame | None = None
        self._first_alerts: Dict[str, Dict[str, Optional[int]]] = {}
        self._default_month: Dict[str, Optional[int]] = {}
        self._is_defaulter: Dict[str, int] = {}
        self._train_entities: set = set()
        self._holdout_entities: set = set()
        self._feat_mean: pd.Series | None = None
        self._feat_std: pd.Series | None = None
        self._eval: Dict[str, object] = {}
        self._portfolio: Dict[str, object] = {}

    # ------------------------------------------------------------------ labels
    @staticmethod
    def _parse_default_month(val) -> Optional[int]:
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return None
        s = str(val).strip()
        if s == "" or s.lower() == "nan":
            return None
        return int(float(s))

    def _attach_labels(self, snaps: pd.DataFrame, labels: pd.DataFrame) -> pd.DataFrame:
        """Add default_within_12m / _3m; drop post-default snapshots. Label-only
        fields (default_month/ramp_start/lead_alt) are consumed HERE and never
        written back into the feature matrix."""
        dm = {r.entity_id: self._parse_default_month(r.default_month)
              for r in labels.itertuples()}
        isd = {r.entity_id: int(r.is_defaulter) for r in labels.itertuples()}
        self._default_month = dm
        self._is_defaulter = isd

        keep, y12, y3 = [], [], []
        for r in snaps.itertuples():
            d = dm.get(r.entity_id)
            if d is not None and r.as_of >= d:
                keep.append(False)                 # drop at/after default
                y12.append(0); y3.append(0)
                continue
            keep.append(True)
            if isd.get(r.entity_id, 0) == 1 and d is not None:
                lead = d - r.as_of
                y12.append(int(0 < lead <= 12))
                y3.append(int(0 < lead <= 3))
            else:
                y12.append(0); y3.append(0)
        out = snaps.copy()
        out["default_within_12m"] = y12
        out["default_within_3m"] = y3
        return out[pd.Series(keep, index=out.index).to_numpy()].reset_index(drop=True)

    # --------------------------------------------------------------------- fit
    def fit(self, data_dir=None) -> "EWSEngine":
        t = _load_tables(data_dir)
        lb, rep, alt, lab = (t["loan_book"], t["repayment_history"],
                             t["altdata_monthly"], t["default_labels"])
        self._loan_book = lb

        snaps = build_snapshots(lb, rep, alt)
        snaps = self._attach_labels(snaps, lab)

        train_ent, hold_ent = _entity_split(snaps["entity_id"].unique().tolist())
        assert not (train_ent & hold_ent), "entity split leaked across train/holdout"
        self._train_entities, self._holdout_entities = train_ent, hold_ent
        tr = snaps[snaps["entity_id"].isin(train_ent)]

        # Fit EWS (full feature set, 12m) and baseline (repayment-only, 3m).
        self.gbm.fit(tr[self.feature_cols], tr["default_within_12m"].to_numpy())
        self.baseline.fit(tr[self.baseline_cols], tr["default_within_3m"].to_numpy())

        # Score every snapshot for trajectories, banding and first-alerts.
        snaps["ews_pd"] = self.gbm.predict_pd(snaps[self.feature_cols])
        snaps["baseline_pd"] = self.baseline.predict_pd(snaps[self.baseline_cols])
        snaps["ews_band"] = [self.band(p) for p in snaps["ews_pd"]]
        snaps["baseline_band"] = [self.band(p) for p in snaps["baseline_pd"]]
        self._snaps = snaps

        # Reason-code population stats (train only, avoids peeking at holdout).
        self._feat_mean = tr[self.feature_cols].mean()
        self._feat_std = tr[self.feature_cols].std(ddof=0).replace(0.0, 1.0)

        # First-alert months (chronological first Red per model, per entity).
        self._first_alerts = self._compute_first_alerts(snaps)

        # Holdout eval + portfolio snapshot.
        self._eval = ews_metrics.compute_scorecard(self, snaps)
        self._portfolio = self._build_portfolio(snaps)
        return self

    # ------------------------------------------------------------------ bands
    def band(self, pd_val: float) -> str:
        if pd_val >= self.red:
            return "Red"
        if pd_val >= self.amber:
            return "Amber"
        return "Green"

    # ----------------------------------------------------------- first alerts
    def _compute_first_alerts(self, snaps: pd.DataFrame) -> Dict[str, Dict[str, Optional[int]]]:
        out: Dict[str, Dict[str, Optional[int]]] = {}
        for eid, g in snaps.groupby("entity_id"):
            g = g.sort_values("as_of")
            red_ews = g.loc[g["ews_band"] == "Red", "as_of"]
            red_base = g.loc[g["baseline_band"] == "Red", "as_of"]
            out[eid] = {
                "ews": int(red_ews.min()) if len(red_ews) else None,
                "baseline": int(red_base.min()) if len(red_base) else None,
            }
        return out

    def first_alert(self, entity_id: str, model: str = "ews") -> Optional[int]:
        """First month (panel index, <=0) this entity's band went Red under
        `model` ('ews' | 'baseline'); None if it never did."""
        return self._first_alerts.get(entity_id, {}).get(model)

    # --------------------------------------------------------- reason codes
    def _reason_codes(self, feats: Dict[str, float], top_k: int = 3) -> List[dict]:
        """Sign-aware risk drivers from standardized feature deviations. A feature
        moving in its *unhealthy* direction (z opposite the health direction) is a
        risk; magnitude = |z|. Returns the top-k risks (negatives)."""
        scored = []
        for f in self.feature_cols:
            mu = float(self._feat_mean[f]); sd = float(self._feat_std[f])
            z = (feats.get(f, mu) - mu) / sd
            risk = -FEATURE_DIRECTIONS[f] * z          # >0 => unhealthy movement
            if risk <= 0.25:
                continue
            scored.append({
                "feature": f, "label": FEATURE_LABELS[f],
                "direction": -1, "contribution": round(float(risk), 2),
            })
        scored.sort(key=lambda s: -s["contribution"])
        return scored[:top_k]

    # ------------------------------------------------------------ portfolio
    def _build_portfolio(self, snaps: pd.DataFrame) -> Dict[str, object]:
        latest = int(snaps["as_of"].max())
        lb = self._loan_book.set_index("entity_id")
        live = snaps[snaps["as_of"] == latest].copy()

        rows: List[dict] = []
        for r in live.itertuples():
            eid = r.entity_id
            if eid not in lb.index:
                continue
            loan = lb.loc[eid]
            feats = {f: getattr(r, f) for f in self.feature_cols}
            rows.append({
                "entity_id": eid,
                "product": loan["product"],
                "status": loan["status"],
                "exposure": float(loan["sanctioned_limit"]),
                "dpd_current": float(r.dpd_current),
                "pd_12m": round(float(r.ews_pd), 4),
                "band": r.ews_band,
                "baseline_pd_3m": round(float(r.baseline_pd), 4),
                "baseline_band": r.baseline_band,
                "reasons": self._reason_codes(feats),
            })
        df = pd.DataFrame(rows)
        # Exclude already-closed loans from the "live book" counts.
        book = df[df["status"] != "closed"]
        bands = book["band"].value_counts().to_dict()
        return {
            "as_of_month": latest,
            "rows": rows,
            "n_loans": int(len(book)),
            "exposure_total": float(book["exposure"].sum()) if len(book) else 0.0,
            "band_counts": {b: int(bands.get(b, 0)) for b in ("Red", "Amber", "Green")},
            "red_share": float((book["band"] == "Red").mean()) if len(book) else 0.0,
            "amber_share": float((book["band"] == "Amber").mean()) if len(book) else 0.0,
        }

    # --------------------------------------------------------------- public API
    def portfolio_snapshot(self) -> Dict[str, object]:
        """Latest-month scores/bands/reasons for every live loan + book aggregates,
        plus the stored eval headline (median lead-time, capture@decile). Pure
        data for WP-4A to render."""
        out = dict(self._portfolio)
        out["eval"] = self._eval
        return out

    def entity_timeline(self, entity_id: str) -> Dict[str, object]:
        """Monthly series for one borrower: alt-data levels, DPD, both models' PD
        trajectory, first-alert markers and default_month. Pure data, no copy."""
        t = _load_tables()
        alt = t["altdata_monthly"]
        rep = t["repayment_history"]
        a = alt[alt["entity_id"] == entity_id].sort_values("month")
        r = rep[rep["entity_id"] == entity_id].sort_values("month")
        snap = (self._snaps[self._snaps["entity_id"] == entity_id]
                .sort_values("as_of")) if self._snaps is not None else pd.DataFrame()
        fa = self._first_alerts.get(entity_id, {"ews": None, "baseline": None})
        return {
            "entity_id": entity_id,
            "months": a["month"].tolist(),
            "gst_turnover_declared": a["gst_turnover_declared"].tolist(),
            "bank_inflows": a["bank_inflows"].tolist(),
            "upi_txn_count": a["upi_txn_count"].tolist(),
            "epfo_employee_count": a["epfo_employee_count"].tolist(),
            "energy_units": a["energy_units"].tolist(),
            "dpd": r.set_index("month")["dpd"].reindex(a["month"]).tolist(),
            "pd_months": snap["as_of"].tolist() if len(snap) else [],
            "ews_pd": snap["ews_pd"].tolist() if len(snap) else [],
            "baseline_pd": snap["baseline_pd"].tolist() if len(snap) else [],
            "ews_first_alert": fa.get("ews"),
            "baseline_first_alert": fa.get("baseline"),
            "default_month": self._default_month.get(entity_id),
            "is_defaulter": self._is_defaulter.get(entity_id, 0),
        }

    def eval_summary(self) -> Dict[str, object]:
        return dict(self._eval)

    # ------------------------------------------------------------- persistence
    def __getstate__(self):
        state = self.__dict__.copy()
        state["_state_version"] = EWSEngine.STATE_VERSION
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)

    def save(self, path=None) -> "EWSEngine":
        path = path or EWS_PICKLE
        with open(path, "wb") as fh:
            pickle.dump(self, fh)
        return self


# --------------------------------------------------------------------------- #
# Prefit pickle (lives INSIDE the track — never touches app/ml/prefit.py).
# --------------------------------------------------------------------------- #
EWS_PICKLE = paths.DATA_DIR / "ews_engine.pkl"

_ENGINE: EWSEngine | None = None


def _load_prefit() -> EWSEngine | None:
    """Load the build-time prefit engine iff it isn't stale vs the loan book and
    matches the current STATE_VERSION (copy of the ScoringEngine pattern)."""
    src = paths.DATA_DIR / "loan_book.csv"
    try:
        if not (EWS_PICKLE.exists() and src.exists()):
            return None
        if EWS_PICKLE.stat().st_mtime < src.stat().st_mtime:
            return None
        with open(EWS_PICKLE, "rb") as fh:
            obj = pickle.load(fh)
        if getattr(obj, "_state_version", None) != EWSEngine.STATE_VERSION:
            return None
        return obj
    except Exception:
        return None


def get_engine() -> EWSEngine:
    """Cached singleton: prefit pickle when fresh, else fit (WP-4A cache wrapper
    will wrap this behind st.cache_resource)."""
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = _load_prefit() or EWSEngine().fit()
    return _ENGINE


def prefit() -> EWSEngine:
    """Warm the EWS pickle (skip-if-fresh). Exposed for central warm-up wiring."""
    fresh = _load_prefit()
    if fresh is not None:
        return fresh
    return EWSEngine().fit().save()


# Alias matching the WP wording ("prefit()/warm()").
warm = prefit
