"""Electricity features — energy-intensity / production-capacity composite driver."""
from __future__ import annotations

import pandas as pd

from .base import feature_source


@feature_source("electricity")
def electricity_features(df: pd.DataFrame, master_row: dict) -> dict:
    if df is None or df.empty:
        return {"electricity_present": 0.0, "electricity_total_kwh": 0.0,
                "electricity_sanctioned_load": 0.0, "electricity_bill_ontime_rate": 0.0}
    return {
        "electricity_present": 1.0,
        "electricity_total_kwh": float(df["consumption_kwh"].sum()),   # raw for Energy-Intensity
        "electricity_sanctioned_load": float(df["sanctioned_load_kw"].max()),
        "electricity_bill_ontime_rate": float(df["bill_paid_on_time"].mean()),
    }
