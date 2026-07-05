"""Track-04 early-warning snapshot features (WP-4M spec §Build.1).

Per (entity, as-of-month) behavioural features from the repayment + alt-data
panel. The whole point of this track is *anti-leakage discipline*, so the causal
contract is enforced structurally, not by convention:

  * `build_snapshots(...)` computes a snapshot at month `m` using ONLY panel rows
    with `month <= m` — a poisoned future row is filtered out before any feature
    touches it (WP-4M §Leakage: "snapshot at m uses only <= m data").
  * Every windowed feature draws its slice through `_window(...)`, which RAISES
    `LeakageError` if a caller asks for a window extending past the snapshot month
    (WP-4M §Leakage: "must raise if asked for a feature window past the snapshot").
  * No label-derived field is ever read here — `default_month`/`ramp_start`/
    `lead_alt`/`repay_lag` live only in the labels file and are joined downstream
    in `model.py`, never in this module (grep-proof: "default" appears in no
    feature column). Label attachment is a *separate* step by construction.

Monotone-direction table (health direction: +1 => higher is healthier, so the
GBM's P(default) constraint is the negation; consumed by `MonotonicGBM`):

    feature                     dir   rationale
    ---------------------------------------------------------------------
    dpd_current                  -1   days-past-due now: higher = worse
    dpd_max_3m                   -1   worst recent delinquency
    bounce_cnt_6m                -1   more EMI bounces = worse
    utilization_now              -1   maxed-out limit = stress
    utilization_slope_6m         -1   utilisation climbing = stress
    months_on_book               +1   seasoning: more history = steadier
    gst_turnover_slope_6m        +1   declared turnover rising = healthier
    gst_missed_filings_6m        -1   more late/missed GST filings = worse
    inflow_slope_6m              +1   bank inflows rising = healthier
    inflow_vs_gst_gap            -1   inflows lagging declared GST = worse
    upi_count_slope_6m           +1   digital activity rising = healthier
    epfo_headcount_delta_6m      +1   payroll growing = healthier
    energy_slope_6m              +1   consumption rising = healthier
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------- #
# Monotone direction table (see module docstring).
# --------------------------------------------------------------------------- #
FEATURE_DIRECTIONS: Dict[str, int] = {
    "dpd_current": -1,
    "dpd_max_3m": -1,
    "bounce_cnt_6m": -1,
    "utilization_now": -1,
    "utilization_slope_6m": -1,
    "months_on_book": +1,
    "gst_turnover_slope_6m": +1,
    "gst_missed_filings_6m": -1,
    "inflow_slope_6m": +1,
    "inflow_vs_gst_gap": -1,
    "upi_count_slope_6m": +1,
    "epfo_headcount_delta_6m": +1,
    "energy_slope_6m": +1,
}

# Feature groups the two models consume.
REPAYMENT_FEATURES: List[str] = [
    "dpd_current", "dpd_max_3m", "bounce_cnt_6m",
    "utilization_now", "utilization_slope_6m", "months_on_book",
]
ALTDATA_FEATURES: List[str] = [
    "gst_turnover_slope_6m", "gst_missed_filings_6m", "inflow_slope_6m",
    "inflow_vs_gst_gap", "upi_count_slope_6m", "epfo_headcount_delta_6m",
    "energy_slope_6m",
]
FEATURE_COLS: List[str] = REPAYMENT_FEATURES + ALTDATA_FEATURES
# The baseline "internal-model stand-in" sees repayment behaviour only.
BASELINE_FEATURES: List[str] = list(REPAYMENT_FEATURES)

# Human labels for reason codes (sign-aware phrasing built in model.py).
FEATURE_LABELS: Dict[str, str] = {
    "dpd_current": "days past due",
    "dpd_max_3m": "recent worst delinquency",
    "bounce_cnt_6m": "EMI bounces (6m)",
    "utilization_now": "limit utilisation",
    "utilization_slope_6m": "rising limit utilisation",
    "months_on_book": "account seasoning",
    "gst_turnover_slope_6m": "GST turnover trend",
    "gst_missed_filings_6m": "missed GST filings (6m)",
    "inflow_slope_6m": "bank-inflow trend",
    "inflow_vs_gst_gap": "inflows lagging declared GST",
    "upi_count_slope_6m": "UPI activity trend",
    "epfo_headcount_delta_6m": "payroll headcount change (6m)",
    "energy_slope_6m": "energy-use trend",
}

# Column subsets each source contributes (used to filter the poisoned-row test).
_WINDOW = 6            # months of look-back for slopes / counts
_EPS = 1e-9


class LeakageError(ValueError):
    """Raised when a feature window would peek past its snapshot month."""


# --------------------------------------------------------------------------- #
# Causal window helper — the structural anti-leakage guard.
# --------------------------------------------------------------------------- #
def _window(entity_df: pd.DataFrame, as_of: int, months_back: int,
            future_offset: int = 0) -> pd.DataFrame:
    """Return one entity's rows in [as_of-months_back+1 .. as_of].

    `future_offset > 0` means the caller is asking for data *ahead* of the
    snapshot month — that is leakage by definition, so we refuse rather than
    silently serve the future. Every windowed feature routes through here, which
    is what makes "future-window raises" a structural guarantee, not a lint rule.
    """
    if future_offset > 0:
        raise LeakageError(
            f"feature window peeks {future_offset} month(s) past snapshot {as_of}")
    lo = as_of - months_back + 1
    w = entity_df[(entity_df["month"] >= lo) & (entity_df["month"] <= as_of)]
    return w.sort_values("month")


def _slope(months: np.ndarray, values: np.ndarray) -> float:
    """OLS slope of `values` over `months` (per-month change). 0 when degenerate."""
    m = np.asarray(months, dtype=float)
    v = np.asarray(values, dtype=float)
    ok = ~np.isnan(v)
    if ok.sum() < 2 or np.ptp(m[ok]) == 0:
        return 0.0
    return float(np.polyfit(m[ok], v[ok], 1)[0])


# --------------------------------------------------------------------------- #
# Per-snapshot feature computation.
# --------------------------------------------------------------------------- #
def _snapshot_features(rep_e: pd.DataFrame, alt_e: pd.DataFrame,
                       sanction_month: int, as_of: int) -> Dict[str, float]:
    """Compute the feature vector for one (entity, as_of) using causal windows."""
    rep6 = _window(rep_e, as_of, _WINDOW)
    rep3 = _window(rep_e, as_of, 3)
    alt6 = _window(alt_e, as_of, _WINDOW)

    # --- repayment channel (lagging indicator) --------------------------------
    dpd_current = float(rep6["dpd"].iloc[-1]) if len(rep6) else 0.0
    dpd_max_3m = float(rep3["dpd"].max()) if len(rep3) else 0.0
    bounce_cnt_6m = float(rep6["bounce_flag"].sum()) if len(rep6) else 0.0
    util = rep6["utilization_pct"]
    util_now = float(util.dropna().iloc[-1]) if util.notna().any() else 0.0
    util_slope = _slope(rep6["month"].to_numpy(), util.to_numpy()) if util.notna().any() else 0.0
    months_on_book = float(max(0, as_of - sanction_month))

    # --- alt-data channel (leading indicator) ---------------------------------
    gst_slope = _slope(alt6["month"].to_numpy(), alt6["gst_turnover_declared"].to_numpy())
    gst_missed = float((1 - alt6["gst_filed_on_time"]).sum()) if len(alt6) else 0.0
    inflow_slope = _slope(alt6["month"].to_numpy(), alt6["bank_inflows"].to_numpy())
    upi_slope = _slope(alt6["month"].to_numpy(), alt6["upi_txn_count"].to_numpy())
    energy_slope = _slope(alt6["month"].to_numpy(), alt6["energy_units"].to_numpy())
    if len(alt6):
        hc = alt6["epfo_employee_count"].to_numpy(dtype=float)
        epfo_delta = float(hc[-1] - hc[0])
    else:
        epfo_delta = 0.0
    # Authenticity idea: declared GST staying high while inflows sag => gap up.
    if len(alt6):
        gst_recent = float(alt6["gst_turnover_declared"].tail(3).mean())
        inflow_recent = float(alt6["bank_inflows"].tail(3).mean())
        gap = 1.0 - inflow_recent / (gst_recent + _EPS)
        inflow_vs_gst_gap = float(np.clip(gap, -2.0, 2.0))
    else:
        inflow_vs_gst_gap = 0.0

    return {
        "dpd_current": dpd_current,
        "dpd_max_3m": dpd_max_3m,
        "bounce_cnt_6m": bounce_cnt_6m,
        "utilization_now": util_now,
        "utilization_slope_6m": util_slope,
        "months_on_book": months_on_book,
        "gst_turnover_slope_6m": gst_slope,
        "gst_missed_filings_6m": gst_missed,
        "inflow_slope_6m": inflow_slope,
        "inflow_vs_gst_gap": inflow_vs_gst_gap,
        "upi_count_slope_6m": upi_slope,
        "epfo_headcount_delta_6m": epfo_delta,
        "energy_slope_6m": energy_slope,
    }


def build_snapshots(loan_book: pd.DataFrame, repayments: pd.DataFrame,
                    altdata: pd.DataFrame,
                    as_of_months: Optional[List[int]] = None,
                    min_history: int = _WINDOW) -> pd.DataFrame:
    """Per (entity, as_of) feature matrix using ONLY months <= as_of.

    `as_of_months` defaults to every month with at least `min_history` prior
    observations (so slopes are well-defined). Poisoned future rows in the input
    are never seen: each snapshot slices `month <= as_of` before any feature runs.
    Label attachment is deliberately NOT done here (see module docstring).
    """
    all_months = sorted(repayments["month"].unique().tolist())
    lo = all_months[0]
    if as_of_months is None:
        as_of_months = [m for m in all_months if m >= lo + min_history - 1]

    sanction = loan_book.set_index("entity_id")["sanction_month"].to_dict()
    rep_by = {e: g for e, g in repayments.groupby("entity_id")}
    alt_by = {e: g for e, g in altdata.groupby("entity_id")}

    rows: List[dict] = []
    for eid in loan_book["entity_id"]:
        rep_e = rep_by.get(eid)
        alt_e = alt_by.get(eid)
        if rep_e is None or alt_e is None:
            continue
        s_month = int(sanction.get(eid, lo))
        for as_of in as_of_months:
            feats = _snapshot_features(rep_e, alt_e, s_month, as_of)
            feats["entity_id"] = eid
            feats["as_of"] = as_of
            rows.append(feats)

    cols = ["entity_id", "as_of"] + FEATURE_COLS
    return pd.DataFrame(rows, columns=cols)
