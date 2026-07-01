"""UPI features — digital-payment footprint (rides on AA bank narration)."""
from __future__ import annotations

import pandas as pd

from .base import feature_source


@feature_source("upi")
def upi_features(df: pd.DataFrame, master_row: dict) -> dict:
    if df is None or df.empty:
        return {"upi_present": 0.0, "upi_total_receipts": 0.0, "upi_p2m_share": 0.0,
                "upi_counterparty_breadth": 0.0, "upi_refund_rate": 0.0}
    p2m = df["p2m_count"].sum()
    p2p = df["p2p_count"].sum()
    total_txn = max(p2m + p2p, 1)
    return {
        "upi_present": 1.0,
        "upi_total_receipts": float(df["total_receipts"].sum()),
        "upi_p2m_share": float(p2m / total_txn),
        "upi_counterparty_breadth": float(df["unique_counterparties"].mean()),
        "upi_refund_rate": float(df["refund_count"].sum() / total_txn),
    }
