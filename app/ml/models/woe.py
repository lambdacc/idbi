"""Weight-of-Evidence binning + Information Value (World Bank scorecard practice).

WOE_bin = ln(%non-events / %events); IV = Σ (%non-events - %events) · WOE.
Used by scorecard.py (interpretable transform) and confidence_score.py (IV as the
per-source information weight). Quantile bins with a small epsilon guard.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

_EPS = 1e-6


class WOEBinner:
    def __init__(self, n_bins: int = 5):
        self.n_bins = n_bins
        self.edges_: Dict[str, np.ndarray] = {}
        self.woe_: Dict[str, List[float]] = {}
        self.iv_: Dict[str, float] = {}

    def _bin_edges(self, x: np.ndarray) -> np.ndarray:
        qs = np.linspace(0, 1, self.n_bins + 1)
        edges = np.unique(np.quantile(x, qs))
        if len(edges) < 2:                      # constant column
            edges = np.array([x[0] - 1, x[0] + 1])
        edges[0], edges[-1] = -np.inf, np.inf
        return edges

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "WOEBinner":
        y = np.asarray(y)
        n_good, n_bad = max((y == 0).sum(), 1), max((y == 1).sum(), 1)
        for col in X.columns:
            x = X[col].to_numpy(dtype=float)
            edges = self._bin_edges(x)
            idx = np.clip(np.digitize(x, edges[1:-1], right=False), 0, len(edges) - 2)
            woes, iv = [], 0.0
            for b in range(len(edges) - 1):
                mask = idx == b
                good = (y[mask] == 0).sum()
                bad = (y[mask] == 1).sum()
                dist_good = good / n_good + _EPS
                dist_bad = bad / n_bad + _EPS
                woe = float(np.log(dist_good / dist_bad))
                woes.append(woe)
                iv += (dist_good - dist_bad) * woe
            self.edges_[col] = edges
            self.woe_[col] = woes
            self.iv_[col] = float(iv)
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        out = {}
        for col in X.columns:
            if col not in self.edges_:
                out[col] = np.zeros(len(X))
                continue
            edges = self.edges_[col]
            x = X[col].to_numpy(dtype=float)
            idx = np.clip(np.digitize(x, edges[1:-1], right=False), 0, len(edges) - 2)
            out[col] = np.array([self.woe_[col][i] for i in idx])
        return pd.DataFrame(out, index=X.index)

    def fit_transform(self, X: pd.DataFrame, y: np.ndarray) -> pd.DataFrame:
        return self.fit(X, y).transform(X)
