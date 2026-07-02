"""Bank / Account-Aggregator features — cash-flow health & obligations."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import feature_source
from .gst_features import _trend


@feature_source("bank")
def bank_features(df: pd.DataFrame, master_row: dict) -> dict:
    if df is None or df.empty:
        return {"bank_present": 0.0, "bank_avg_balance": 0.0, "bank_balance_volatility": 0.0,
                "bank_low_balance_freq": 0.0, "bank_net_flow_trend": 0.0,
                "bank_bounce_frequency": 0.0, "bank_total_inflow": 0.0,
                "dscr": 0.0, "foir": 0.0, "banking_relationship_months": 0.0}
    avg_bal = df["avg_balance"].to_numpy()
    inflow = df["total_inflow"].to_numpy()
    outflow = df["total_outflow"].to_numpy()
    net_flow = inflow - outflow
    emi = df["emi_debits"].sum()
    total_inflow = float(inflow.sum())
    # low-balance months: min balance below 5% of that month's average, or negative
    low_bal = ((df["min_balance"] <= 0) | (df["min_balance"] < 0.05 * df["avg_balance"])).mean()
    net_operating = max(total_inflow - outflow.sum() + emi, 0.0)  # add back debt service
    return {
        "bank_present": 1.0,
        "bank_avg_balance": float(avg_bal.mean()),
        "bank_balance_volatility": float(avg_bal.std() / max(avg_bal.mean(), 1.0)),
        "bank_low_balance_freq": float(low_bal),
        "bank_net_flow_trend": _trend(net_flow),
        "bank_bounce_frequency": float(df["bounce_count"].sum() / max(len(df), 1)),
        "bank_total_inflow": total_inflow,                          # raw for composites
        "dscr": float(net_operating / max(emi, 1.0)) if emi > 0 else 3.0,
        "foir": float(emi / max(total_inflow, 1.0)),
        "banking_relationship_months": float(len(df)),
    }
