"""The 8 money-mule typologies as parameterized transaction injectors (WP-5D).

Each injector is a pure function ``inject_*(acc, ring, rng) -> list[dict]`` that
appends raw transaction rows (without ``txn_id``/``account_id``/``balance_after``
— ``build.py`` stamps those) expressing one behaviour. A ring mule is assigned
2-4 of these in ``fraud_profiles.py`` and the union forms its signature.

Grounding: these mirror 8 of the ~19 behaviour patterns RBIH's MuleHunter.AI
describes for mule detection:

  1. fan_in_fan_out        many small distinct credits -> rapid consolidation out
  2. rapid_pass_through    >=80% of inflow leaves within 24h; balance ~0
  3. dormancy_burst        long dormant, then a sudden high-velocity burst
  4. new_account_velocity  account age <30d with disproportionate volume
  5. kyc_income_mismatch   monthly throughput >> declared income band
  6. round_amount_structuring   dense round amounts just under reporting thresholds
  7. odd_hours             activity concentrated 00:00-05:00
  8. shared_device         one device_id reused across >=3 ring accounts (glue)

Deterministic under the account's seeded RNG.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

import numpy as np

# Canonical typology names (also the values stored in fraud_ground_truth.csv).
TYP_FAN = "fan_in_fan_out"
TYP_PASS = "rapid_pass_through"
TYP_DORMANCY = "dormancy_burst"
TYP_NEWVEL = "new_account_velocity"
TYP_KYC = "kyc_income_mismatch"
TYP_STRUCT = "round_amount_structuring"
TYP_ODD = "odd_hours"
TYP_DEVICE = "shared_device"

ALL_TYPOLOGIES = (TYP_FAN, TYP_PASS, TYP_DORMANCY, TYP_NEWVEL,
                  TYP_KYC, TYP_STRUCT, TYP_ODD, TYP_DEVICE)

# Common Indian cash/reporting thresholds mules hug (PAN@50k, CTR@10L bands).
STRUCTURING_THRESHOLDS = (50_000, 100_000)
# Dense round amounts just *under* those thresholds.
STRUCTURING_AMOUNTS = (48_500, 49_000, 49_500, 45_000, 98_500, 99_000, 99_500)

CHANNELS = ("UPI", "IMPS", "NEFT", "ATM", "POS")


# --------------------------------------------------------------------------- #
# shared helpers (also used by legit.py)
# --------------------------------------------------------------------------- #
def txn(dt: datetime, direction: str, amount: float, channel: str,
        counterparty: str, device: str) -> dict:
    return dict(datetime=dt, direction=direction, amount=round(float(amount), 2),
                channel=channel, counterparty_id=counterparty, device_id=device)


def rand_dt(rng: np.random.Generator, start: datetime, end: datetime,
            odd: bool = False) -> datetime:
    span = max((end - start).total_seconds(), 1.0)
    t = start + timedelta(seconds=float(rng.uniform(0, span)))
    if odd:
        t = t.replace(hour=int(rng.integers(0, 5)), minute=int(rng.integers(0, 60)),
                      second=int(rng.integers(0, 60)))
    return t


def pick_channel(rng: np.random.Generator, amount: float, kind: str = "transfer") -> str:
    if kind == "atm":
        return "ATM"
    if kind == "pos":
        return "POS"
    if amount < 20_000:
        return str(rng.choice(("UPI", "IMPS"), p=(0.85, 0.15)))
    if amount < 100_000:
        return str(rng.choice(("IMPS", "UPI", "NEFT"), p=(0.50, 0.20, 0.30)))
    return str(rng.choice(("NEFT", "IMPS"), p=(0.70, 0.30)))


# --------------------------------------------------------------------------- #
# 1. Fan-in / fan-out
# --------------------------------------------------------------------------- #
def inject_fan_in_fan_out(acc, ring, rng: np.random.Generator) -> List[dict]:
    """Many small credits from distinct payers, then consolidation out to the ring."""
    rows: List[dict] = []
    n_in = int(rng.integers(22, 40))
    total_in = 0.0
    for k in range(n_in):
        amt = float(rng.uniform(1_500, 9_000)) * acc.amount_scale
        total_in += amt
        cp = f"PAYER-{acc.account_id[-4:]}-{k:02d}"
        rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end, acc.odd_hours),
                        "credit", amt, pick_channel(rng, amt), cp, ring["device"]))
    # consolidate outward to cash-out endpoints + recruiter (intra-universe edges)
    targets = list(ring["cashouts"]) + [ring["recruiter"]]
    n_out = int(rng.integers(2, 5))
    for j in range(n_out):
        amt = total_in / n_out * float(rng.uniform(0.80, 1.0))
        tgt = targets[j % len(targets)]
        rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end, acc.odd_hours),
                        "debit", amt, pick_channel(rng, amt), tgt, ring["device"]))
    return rows


# --------------------------------------------------------------------------- #
# 2. Rapid pass-through
# --------------------------------------------------------------------------- #
def inject_rapid_pass_through(acc, ring, rng: np.random.Generator) -> List[dict]:
    """Each inflow is swept out (80-95%) to a cash-out endpoint within 24h."""
    rows: List[dict] = []
    targets = list(ring["cashouts"]) or [ring["recruiter"]]
    n = int(rng.integers(8, 16))
    for k in range(n):
        amt = float(rng.uniform(8_000, 40_000)) * acc.amount_scale
        t_in = rand_dt(rng, acc.active_start, acc.active_end, acc.odd_hours)
        cp = f"PAYER-{acc.account_id[-4:]}-P{k:02d}"
        rows.append(txn(t_in, "credit", amt, pick_channel(rng, amt), cp, ring["device"]))
        # swept out within 24h (minutes..~20h)
        t_out = t_in + timedelta(minutes=int(rng.integers(3, 20 * 60)))
        if t_out > acc.active_end:
            t_out = acc.active_end
        out_amt = amt * float(rng.uniform(0.80, 0.95))
        tgt = targets[k % len(targets)]
        rows.append(txn(t_out, "debit", out_amt, pick_channel(rng, out_amt), tgt,
                        ring["device"]))
    return rows


# --------------------------------------------------------------------------- #
# 3. Dormancy burst
# --------------------------------------------------------------------------- #
def inject_dormancy_burst(acc, ring, rng: np.random.Generator) -> List[dict]:
    """A concentrated burst of activity after >=60 dormant days.

    ``acc.active_start`` is already pinned to the burst window (last ~3 weeks) by
    the temporal-mode logic, so we simply emit a high-velocity flurry there.
    """
    rows: List[dict] = []
    n = int(rng.integers(16, 28))
    targets = list(ring["cashouts"]) + [ring["recruiter"]]
    for k in range(n):
        if rng.random() < 0.6:
            amt = float(rng.uniform(2_000, 12_000)) * acc.amount_scale
            cp = f"PAYER-{acc.account_id[-4:]}-B{k:02d}"
            rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end, acc.odd_hours),
                            "credit", amt, pick_channel(rng, amt), cp, ring["device"]))
        else:
            amt = float(rng.uniform(5_000, 25_000)) * acc.amount_scale
            tgt = targets[k % len(targets)]
            rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end, acc.odd_hours),
                            "debit", amt, pick_channel(rng, amt), tgt, ring["device"]))
    return rows


# --------------------------------------------------------------------------- #
# 4. New-account velocity
# --------------------------------------------------------------------------- #
def inject_new_account_velocity(acc, ring, rng: np.random.Generator) -> List[dict]:
    """Disproportionate volume for an account opened <30 days ago.

    ``acc.active_start`` is pinned just after ``open_date``; we emit a dense
    stream so age-x-volume is anomalous.
    """
    rows: List[dict] = []
    n = int(rng.integers(18, 30))
    targets = list(ring["cashouts"]) + [ring["recruiter"]]
    for k in range(n):
        if rng.random() < 0.62:
            amt = float(rng.uniform(1_500, 10_000)) * acc.amount_scale
            cp = f"PAYER-{acc.account_id[-4:]}-N{k:02d}"
            rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end, acc.odd_hours),
                            "credit", amt, pick_channel(rng, amt), cp, ring["device"]))
        else:
            amt = float(rng.uniform(4_000, 20_000)) * acc.amount_scale
            tgt = targets[k % len(targets)]
            rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end, acc.odd_hours),
                            "debit", amt, pick_channel(rng, amt), tgt, ring["device"]))
    return rows


# --------------------------------------------------------------------------- #
# 5. KYC-income mismatch
# --------------------------------------------------------------------------- #
def inject_kyc_income_mismatch(acc, ring, rng: np.random.Generator) -> List[dict]:
    """Large throughput far above the declared income band.

    The scale-up already rides on ``acc.amount_scale`` (set high for mismatch
    accounts); here we add a handful of oversized credits + sweeps to push
    monthly throughput well beyond the KYC ceiling.
    """
    rows: List[dict] = []
    n = int(rng.integers(6, 12))
    targets = list(ring["cashouts"]) + [ring["recruiter"]]
    for k in range(n):
        amt = float(rng.uniform(60_000, 180_000))
        cp = f"BIZ-{acc.account_id[-4:]}-{k:02d}"
        t_in = rand_dt(rng, acc.active_start, acc.active_end, acc.odd_hours)
        rows.append(txn(t_in, "credit", amt, pick_channel(rng, amt), cp, ring["device"]))
        tgt = targets[k % len(targets)]
        rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end, acc.odd_hours),
                        "debit", amt * float(rng.uniform(0.75, 0.95)),
                        pick_channel(rng, amt), tgt, ring["device"]))
    return rows


# --------------------------------------------------------------------------- #
# 6. Round-amount structuring
# --------------------------------------------------------------------------- #
def inject_round_amount_structuring(acc, ring, rng: np.random.Generator) -> List[dict]:
    """Dense round amounts pinned just under reporting thresholds (e.g. Rs 49,500)."""
    rows: List[dict] = []
    n = int(rng.integers(12, 24))
    targets = list(ring["cashouts"]) + [ring["recruiter"]]
    for k in range(n):
        amt = float(rng.choice(STRUCTURING_AMOUNTS))
        if rng.random() < 0.5:
            cp = f"PAYER-{acc.account_id[-4:]}-S{k:02d}"
            rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end, acc.odd_hours),
                            "credit", amt, pick_channel(rng, amt), cp, ring["device"]))
        else:
            tgt = targets[k % len(targets)]
            rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end, acc.odd_hours),
                            "debit", amt, pick_channel(rng, amt), tgt, ring["device"]))
    return rows


# --------------------------------------------------------------------------- #
# 7. Odd-hours pattern
# --------------------------------------------------------------------------- #
def inject_odd_hours(acc, ring, rng: np.random.Generator) -> List[dict]:
    """A batch of activity concentrated in the 00:00-05:00 window."""
    rows: List[dict] = []
    n = int(rng.integers(12, 22))
    targets = list(ring["cashouts"]) + [ring["recruiter"]]
    for k in range(n):
        if rng.random() < 0.55:
            amt = float(rng.uniform(2_000, 12_000)) * acc.amount_scale
            cp = f"PAYER-{acc.account_id[-4:]}-O{k:02d}"
            rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end, odd=True),
                            "credit", amt, pick_channel(rng, amt), cp, ring["device"]))
        else:
            amt = float(rng.uniform(4_000, 18_000)) * acc.amount_scale
            tgt = targets[k % len(targets)]
            rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end, odd=True),
                            "debit", amt, pick_channel(rng, amt), tgt, ring["device"]))
    return rows


# --------------------------------------------------------------------------- #
# 8. Shared device — the ring glue (resolver, not an emitter)
# --------------------------------------------------------------------------- #
def resolve_shared_device(acc, ring) -> str:
    """Return the device_id a ring account transacts on.

    ``shared_device`` is expressed structurally: every ring account stamps the
    *same* ``ring['device']`` on its mule-activity rows, so a single device spans
    >=3 accounts. (All ring injectors above already pass ``ring['device']``; this
    resolver documents the contract and is used for ring accounts' cash-out rows.)
    """
    return ring["device"]


# Dispatch map: typology name -> injector (the 6 additive emitters).
# dormancy/new-velocity are temporal *modes* whose bursts are emitted here too.
INJECTORS = {
    TYP_FAN: inject_fan_in_fan_out,
    TYP_PASS: inject_rapid_pass_through,
    TYP_DORMANCY: inject_dormancy_burst,
    TYP_NEWVEL: inject_new_account_velocity,
    TYP_KYC: inject_kyc_income_mismatch,
    TYP_STRUCT: inject_round_amount_structuring,
    TYP_ODD: inject_odd_hours,
}
