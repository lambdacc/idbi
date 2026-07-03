"""Post-hoc probability calibration — makes the displayed PD mean what it says.

A ranking model can separate defaulters from non-defaulters (good AUC) yet still
be systematically over/under-confident, so a raw predict_proba of 0.05 need not
mean "5 in 100 default". We fit a monotone calibration map on OUT-OF-FOLD
predictions (never in-sample — that would look better than it is) and apply it to
the displayed PD. `point_contributions`/log-odds explanations are untouched: this
only reshapes the probability, not the model's driver attribution.

isotonic when there is enough data to support it, Platt (sigmoid) otherwise;
identity (no-op) when there are too few events to calibrate honestly.
"""
from __future__ import annotations

from typing import Callable, Optional

import numpy as np
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_predict

_EPS = 1e-6


def out_of_fold_pd(make_estimator: Callable, X, y, n_splits: int = 5,
                   seed: int = 42) -> Optional[np.ndarray]:
    """Cross-validated P(default) for every training row, so calibration is fit on
    predictions the model did NOT train on. Returns None when the cohort is too
    small / imbalanced to cross-validate honestly."""
    y = np.asarray(y)
    n_pos, n_neg = int((y == 1).sum()), int((y == 0).sum())
    folds = min(n_splits, n_pos, n_neg)
    if folds < 2:
        return None
    skf = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    try:
        proba = cross_val_predict(make_estimator(), X, y, cv=skf,
                                  method="predict_proba")
        return np.asarray(proba)[:, 1]
    except Exception:
        return None


class PostHocCalibrator:
    """Fits raw_pd -> calibrated_pd. `method='auto'` picks isotonic when both
    classes are well populated, else Platt sigmoid."""

    def __init__(self, method: str = "auto", min_isotonic: int = 50):
        self.method = method
        self.min_isotonic = min_isotonic
        self.kind_: str = "identity"
        self._iso: Optional[IsotonicRegression] = None
        self._platt: Optional[LogisticRegression] = None

    @property
    def fitted(self) -> bool:
        return self.kind_ != "identity"

    def fit(self, raw_pd: Optional[np.ndarray], y) -> "PostHocCalibrator":
        if raw_pd is None:
            self.kind_ = "identity"
            return self
        raw = np.clip(np.asarray(raw_pd, dtype=float), _EPS, 1 - _EPS)
        y = np.asarray(y)
        n_pos, n_neg = int((y == 1).sum()), int((y == 0).sum())
        method = self.method
        if method == "auto":
            method = "isotonic" if min(n_pos, n_neg) >= self.min_isotonic else "sigmoid"
        if method == "isotonic":
            self._iso = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
            self._iso.fit(raw, y)
            self.kind_ = "isotonic"
        else:  # Platt scaling: logistic on the raw-PD logit
            logit = np.log(raw / (1 - raw)).reshape(-1, 1)
            self._platt = LogisticRegression(max_iter=1000)
            self._platt.fit(logit, y)
            self.kind_ = "sigmoid"
        return self

    def transform(self, raw_pd: np.ndarray) -> np.ndarray:
        raw = np.clip(np.asarray(raw_pd, dtype=float), _EPS, 1 - _EPS)
        if self.kind_ == "isotonic":
            return np.clip(self._iso.predict(raw), _EPS, 1 - _EPS)
        if self.kind_ == "sigmoid":
            logit = np.log(raw / (1 - raw)).reshape(-1, 1)
            return np.clip(self._platt.predict_proba(logit)[:, 1], _EPS, 1 - _EPS)
        return raw  # identity
