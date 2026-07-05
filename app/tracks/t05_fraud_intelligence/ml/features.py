"""Per-account behavioural feature engineering for SentinelPulse (WP-5M).

Reads ONLY the engine inputs (``accounts.csv`` + ``transactions.csv``) and folds
90 days of one account's ledger into a fixed vector of behavioural signals. The
labels file is never touched here — this module runs at score time.

Design mirrors ``app/data_gen/profiles.py``'s philosophy in reverse: the data
generator draws hidden latents and emits observable rows; here we recover
observable, model-ready signals (velocity, pass-through, fan-in/out, structuring,
device sharing, KYC throughput) that the typology detectors and the anomaly leg
consume. Every signal is oriented so a benign account sits low.

Grounding: the behaviours mirror RBIH MuleHunter.AI's documented mule patterns
(fan-in/out consolidation, rapid pass-through, dormancy burst, new-account
velocity, KYC-throughput mismatch, threshold structuring, odd-hours, shared
device). No user-facing copy lives here (ml computes; backend narrates in WP-5A).
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from ..data_gen.fraud_profiles import AS_OF, INCOME_BAND_CEILING, WINDOW_START

# Common Indian cash/reporting thresholds mules hug (PAN@50k, CTR bands). A
# "threshold-hugging" amount sits in [0.9, 1.0) x one of these.
COMMON_THRESHOLDS = (50_000.0, 100_000.0)
# A "round" amount is an exact multiple of this (structuring amounts are; the
# uniform-float legit amounts almost never are).
ROUND_STEP = 500.0
# Sweep window for rapid pass-through matching.
PASSTHROUGH_HOURS = 24.0
# Sliding window (days) used to measure a dormancy burst's concentration.
BURST_WINDOW_DAYS = 21

FEATURE_COLS: List[str] = [
    "n_txn", "n_credit", "n_debit", "inflow_total", "outflow_total",
    "txn_per_active_day", "peak_day_count",
    "out_in_ratio", "passthrough_share", "median_passthrough_minutes",
    "dormancy_burst_score", "fan_in_degree", "fan_out_degree",
    "consolidation_ratio", "round_amount_share", "threshold_hug_share",
    "odd_hours_share", "device_sharing_degree", "age_days",
    "age_volume_interaction", "kyc_mismatch_ratio", "is_current",
]


# --------------------------------------------------------------------------- #
# shared preparation (reused by typologies.py so we group the ledger once)
# --------------------------------------------------------------------------- #
class AccountLedger:
    """One account's ledger prepared once: sorted arrays + the account row.

    Both the feature builder and the typology detectors read this so we pay the
    grouping/sort cost a single time per account.
    """

    __slots__ = ("account_id", "acc_row", "df", "dt", "amount", "direction",
                 "counterparty", "device", "txn_id", "hour", "is_current",
                 "age_days", "ceiling")

    def __init__(self, account_id: str, acc_row: dict, df: pd.DataFrame):
        self.account_id = account_id
        self.acc_row = acc_row
        df = df.sort_values("_dt", kind="mergesort")
        self.df = df
        self.dt = df["_dt"].to_numpy()
        self.amount = df["amount"].to_numpy(dtype=float)
        self.direction = df["direction"].to_numpy()
        self.counterparty = df["counterparty_id"].astype(str).to_numpy()
        self.device = df["device_id"].astype(str).to_numpy()
        self.txn_id = df["txn_id"].astype(str).to_numpy()
        self.hour = df["_hour"].to_numpy()
        self.is_current = acc_row.get("account_type") == "current"
        open_date = pd.Timestamp(acc_row.get("open_date"))
        self.age_days = max(float((AS_OF - open_date).days), 0.0)
        self.ceiling = float(INCOME_BAND_CEILING.get(
            str(acc_row.get("kyc_income_band")), 50_000.0))


def is_round(amounts: np.ndarray) -> np.ndarray:
    """Exact multiple of ROUND_STEP (structuring amounts are; legit floats aren't)."""
    r = np.remainder(amounts, ROUND_STEP)
    return (r < 0.5) | (r > ROUND_STEP - 0.5)


def is_threshold_hug(amounts: np.ndarray) -> np.ndarray:
    """Amount in [0.9, 1.0) x a common reporting threshold."""
    hit = np.zeros(len(amounts), dtype=bool)
    for thr in COMMON_THRESHOLDS:
        hit |= (amounts >= 0.9 * thr) & (amounts < thr)
    return hit


def _passthrough(dt: np.ndarray, amount: np.ndarray,
                 is_credit: np.ndarray) -> tuple[float, float]:
    """Share of inflow swept out within 24h + median minutes to first sweep.

    For each credit, greedily consume subsequent debits inside the 24h window;
    the matched (capped at the credit) contributes to the pass-through share.
    """
    n = len(dt)
    if n == 0:
        return 0.0, 0.0
    inflow = float(amount[is_credit].sum())
    if inflow <= 0:
        return 0.0, 0.0
    debit_avail = np.where(is_credit, 0.0, amount).astype(float).copy()
    win = np.timedelta64(int(PASSTHROUGH_HOURS * 3600), "s")
    matched = 0.0
    minutes: List[float] = []
    j0 = 0
    for i in range(n):
        if not is_credit[i]:
            continue
        need = amount[i]
        first_min = None
        # advance a pointer to the first debit at/after this credit
        j = max(j0, i + 1)
        limit = dt[i] + win
        while j < n and dt[j] <= limit and need > 1e-6:
            if not is_credit[j] and debit_avail[j] > 1e-6:
                take = min(need, debit_avail[j])
                debit_avail[j] -= take
                need -= take
                matched += take
                if first_min is None:
                    first_min = (dt[j] - dt[i]) / np.timedelta64(1, "s") / 60.0
            j += 1
        if first_min is not None:
            minutes.append(float(first_min))
    share = min(matched / inflow, 1.0)
    med = float(np.median(minutes)) if minutes else 0.0
    return share, med


def _dormancy_burst(dt: np.ndarray) -> float:
    """0..1: long silence (at window start or a mid-gap) then a concentrated burst.

    ``dormant_days`` = the larger of the lead-in silence (WINDOW_START -> first
    txn) and the biggest inter-txn gap; ``burst_share`` = the fraction of txns in
    the busiest 21-day window. Their product is high only for a genuine dormant
    account that suddenly wakes up, and ~0 for an account active throughout.
    """
    n = len(dt)
    if n < 3:
        return 0.0
    day = np.timedelta64(1, "D")
    lead_in = (dt[0] - np.datetime64(WINDOW_START)) / day
    gaps = np.diff(dt) / day
    max_gap = float(gaps.max()) if len(gaps) else 0.0
    dormant_days = max(float(lead_in), max_gap)
    # busiest 21-day window share (two-pointer over sorted times)
    win = np.timedelta64(BURST_WINDOW_DAYS, "D")
    best = 0
    j = 0
    for i in range(n):
        while dt[i] - dt[j] > win:
            j += 1
        best = max(best, i - j + 1)
    burst_share = best / n
    return float(np.clip(dormant_days / 60.0, 0.0, 1.0) * burst_share)


def account_features(led: AccountLedger) -> Dict[str, float]:
    """The full behavioural feature vector for one prepared ledger."""
    amt, direc, dt = led.amount, led.direction, led.dt
    is_credit = direc == "credit"
    is_debit = ~is_credit
    n = len(amt)
    inflow = float(amt[is_credit].sum())
    outflow = float(amt[is_debit].sum())

    days = pd.to_datetime(dt).normalize()
    uniq_days, day_counts = np.unique(days.values, return_counts=True)
    span_days = max((dt[-1] - dt[0]) / np.timedelta64(1, "D"), 1.0) if n else 1.0

    fan_in = int(len(np.unique(led.counterparty[is_credit]))) if is_credit.any() else 0
    fan_out = int(len(np.unique(led.counterparty[is_debit]))) if is_debit.any() else 0

    passthrough_share, median_pt = _passthrough(dt, amt, is_credit)
    months = max(span_days / 30.0, 1.0)
    throughput_month = max(inflow, outflow) / months
    kyc_ratio = throughput_month / max(led.ceiling, 1.0)

    return {
        "n_txn": float(n),
        "n_credit": float(int(is_credit.sum())),
        "n_debit": float(int(is_debit.sum())),
        "inflow_total": inflow,
        "outflow_total": outflow,
        "txn_per_active_day": float(n / max(len(uniq_days), 1)),
        "peak_day_count": float(day_counts.max()) if n else 0.0,
        "out_in_ratio": float(outflow / (inflow + 1.0)),
        "passthrough_share": float(passthrough_share),
        "median_passthrough_minutes": float(median_pt),
        "dormancy_burst_score": _dormancy_burst(dt),
        "fan_in_degree": float(fan_in),
        "fan_out_degree": float(fan_out),
        "consolidation_ratio": float(fan_in / max(fan_out, 1)),
        "round_amount_share": float(is_round(amt).mean()) if n else 0.0,
        "threshold_hug_share": float(is_threshold_hug(amt).mean()) if n else 0.0,
        "odd_hours_share": float((led.hour < 5).mean()) if n else 0.0,
        "device_sharing_degree": 0.0,  # filled in by the engine (needs global map)
        "age_days": led.age_days,
        "age_volume_interaction": float(inflow / max(led.age_days, 1.0)),
        "kyc_mismatch_ratio": float(kyc_ratio),
        "is_current": 1.0 if led.is_current else 0.0,
    }


def prepare_ledgers(accounts: pd.DataFrame,
                    transactions: pd.DataFrame) -> Dict[str, AccountLedger]:
    """Group the ledger once and return an ``AccountLedger`` per account."""
    tx = transactions.copy()
    tx["_dt"] = pd.to_datetime(tx["datetime"]).to_numpy()
    tx["_hour"] = pd.to_datetime(tx["datetime"]).dt.hour.to_numpy()
    acc_rows = {r["account_id"]: r for r in accounts.to_dict("records")}
    ledgers: Dict[str, AccountLedger] = {}
    for aid, g in tx.groupby("account_id", sort=False):
        row = acc_rows.get(aid, {"account_type": "savings",
                                 "open_date": AS_OF.strftime("%Y-%m-%d"),
                                 "kyc_income_band": "25k-50k"})
        ledgers[aid] = AccountLedger(aid, row, g)
    return ledgers


def build_feature_matrix(ledgers: Dict[str, AccountLedger],
                         device_degree: Dict[str, int]) -> pd.DataFrame:
    """Assemble the account-indexed feature matrix. ``device_degree`` is the count
    of distinct OTHER accounts each account shares a device with (global signal)."""
    rows = {}
    for aid, led in ledgers.items():
        feats = account_features(led)
        feats["device_sharing_degree"] = float(device_degree.get(aid, 0))
        rows[aid] = feats
    fm = pd.DataFrame.from_dict(rows, orient="index")[FEATURE_COLS]
    fm.index.name = "account_id"
    return fm.fillna(0.0)
