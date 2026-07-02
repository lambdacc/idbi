"""Population Stability Index — distribution drift between two samples.

PSI < 0.1 = stable, 0.1-0.25 = moderate shift, > 0.25 = significant shift.
Used to check train-vs-holdout feature stability (solution-design.md §9).
"""
from __future__ import annotations

from typing import Dict

import numpy as np
import pandas as pd


def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    if np.all(expected == expected[0]):
        return 0.0  # constant feature — no drift definable
    # Quantile bins from the expected (reference) distribution.
    quantiles = np.unique(np.quantile(expected, np.linspace(0, 1, bins + 1)))
    if len(quantiles) < 2:
        return 0.0
    e_counts, _ = np.histogram(expected, bins=quantiles)
    a_counts, _ = np.histogram(actual, bins=quantiles)
    e_pct = np.clip(e_counts / max(e_counts.sum(), 1), 1e-6, None)
    a_pct = np.clip(a_counts / max(a_counts.sum(), 1), 1e-6, None)
    return float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))


def psi_report(train: pd.DataFrame, test: pd.DataFrame, features: list) -> Dict[str, float]:
    out = {}
    for f in features:
        if f in train.columns and f in test.columns:
            out[f] = round(psi(train[f].to_numpy(), test[f].to_numpy()), 4)
    return out
