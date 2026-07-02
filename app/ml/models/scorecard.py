"""WOE/IV logistic scorecard — the transparent PD backbone (solution-design.md §5).

Fits logistic regression on WOE-transformed features to predict default. Every
prediction decomposes into native additive point contributions (coef · WOE),
so the reason path needs no post-hoc approximation. Also emits an optional
300-900 bureau-style analogue (first to cut under pressure, per §7 cut-list).
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from .woe import WOEBinner

# Standard scorecard scaling: PDO points-to-double-the-odds.
_BASE_SCORE, _BASE_ODDS, _PDO = 600.0, 50.0, 20.0


class WOEScorecard:
    def __init__(self, n_bins: int = 5, iv_floor: float = 0.02):
        self.binner = WOEBinner(n_bins=n_bins)
        self.iv_floor = iv_floor
        self.features_: List[str] = []
        # No class_weight balancing here: we need CALIBRATED probabilities for the
        # displayed PD, not just ranking. (The eval harness uses its own balanced
        # baseline for discrimination.)
        self.model = LogisticRegression(max_iter=1000)
        self._factor = _PDO / np.log(2)
        self._offset = _BASE_SCORE - self._factor * np.log(_BASE_ODDS)

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "WOEScorecard":
        self.binner.fit(X, y)
        # Keep only features carrying signal (IV >= floor) — drops dead columns.
        self.features_ = [c for c in X.columns if self.binner.iv_.get(c, 0.0) >= self.iv_floor]
        if not self.features_:                       # fallback: keep top-10 by IV
            self.features_ = sorted(X.columns, key=lambda c: -self.binner.iv_.get(c, 0))[:10]
        Xw = self.binner.transform(X)[self.features_]
        self.model.fit(Xw, y)
        return self

    def _woe(self, X: pd.DataFrame) -> pd.DataFrame:
        return self.binner.transform(X)[self.features_]

    def predict_pd(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(self._woe(X))[:, 1]

    def credit_score_300_900(self, X: pd.DataFrame) -> np.ndarray:
        """Optional bureau-style analogue derived from PD odds."""
        pd_ = np.clip(self.predict_pd(X), 1e-6, 1 - 1e-6)
        odds = (1 - pd_) / pd_
        score = self._offset + self._factor * np.log(odds)
        return np.clip(score, 300, 900)

    def point_contributions(self, feats: Dict[str, float]) -> Dict[str, float]:
        """Per-feature contribution to log-odds of DEFAULT for one entity.

        Positive => pushes toward default (a risk); negative => protective.
        """
        X = pd.DataFrame([{f: feats.get(f, 0.0) for f in self.features_}])
        woe = self._woe(X).iloc[0]
        coefs = dict(zip(self.features_, self.model.coef_[0]))
        return {f: float(coefs[f] * woe[f]) for f in self.features_}

    def top_iv(self, k: int = 15) -> Dict[str, float]:
        return dict(sorted(self.binner.iv_.items(), key=lambda kv: -kv[1])[:k])
