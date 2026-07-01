"""E-way bill features — real goods-movement proxy feeding Turnover-Authenticity."""
from __future__ import annotations

import pandas as pd

from .base import feature_source


@feature_source("ewaybill")
def ewaybill_features(df: pd.DataFrame, master_row: dict) -> dict:
    if df is None or df.empty:
        return {"ewb_present": 0.0, "ewb_total_value": 0.0, "ewb_count_total": 0.0}
    return {
        "ewb_present": 1.0,
        "ewb_total_value": float(df["ewb_value"].sum()),   # raw for Turnover-Authenticity
        "ewb_count_total": float(df["ewb_count"].sum()),
    }
