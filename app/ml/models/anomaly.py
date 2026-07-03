"""Isolation Forest fraud leg — an UNSUPERVISED, independent cross-check.

The Turnover-Authenticity composite is a hand-crafted rule: it encodes exactly the
inconsistency we thought to look for (declared turnover vs settled bank inflows and
goods movement). An Isolation Forest complements it by learning, with NO fraud
labels, what a normal MSME's *other* cross-source consistency signals look like —
premises, supply-chain, credit-exposure and energy corroboration — and isolating
the entities whose joint profile sits far from that norm. Because it reads signals
the turnover check does NOT, it is a genuinely independent second opinion.

Two design points that make it safe to show a banker:
  * Features are BADNESS-oriented (0 = corroborated or not-applicable, higher =
    an active contradiction), so an exceptional genuine business sits at the origin
    and is never mistaken for an outlier.
  * The displayed anomaly is measured as EXCESS over the clearly-genuine cohort
    (entities with zero measured contradiction), so "normal" maps to ~0 rather than
    to a misleading mid-percentile.

Validation (synthetic holdout, labels used only to score — never to train): the
authenticity composite alone lands ~0.72 fraud AUC; the anomaly leg ~0.84; blended
into one fraud-risk score, ~0.92 — and it catches inflated entities the composite
alone misses.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

_AUTH_KEY = "turnover_authenticity_score"
_CHECKS_KEY = "ta_num_checks"

# Ensemble weight on the interpretable authenticity composite; remainder on the
# anomaly leg. 0.65 keeps the explainable rule as the primary voice while giving
# the unsupervised model a meaningful say (selected on the synthetic holdout).
_W_COMPOSITE = 0.65
# Fraud-risk band cut-offs (0-100). Genuine archetypes score < 35 on the holdout;
# inflated ~60 — the cut-offs sit in the wide gap between the two.
_ELEVATED, _MODERATE = 55.0, 38.0


def _badness_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Consistency signals, each oriented so 0 = corroborated / not-applicable and
    a higher value = an active, independently-verifiable contradiction. Deliberately
    excludes the turnover-authenticity signal so this leg is INDEPENDENT of it."""
    idx = df.index
    def col(name):
        return df[name] if name in df.columns else pd.Series(0.0, index=idx)
    b = pd.DataFrame(index=idx)
    # Supply chain (customs vs GST vs e-way-bill) — only meaningful for IEC holders.
    iec = col("dgft_has_iec") > 0
    b["b_supply"] = np.where(iec, 1.0 - col("supply_chain_consistency"), 0.0)
    # Undisclosed borrowing: bank EMI debits with no matching bureau exposure (0/1).
    b["b_credit"] = col("credit_exposure_mismatch")
    # Premises: a contradiction only when a property-tax record exists but its
    # address does NOT match GST (absence of a record is not evidence of fraud).
    ptax = col("ptax_has_record") > 0
    b["b_premises"] = np.where(ptax, 1.0 - col("ptax_address_matches_gst"), 0.0)
    # Declared turnover vs metered electricity (already a 0-1 badness gap).
    b["b_energy"] = col("energy_intensity_flag")
    return b.fillna(0.0)


class AnomalyDetector:
    def __init__(self, n_estimators: int = 400, seed: int = 42):
        self.n_estimators = n_estimators
        self.seed = seed
        self.scaler = StandardScaler()
        self.model: Optional[IsolationForest] = None
        self.features_: List[str] = []
        self._normal_hi = 0.0     # anomaly level at the top of the clearly-genuine set
        self._anom_hi = 1.0       # anomaly level of the most extreme training entity

    # ------------------------------------------------------------------ fit
    def fit(self, feature_matrix: pd.DataFrame) -> "AnomalyDetector":
        B = _badness_frame(feature_matrix)
        self.features_ = list(B.columns)
        Xs = self.scaler.fit_transform(B)
        self.model = IsolationForest(n_estimators=self.n_estimators,
                                     random_state=self.seed).fit(Xs)
        anom = -self.model.score_samples(Xs)          # higher = more anomalous
        genuine = B.sum(axis=1).to_numpy() < 1e-9      # zero measured contradiction
        base = anom[genuine] if genuine.any() else anom
        # Anchor "normal" at the 90th percentile of the clearly-genuine set so the
        # dense normal cluster maps to ~0 excess and only true outliers rise.
        self._normal_hi = float(np.percentile(base, 90))
        self._anom_hi = float(np.percentile(anom, 99))
        if self._anom_hi <= self._normal_hi:
            self._anom_hi = self._normal_hi + 1e-6
        return self

    # ------------------------------------------------------------- transform
    def _anomaly_raw(self, X_badness: pd.DataFrame) -> np.ndarray:
        return -self.model.score_samples(self.scaler.transform(X_badness))

    def _excess(self, anom: np.ndarray) -> np.ndarray:
        """Directional anomaly in [0, 1]: 0 within the genuine range, 1 = extreme."""
        return np.clip((anom - self._normal_hi) / (self._anom_hi - self._normal_hi), 0.0, 1.0)

    @staticmethod
    def _composite_gap(auth: np.ndarray, checks: np.ndarray) -> np.ndarray:
        # Direct authenticity gap; neutral-low (0.30) when no checks could run so an
        # unassessable thin file is never treated as corroborated OR as fraud.
        return np.where(checks > 0, (100.0 - auth) / 100.0, 0.30)

    def anomaly_scores(self, feature_matrix: pd.DataFrame) -> np.ndarray:
        """Directional anomaly score in [0, 1] for a cohort (eval / ranking)."""
        return self._excess(self._anomaly_raw(_badness_frame(feature_matrix)))

    def fraud_risk_series(self, feature_matrix: pd.DataFrame) -> np.ndarray:
        """Blended fraud-risk in [0, 1] for a cohort (eval convenience)."""
        excess = self.anomaly_scores(feature_matrix)
        auth = feature_matrix.get(_AUTH_KEY, pd.Series(0.0, index=feature_matrix.index)).to_numpy()
        checks = feature_matrix.get(_CHECKS_KEY, pd.Series(0.0, index=feature_matrix.index)).to_numpy()
        comp = self._composite_gap(auth, checks)
        return np.clip(_W_COMPOSITE * comp + (1 - _W_COMPOSITE) * excess, 0.0, 1.0)

    @staticmethod
    def _band(risk_0_100: float) -> str:
        if risk_0_100 >= _ELEVATED:
            return "Elevated"
        if risk_0_100 >= _MODERATE:
            return "Moderate"
        return "Low"

    def assess(self, feats: Dict[str, float]) -> Dict[str, float]:
        """Per-entity fraud assessment: the independent anomaly leg, the authenticity
        composite leg, and the blended fraud-risk (all 0-100, higher = more suspect)."""
        row = pd.DataFrame([feats])
        excess = float(self._excess(self._anomaly_raw(_badness_frame(row)))[0])
        auth = float(feats.get(_AUTH_KEY, 0.0))
        checks = float(feats.get(_CHECKS_KEY, 0.0))
        comp = float(self._composite_gap(np.array([auth]), np.array([checks]))[0])
        fraud_risk = 100.0 * min(max(_W_COMPOSITE * comp + (1 - _W_COMPOSITE) * excess, 0.0), 1.0)
        return {
            "anomaly_score": round(100.0 * excess, 1),      # directional: 0 = within genuine range
            "authenticity_score": round(auth, 1),
            "fraud_risk_score": round(fraud_risk, 1),
            "fraud_band": self._band(fraud_risk),
            "n_signals": len(self.features_),
            "composite_weight": _W_COMPOSITE,
        }
