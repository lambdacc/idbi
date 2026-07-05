"""Benign transaction patterns for non-mule accounts (WP-5D).

Legit accounts get realistic salary / merchant / utility rhythms; hard-negative
accounts get *high-velocity* but structurally clean flows (a gig worker's many
small daily credits, or a small merchant's POS stream) — the "explainably
cleared" demo stars. Nothing here uses a shared device, sweeps inflow out within
24h, or hugs round thresholds, so the detectors must clear them on structure,
not on volume.
"""
from __future__ import annotations

from datetime import timedelta
from typing import List

import numpy as np

from .fraud_profiles import AS_OF, INCOME_BAND_CEILING
from .typologies import pick_channel, rand_dt, txn

_ACTIVITY_DEBITS_PER_DAY = {"low": 0.5, "medium": 1.2, "high": 2.4}


def _month_anchors(open_date, end):
    """Salary/utility anchor datetimes (~monthly) within the active window."""
    start = max(open_date, end - timedelta(days=90))
    anchors = []
    d = start.replace(hour=10, minute=0, second=0)
    while d <= end:
        anchors.append(d)
        # jump ~1 month
        d = d + timedelta(days=30)
    return anchors


def gen_legit(acc, rng: np.random.Generator) -> List[dict]:
    """Salary-in / spend-out rhythm for a retail savings or MSME current account."""
    rows: List[dict] = []
    start = max(acc.open_date, AS_OF - timedelta(days=90))
    end = AS_OF
    dev = acc.home_device_id
    ceiling = INCOME_BAND_CEILING[acc.kyc_income_band]

    if acc.account_type == "current":
        # merchant: frequent small customer credits + weekly supplier debits + payroll
        per_day = {"low": 3, "medium": 5, "high": 8}[acc.activity_level]
        days = max((end - start).days, 1)
        n_credits = int(per_day * days * float(rng.uniform(0.8, 1.2)))
        n_credits = min(n_credits, 2200)
        for _ in range(n_credits):
            amt = float(rng.uniform(200, 6_000))
            rows.append(txn(rand_dt(rng, start, end), "credit", amt,
                            pick_channel(rng, amt, "pos" if rng.random() < 0.5 else "transfer"),
                            f"CUST-{int(rng.integers(0, 4000)):04d}", dev))
        # supplier + payroll debits (weekly-ish)
        n_deb = int(days / 7 * 3)
        for _ in range(n_deb):
            amt = float(rng.uniform(10_000, min(ceiling * 3, 250_000)))
            rows.append(txn(rand_dt(rng, start, end), "debit", amt,
                            pick_channel(rng, amt), f"SUPPLIER-{int(rng.integers(0, 60)):03d}", dev))
        return rows

    # savings: monthly salary credit + rent/utility + everyday spends
    salary = float(rng.uniform(0.45, 0.9)) * ceiling
    clamp = lambda d: min(max(d, start), end)  # keep anchors inside the window
    for a in _month_anchors(start, end):
        rows.append(txn(clamp(a + timedelta(hours=float(rng.uniform(0, 6)))), "credit",
                        salary * float(rng.uniform(0.95, 1.05)), "NEFT",
                        f"EMPLOYER-{acc.account_id[-3:]}", dev))
        # rent / utilities a few days later
        rows.append(txn(clamp(a + timedelta(days=float(rng.uniform(2, 6)))), "debit",
                        salary * float(rng.uniform(0.20, 0.35)), "NEFT",
                        f"LANDLORD-{acc.account_id[-3:]}", dev))
        rows.append(txn(clamp(a + timedelta(days=float(rng.uniform(4, 9)))), "debit",
                        float(rng.uniform(500, 4_000)), "UPI",
                        f"UTILITY-{int(rng.integers(0, 40)):02d}", dev))

    days = max((end - start).days, 1)
    n_spend = int(days * _ACTIVITY_DEBITS_PER_DAY[acc.activity_level] * float(rng.uniform(0.8, 1.2)))
    for _ in range(n_spend):
        amt = float(rng.uniform(80, 3_500))
        kind = "atm" if rng.random() < 0.12 else ("pos" if rng.random() < 0.4 else "transfer")
        cp = "ATM-CASH" if kind == "atm" else f"MERCHANT-{int(rng.integers(0, 800)):03d}"
        rows.append(txn(rand_dt(rng, start, end), "debit", amt,
                        pick_channel(rng, amt, kind), cp, dev))
    return rows


def gen_hard_negative(acc, rng: np.random.Generator) -> List[dict]:
    """High-velocity but clean: gig-worker micro-credits or a busy small merchant.

    Deliberately EXHIBITS high velocity (the trait that trips naive rules) while
    AVOIDING every structural mule signature: no shared device (own device only),
    no <24h sweep of inflow, no round-threshold amounts, daytime hours, and a
    balance that accumulates rather than hovering at zero.
    """
    rows: List[dict] = []
    start = max(acc.open_date, AS_OF - timedelta(days=90))
    end = AS_OF
    dev = acc.home_device_id
    days = max((end - start).days, 1)

    if acc.account_type == "current":
        # small merchant: dense POS/UPI customer credits
        per_day = int(rng.integers(10, 17))
        for _ in range(per_day * days):
            amt = float(rng.uniform(120, 2_400))  # varied, never round thresholds
            rows.append(txn(rand_dt(rng, start, end), "credit", amt,
                            "POS" if rng.random() < 0.55 else "UPI",
                            f"CUST-{int(rng.integers(0, 6000)):04d}", dev))
    else:
        # gig worker: many small platform payouts + tips
        per_day = int(rng.integers(7, 13))
        for _ in range(per_day * days):
            amt = float(rng.uniform(60, 900))
            rows.append(txn(rand_dt(rng, start, end), "credit", amt, "UPI",
                            f"PLATFORM-{int(rng.integers(0, 5)):01d}", dev))

    # withdrawals/spends: gradual, NOT a >=80% same-day sweep (balance builds up)
    n_out = int(days * 1.3)
    for _ in range(n_out):
        amt = float(rng.uniform(300, 6_000))
        kind = "atm" if rng.random() < 0.35 else "transfer"
        cp = "ATM-CASH" if kind == "atm" else f"MERCHANT-{int(rng.integers(0, 500)):03d}"
        rows.append(txn(rand_dt(rng, start, end), "debit", amt,
                        pick_channel(rng, amt, kind), cp, dev))
    return rows
