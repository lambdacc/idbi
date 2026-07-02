"""EPFO features — workforce scale & stability (going-concern proxy).

NOT live on AA — mocked/roadmap per data-and-intel-sourcing-guide.md.
Arrears are the strongest distress marker (statutory first-charge).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import feature_source
from .gst_features import _trend


@feature_source("epfo")
def epfo_features(df: pd.DataFrame, master_row: dict) -> dict:
    if df is None or df.empty:
        return {"epfo_present": 0.0, "epfo_headcount_latest": 0.0,
                "epfo_workforce_stability": 0.0, "epfo_arrears_rate": 0.0,
                "epfo_total_wage_bill": 0.0}
    hc = df["headcount"].to_numpy()
    trend = _trend(hc)  # positive = growing workforce
    stability = float(np.clip(1.0 - abs(hc.std() / max(hc.mean(), 1.0)) + max(trend, 0), 0, 1))
    return {
        "epfo_present": 1.0,
        "epfo_headcount_latest": float(hc[-1]),
        "epfo_workforce_stability": stability,
        "epfo_arrears_rate": float(df["arrears_flag"].mean()),
        "epfo_total_wage_bill": float(df["wage_bill"].sum()),
    }
