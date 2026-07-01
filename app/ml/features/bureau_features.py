"""Credit-bureau features — existing obligations & delinquency.

Structurally thin/blank for the NTC/NTB target segment (that is the point) —
valuable as a cross-check, not a primary signal.
"""
from __future__ import annotations

import pandas as pd

from .base import feature_source


@feature_source("bureau")
def bureau_features(df: pd.DataFrame, master_row: dict) -> dict:
    if df is None or df.empty:
        return {"bureau_has_record": 0.0, "bureau_delinquency": 0.0,
                "bureau_exposure": 0.0, "bureau_enquiries": 0.0, "bureau_rank": 0.0}
    r = df.iloc[0]
    return {
        "bureau_has_record": float(r["has_bureau_record"]),
        "bureau_delinquency": float(r["max_dpd_12m"]),
        "bureau_exposure": float(r["total_exposure"]),
        "bureau_enquiries": float(r["num_enquiries_6m"]),
        "bureau_rank": float(r["msme_rank"]),
    }
