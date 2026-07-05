"""The 8 named mule typology detectors (WP-5M).

Each detector inspects one prepared ``AccountLedger`` (+ the global device/link
context) and, when its behavioural signature is present, returns a
``TypologyHit`` carrying its 0-100 strength AND the CONCRETE evidence that
triggered it: the transaction IDs, counterparties and devices. That evidence is
the backbone of downstream citation gating — WP-5A's case orchestrator refuses to
emit any finding that cannot cite >=1 real transaction, so these ``txn_ids`` must
always reference rows that exist in ``transactions.csv``.

Detectors are deterministic rules (no learning, no labels). They mirror the same
8 patterns the WP-5D generator injects, but the detector and the injector share
NO code path — the detector recovers the pattern from raw rows. No user-facing
copy lives here (ml computes; backend narrates).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from . import features as F
# Reuse the canonical typology names so detector output aligns 1:1 with the
# labels the generator wrote (names only — no label data is read).
from ..data_gen.typologies import (TYP_DEVICE, TYP_DORMANCY, TYP_FAN, TYP_KYC,
                                    TYP_NEWVEL, TYP_ODD, TYP_PASS, TYP_STRUCT)

# How many evidence txn_ids/counterparties a detector keeps (representative cap so
# the case-file payload stays small; every id still resolves to a real row).
_EVIDENCE_CAP = 30

# Per-detector fire threshold (0-100). A detector "fires" (contributes a hit +
# evidence) only at/above this; below it the pattern is deemed absent. Tuned so
# injected accounts fire and clean high-velocity hard negatives do not.
FIRE_THRESHOLD = 40.0


@dataclass
class TypologyHit:
    """A fired typology detector + the evidence that triggered it.

    Fields:
      * ``name``                 canonical typology name (matches the generator).
      * ``score``                0-100 strength.
      * ``txn_ids``              concrete transaction IDs that triggered it (the
                                 citation set — every id exists in transactions.csv).
      * ``counterparties``       counterparty IDs implicated (payers / ring targets).
      * ``device_ids``           device IDs implicated (shared-device evidence).
      * ``plain_summary_inputs`` numeric facts (NOT prose) the backend narrates.
    """
    name: str
    score: float
    txn_ids: List[str] = field(default_factory=list)
    counterparties: List[str] = field(default_factory=list)
    device_ids: List[str] = field(default_factory=list)
    plain_summary_inputs: Dict[str, float] = field(default_factory=dict)


def _cap(seq) -> List[str]:
    out, seen = [], set()
    for x in seq:
        s = str(x)
        if s not in seen:
            seen.add(s)
            out.append(s)
        if len(out) >= _EVIDENCE_CAP:
            break
    return out


def _ramp(x: float, lo: float, hi: float) -> float:
    """Linear 0..100 ramp: <=lo -> 0, >=hi -> 100."""
    if hi <= lo:
        return 100.0 if x >= hi else 0.0
    return float(np.clip((x - lo) / (hi - lo), 0.0, 1.0) * 100.0)


# --------------------------------------------------------------------------- #
# 1. Fan-in / fan-out
# --------------------------------------------------------------------------- #
def detect_fan_in_fan_out(led: F.AccountLedger, ctx: dict) -> Optional[TypologyHit]:
    """Many distinct small credits consolidated out to a few counterparties."""
    is_credit = led.direction == "credit"
    is_debit = ~is_credit
    fan_in = len(np.unique(led.counterparty[is_credit])) if is_credit.any() else 0
    fan_out = len(np.unique(led.counterparty[is_debit])) if is_debit.any() else 0
    inflow = float(led.amount[is_credit].sum())
    if fan_in < 10 or inflow <= 0:
        return None
    consolidation = fan_in / max(fan_out, 1)
    # need genuine consolidation (few outflow targets) — a busy merchant fans out
    # widely and is filtered here.
    if fan_out > 8 or consolidation < 2.5:
        return None
    # strength driven by the breadth of the fan-in, tempered by how tight the
    # consolidation is (a wider spread of payers into fewer sinks scores higher).
    score = _ramp(fan_in, 10, 28) * min(consolidation / 3.0, 1.0)
    if score < FIRE_THRESHOLD:
        return None
    credit_ids = led.txn_id[is_credit]
    debit_ids = led.txn_id[is_debit]
    return TypologyHit(
        TYP_FAN, round(score, 1),
        txn_ids=_cap(list(credit_ids) + list(debit_ids)),
        counterparties=_cap(led.counterparty[is_credit]),
        plain_summary_inputs={"fan_in_degree": float(fan_in),
                              "fan_out_degree": float(fan_out),
                              "consolidation_ratio": round(consolidation, 2),
                              "inflow_total": round(inflow, 2)})


# --------------------------------------------------------------------------- #
# 2. Rapid pass-through
# --------------------------------------------------------------------------- #
def detect_rapid_pass_through(led: F.AccountLedger, ctx: dict) -> Optional[TypologyHit]:
    """A money conduit: inflow ~= outflow (money passes straight through) with a
    quick 24h sweep, and the balance hovers low relative to throughput.

    The conduit ratio (min(in,out)/max(in,out)) is the robust structural tell —
    it is high only when money that arrives leaves again, so a salaried or
    accumulating account (in >> out, balance builds) never qualifies. It is
    combined with the 24h sweep share so a genuinely fast conduit scores highest.
    """
    is_credit = led.direction == "credit"
    is_debit = ~is_credit
    inflow = float(led.amount[is_credit].sum())
    outflow = float(led.amount[is_debit].sum())
    if inflow <= 0 or outflow <= 0:
        return None
    conduit = min(inflow, outflow) / max(inflow, outflow)
    if conduit < 0.60:  # gate 1: not a balanced conduit -> not pass-through
        return None
    # gate 2: a laundering conduit FORWARDS to a few downstream parties; a gig
    # worker who merely earns-and-spends disperses to many external merchants.
    debit_cps = led.counterparty[is_debit]
    debit_amt = led.amount[is_debit]
    top3 = 0.0
    if len(debit_cps):
        by_cp = {}
        for cp, a in zip(debit_cps, debit_amt):
            by_cp[cp] = by_cp.get(cp, 0.0) + float(a)
        top = sorted(by_cp.values(), reverse=True)[:3]
        top3 = sum(top) / max(outflow, 1.0)
    if top3 < 0.55:
        return None
    share, med_min = F._passthrough(led.dt, led.amount, is_credit)
    combined = 0.5 * conduit + 0.2 * share + 0.3 * top3
    score = _ramp(combined, 0.55, 0.92)
    if score < FIRE_THRESHOLD:
        return None
    return TypologyHit(
        TYP_PASS, round(score, 1),
        txn_ids=_cap(list(led.txn_id[is_credit]) + list(led.txn_id[is_debit])),
        counterparties=_cap(debit_cps),
        plain_summary_inputs={"conduit_ratio": round(float(conduit), 3),
                              "outflow_top3_share": round(float(top3), 3),
                              "passthrough_share": round(float(share), 3),
                              "median_passthrough_minutes": round(float(med_min), 1)})


# --------------------------------------------------------------------------- #
# 3. Dormancy burst
# --------------------------------------------------------------------------- #
def detect_dormancy_burst(led: F.AccountLedger, ctx: dict) -> Optional[TypologyHit]:
    """A long silence then a concentrated high-velocity burst."""
    score_raw = F._dormancy_burst(led.dt)  # 0..1
    score = _ramp(score_raw, 0.35, 0.80)
    if score < FIRE_THRESHOLD:
        return None
    # evidence = the txns inside the busiest 21-day window
    dt = led.dt
    win = np.timedelta64(F.BURST_WINDOW_DAYS, "D")
    best_i = best_j = 0
    j = 0
    for i in range(len(dt)):
        while dt[i] - dt[j] > win:
            j += 1
        if i - j > best_i - best_j:
            best_i, best_j = i, j
    burst_ids = led.txn_id[best_j:best_i + 1]
    return TypologyHit(
        TYP_DORMANCY, round(score, 1),
        txn_ids=_cap(burst_ids),
        counterparties=_cap(led.counterparty[best_j:best_i + 1]),
        plain_summary_inputs={"dormancy_burst_score": round(float(score_raw), 3),
                              "burst_txn_count": float(best_i - best_j + 1)})


# --------------------------------------------------------------------------- #
# 4. New-account velocity
# --------------------------------------------------------------------------- #
def detect_new_account_velocity(led: F.AccountLedger, ctx: dict) -> Optional[TypologyHit]:
    """Account age < 30d carrying disproportionate volume."""
    if led.age_days >= 30:
        return None
    n = len(led.amount)
    inflow = float(led.amount[led.direction == "credit"].sum())
    # volume relative to a very young account: txns/day and rupees/day both high
    per_day = n / max(led.age_days, 1.0)
    if n < 15 or per_day < 1.5:
        return None
    score = 0.5 * _ramp(per_day, 1.5, 6.0) + 0.5 * _ramp(n, 15, 40)
    # amplify: the younger the account, the more anomalous the same volume
    score = min(100.0, score * (1.0 + (30.0 - led.age_days) / 60.0))
    if score < FIRE_THRESHOLD:
        return None
    return TypologyHit(
        TYP_NEWVEL, round(score, 1),
        txn_ids=_cap(led.txn_id),
        counterparties=_cap(led.counterparty),
        plain_summary_inputs={"age_days": round(led.age_days, 1),
                              "n_txn": float(n), "inflow_total": round(inflow, 2),
                              "txn_per_day": round(per_day, 2)})


# --------------------------------------------------------------------------- #
# 5. KYC-income mismatch
# --------------------------------------------------------------------------- #
def detect_kyc_income_mismatch(led: F.AccountLedger, ctx: dict) -> Optional[TypologyHit]:
    """Monthly throughput far above the declared income band.

    Business (current) accounts legitimately run turnover well above personal
    income, so this detector applies to personal (savings) accounts — which is
    also where the generator injects the mismatch. This is what keeps the
    small-merchant hard negative cleared.
    """
    if led.is_current:
        return None
    is_credit = led.direction == "credit"
    is_debit = ~is_credit
    inflow = float(led.amount[is_credit].sum())
    outflow = float(led.amount[is_debit].sum())
    span_days = max((led.dt[-1] - led.dt[0]) / np.timedelta64(1, "D"), 1.0) \
        if len(led.dt) else 1.0
    throughput_month = max(inflow, outflow) / max(span_days / 30.0, 1.0)
    ratio = throughput_month / max(led.ceiling, 1.0)
    if ratio < 4.0:
        return None
    score = _ramp(ratio, 4.0, 10.0)
    if score < FIRE_THRESHOLD:
        return None
    # evidence: the largest credits driving the excess throughput
    order = np.argsort(-led.amount)
    big = [i for i in order if is_credit[i]][:_EVIDENCE_CAP]
    return TypologyHit(
        TYP_KYC, round(score, 1),
        txn_ids=_cap(led.txn_id[big]),
        counterparties=_cap(led.counterparty[big]),
        plain_summary_inputs={"kyc_income_band": led.acc_row.get("kyc_income_band"),
                              "band_ceiling": led.ceiling,
                              "monthly_throughput": round(throughput_month, 2),
                              "throughput_ratio": round(ratio, 2)})


# --------------------------------------------------------------------------- #
# 6. Round-amount structuring
# --------------------------------------------------------------------------- #
def detect_round_amount_structuring(led: F.AccountLedger, ctx: dict) -> Optional[TypologyHit]:
    """Dense round amounts pinned just under reporting thresholds."""
    amt = led.amount
    if len(amt) == 0:
        return None
    hug = F.is_threshold_hug(amt) & F.is_round(amt)
    n_hug = int(hug.sum())
    hug_share = float(hug.mean())
    if n_hug < 6:
        return None
    score = max(_ramp(n_hug, 6, 20), _ramp(hug_share, 0.05, 0.30))
    if score < FIRE_THRESHOLD:
        return None
    return TypologyHit(
        TYP_STRUCT, round(score, 1),
        txn_ids=_cap(led.txn_id[hug]),
        counterparties=_cap(led.counterparty[hug]),
        plain_summary_inputs={"threshold_hug_count": float(n_hug),
                              "threshold_hug_share": round(hug_share, 3)})


# --------------------------------------------------------------------------- #
# 7. Odd-hours pattern
# --------------------------------------------------------------------------- #
def detect_odd_hours(led: F.AccountLedger, ctx: dict) -> Optional[TypologyHit]:
    """Activity concentrated in the 00:00-05:00 window."""
    n = len(led.amount)
    if n == 0:
        return None
    night = led.hour < 5
    share = float(night.mean())
    n_night = int(night.sum())
    if share < 0.25 or n_night < 5:
        return None
    score = _ramp(share, 0.25, 0.60)
    if score < FIRE_THRESHOLD:
        return None
    return TypologyHit(
        TYP_ODD, round(score, 1),
        txn_ids=_cap(led.txn_id[night]),
        counterparties=_cap(led.counterparty[night]),
        plain_summary_inputs={"odd_hours_share": round(share, 3),
                              "odd_hours_count": float(n_night)})


# --------------------------------------------------------------------------- #
# 8. Shared device / endpoint — the ring glue
# --------------------------------------------------------------------------- #
def detect_shared_device(led: F.AccountLedger, ctx: dict) -> Optional[TypologyHit]:
    """One device_id reused across >=3 accounts (structural ring glue).

    ``ctx['device_accounts']`` maps device_id -> set of account_ids that transact
    on it. A device shared by >=3 distinct accounts is the strongest structural
    mule tell; the strength scales with the size of the shared cluster.
    """
    dev_accounts: Dict[str, set] = ctx["device_accounts"]
    shared_devs = []
    co_accounts: set = set()
    max_cluster = 0
    for dev in np.unique(led.device):
        accts = dev_accounts.get(dev, set())
        if len(accts) >= 3:
            shared_devs.append(dev)
            co_accounts |= accts
            max_cluster = max(max_cluster, len(accts))
    if not shared_devs:
        return None
    co_accounts.discard(led.account_id)
    score = _ramp(max_cluster, 3, 9)
    if score < FIRE_THRESHOLD:
        return None
    on_dev = np.isin(led.device, shared_devs)
    return TypologyHit(
        TYP_DEVICE, round(score, 1),
        txn_ids=_cap(led.txn_id[on_dev]),
        counterparties=_cap(sorted(co_accounts)),
        device_ids=_cap(shared_devs),
        plain_summary_inputs={"shared_device_count": float(len(shared_devs)),
                              "cluster_size": float(max_cluster),
                              "co_account_count": float(len(co_accounts))})


DETECTORS = (
    detect_fan_in_fan_out,
    detect_rapid_pass_through,
    detect_dormancy_burst,
    detect_new_account_velocity,
    detect_kyc_income_mismatch,
    detect_round_amount_structuring,
    detect_odd_hours,
    detect_shared_device,
)


def detect_all(led: F.AccountLedger, ctx: dict) -> List[TypologyHit]:
    """Run every detector; return the fired hits (score >= FIRE_THRESHOLD)."""
    hits = []
    for det in DETECTORS:
        hit = det(led, ctx)
        if hit is not None:
            hits.append(hit)
    return hits
