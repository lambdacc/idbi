"""GST features — revenue quality & GST discipline + CAG DORF-II ratio signals.

CAG-mined ratios (intel-cag-gst-feature-analysis.md §3A): ITC/tax-paid,
IGST/(CGST+SGST), exempt/taxable, credit-notes/turnover — all GSTN-stable and
computable from the borrower's own returns (no consent needed).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import feature_source


def _trend(series: np.ndarray) -> float:
    """Fractional change of last-third mean vs first-third mean."""
    n = len(series)
    if n < 3:
        return 0.0
    k = max(1, n // 3)
    first, last = series[:k].mean(), series[-k:].mean()
    if first <= 0:
        return 0.0
    return float((last - first) / first)


@feature_source("gst")
def gst_features(df: pd.DataFrame, master_row: dict) -> dict:
    if df is None or df.empty:
        # Legally-exempt / unregistered — a genuine thin-file case, not a defect.
        return {"gst_present": 0.0, "gst_turnover_level": 0.0, "gst_turnover_trend": 0.0,
                "gst_filing_regularity": 0.0, "gst_customer_concentration": 0.0,
                "gst_credit_note_ratio": 0.0, "gst_itc_to_tax_paid": 0.0,
                "gst_igst_ratio": 0.0, "gst_exempt_ratio": 0.0, "gst_total_turnover": 0.0}
    turnover = df["turnover"].to_numpy()
    tax = df["tax_liability"].sum()
    return {
        "gst_present": 1.0,
        "gst_turnover_level": float(turnover.mean()),
        "gst_total_turnover": float(turnover.sum()),           # annualised, raw for composites
        "gst_turnover_trend": _trend(turnover),
        "gst_filing_regularity": float((df["filing_days_late"] == 0).mean()),
        "gst_customer_concentration": float(1.0 / max(df["num_customers"].mean(), 1.0)),
        "gst_credit_note_ratio": float(df["credit_notes"].sum() / max(turnover.sum(), 1.0)),
        "gst_itc_to_tax_paid": float(df["itc_availed"].sum() / max(tax, 1.0)),
        "gst_igst_ratio": float(df["igst"].sum() / max((df["cgst"].sum() + df["sgst"].sum()), 1.0)),
        "gst_exempt_ratio": float(df["exempted_turnover"].sum() / max(turnover.sum(), 1.0)),
    }
