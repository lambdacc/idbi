"""Latent account universe for SentinelPulse (Track 05, WP-5D).

Mirrors the latent-variable philosophy of ``app/data_gen/profiles.py``: every
account is drawn from *hidden truth variables* FIRST — ``is_mule``, ring
membership + role, ``activity_level`` and the KYC ``income_band`` — and the
transaction generator (``build.py``) then emits observable rows conditioned on
those latents. That is what makes the mule typologies co-occur into a coherent
ring signature instead of independent noise (the same trick that lets the MSME
cohort's authenticity composites fire).

Grounding: RBIH's MuleHunter.AI documents ~19 mule behaviour patterns; WP-5D
implements the 8 listed in ``typologies.py``. Ring topology (a handful of mule
"collector" accounts feeding 1 recruiter + 2-3 cash-out endpoints) follows the
standard laundering chain collector -> layer -> cash-out.

GROUND-TRUTH ISOLATION: ``is_mule`` / ``ring_id`` / ``role`` /
``is_hard_negative`` / ``typologies`` live ONLY on this latent object and in
``fraud_ground_truth.csv``. They are eval labels and MUST NOT be read by any
scoring/runtime module — ``accounts.csv`` (the engine's input) deliberately
omits them.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np

from . import typologies as T

# --------------------------------------------------------------------------- #
# Universe constants (locked in WP-5D spec)
# --------------------------------------------------------------------------- #
FRAUD_SEED = 20260705                     # project seed convention (yyyymmdd)
AS_OF = datetime(2026, 6, 30, 23, 59, 0)  # last day of the 90-day window
WINDOW_DAYS = 90
# window start floored to midnight so day-anchored legit rows stay inside it
WINDOW_START = (AS_OF - timedelta(days=WINDOW_DAYS)).replace(hour=0, minute=0, second=0)

N_ACCOUNTS = 800
N_CURRENT = 200                           # mapped to MSME entity_ids (join key)
N_SAVINGS = N_ACCOUNTS - N_CURRENT        # 600 retail savings

# Ring structure: 6 rings, 4-8 mules + 1 recruiter + 2-3 cash-out endpoints each.
RING_MULE_SIZES = [4, 5, 5, 6, 6, 6]      # -> 32 mules  (is_mule=1, ~4%)
RING_CASHOUT_SIZES = [2, 3, 2, 3, 2, 3]   # -> 15 cash-out endpoints
N_RINGS = len(RING_MULE_SIZES)
N_MULES = sum(RING_MULE_SIZES)            # 32
N_RECRUITERS = N_RINGS                    # 6
N_CASHOUTS = sum(RING_CASHOUT_SIZES)      # 15
N_HARD_NEG = 10                           # gig-worker / small-merchant clean stars

# KYC income bands (declared monthly income) with their monthly-throughput ceiling.
INCOME_BANDS = ("0-25k", "25k-50k", "50k-1L", "1L-3L", "3L+")
INCOME_BAND_CEILING = {
    "0-25k": 25_000, "25k-50k": 50_000, "50k-1L": 100_000,
    "1L-3L": 300_000, "3L+": 600_000,
}

ACTIVITY_LEVELS = ("low", "medium", "high")

# Roles
ROLE_LEGIT = "legit"
ROLE_MULE = "mule"
ROLE_RECRUITER = "recruiter"
ROLE_CASHOUT = "cashout"
ROLE_HARDNEG = "hard_negative"


@dataclass
class AccountProfile:
    """One synthetic account with its latent drivers + observable KYC fields.

    The ``account_id`` .. ``activity_level`` block is what the engine may see
    (via ``accounts.csv``). Everything below the ``--- ground truth ---`` line is
    eval-only and never written to ``accounts.csv``.
    """
    account_id: str
    account_type: str                 # "savings" | "current"
    open_date: datetime
    kyc_income_band: str
    linked_entity_id: Optional[str]   # MSME join key for current accounts, else None
    activity_level: str

    home_device_id: str               # the account's own device (used for legit rows)

    # --- ground truth (eval only) ---
    is_mule: int = 0
    ring_id: Optional[str] = None
    role: str = ROLE_LEGIT
    is_hard_negative: int = 0
    typologies: List[str] = field(default_factory=list)

    # active transaction window (derived from temporal mode) — build-time only
    active_start: datetime = WINDOW_START
    active_end: datetime = AS_OF
    amount_scale: float = 1.0         # KYC-mismatch throughput multiplier
    odd_hours: bool = False

    seed: int = 0

    def rng(self, salt: int = 0) -> np.random.Generator:
        return np.random.default_rng(self.seed + salt)


# --------------------------------------------------------------------------- #
# MSME join keys (read-only import from platform core)
# --------------------------------------------------------------------------- #
def _msme_entity_ids(n_needed: int) -> List[str]:
    """Read entity_ids from the MSME cohort as a JOIN KEY ONLY (read-only).

    We only ever read the ids — no MSME generator is invoked or mutated. A
    deterministic fallback keeps the build hermetic if core changes shape.
    """
    try:
        from app.data_gen.build_dataset import build_profiles
        ids = [p.entity_id for p in build_profiles(n_random=n_needed + 30)]
        if len(ids) >= n_needed:
            return ids[:n_needed]
    except Exception:
        pass
    return [f"E{20261000 + i:06d}" for i in range(n_needed)]


# --------------------------------------------------------------------------- #
# Universe builder
# --------------------------------------------------------------------------- #
def _assign_mule_typologies(rng: np.random.Generator) -> Tuple[List[str], str]:
    """Pick 2-4 typologies for a mule + its temporal mode.

    Every mule shares the ring device (``shared_device``) and moves money
    (``fan_in_fan_out`` and/or ``rapid_pass_through``); it may additionally add a
    temporal mode (new-account / dormancy) and behavioural typologies, capped at
    four so the signature stays legible.
    """
    mode = str(rng.choice(("aged", "new_velocity", "dormant_burst"),
                          p=(0.40, 0.30, 0.30)))
    behavioural = [T.TYP_FAN, T.TYP_PASS, T.TYP_KYC, T.TYP_STRUCT, T.TYP_ODD]
    k = int(rng.integers(1, 4))  # 1..3 behavioural picks
    extras = list(rng.choice(behavioural, size=k, replace=False))
    if not (T.TYP_FAN in extras or T.TYP_PASS in extras):
        extras[0] = T.TYP_FAN  # guarantee outbound money flow -> ring edges

    typ = [T.TYP_DEVICE]
    if mode == "new_velocity":
        typ.append(T.TYP_NEWVEL)
    elif mode == "dormant_burst":
        typ.append(T.TYP_DORMANCY)
    for e in extras:
        if e not in typ:
            typ.append(e)
    typ = typ[:4]
    # Re-guarantee money flow survived the cap.
    if not (T.TYP_FAN in typ or T.TYP_PASS in typ):
        typ[-1] = T.TYP_FAN
    return typ, mode


def _temporal_window(rng: np.random.Generator, mode: str) -> Tuple[datetime, datetime, datetime]:
    """Return (open_date, active_start, active_end) for a mule's temporal mode."""
    if mode == "new_velocity":
        open_date = AS_OF - timedelta(days=int(rng.integers(6, 29)))
        return open_date, open_date + timedelta(hours=6), AS_OF
    if mode == "dormant_burst":
        open_date = AS_OF - timedelta(days=int(rng.integers(400, 2500)))
        burst_start = AS_OF - timedelta(days=int(rng.integers(18, 28)))
        return open_date, burst_start, AS_OF  # >=60 dormant days before burst
    open_date = AS_OF - timedelta(days=int(rng.integers(200, 2500)))
    return open_date, WINDOW_START, AS_OF


def build_universe(seed: int = FRAUD_SEED) -> Tuple[Dict[str, AccountProfile], Dict[str, dict]]:
    """Construct all 800 latent accounts and the 6-ring topology.

    Returns ``(accounts_by_id, rings)`` where each ring dict carries its member
    account_ids by role plus the shared ``device`` id (the ring glue).
    """
    rng = np.random.default_rng(seed)
    accounts: Dict[str, AccountProfile] = {}

    def acc_id(i: int) -> str:
        return f"ACC{i + 1:05d}"

    # Index layout: [mules][recruiters][cashouts][hard_neg][legit]
    idx = 0
    mule_ids = [acc_id(idx + j) for j in range(N_MULES)]; idx += N_MULES
    recruiter_ids = [acc_id(idx + j) for j in range(N_RECRUITERS)]; idx += N_RECRUITERS
    cashout_ids = [acc_id(idx + j) for j in range(N_CASHOUTS)]; idx += N_CASHOUTS
    hardneg_ids = [acc_id(idx + j) for j in range(N_HARD_NEG)]; idx += N_HARD_NEG
    legit_ids = [acc_id(idx + j) for j in range(N_ACCOUNTS - idx)]

    # --- current-account assignment (200): all hard-neg merchants + legit fill ---
    # Hard negatives: half gig-worker (savings), half small-merchant (current).
    hardneg_current = set(hardneg_ids[N_HARD_NEG // 2:])
    n_current_from_legit = N_CURRENT - len(hardneg_current)
    entity_ids = _msme_entity_ids(N_CURRENT)
    current_legit = set(legit_ids[:n_current_from_legit])

    ent_iter = iter(entity_ids)

    def _open_old(r: np.random.Generator) -> datetime:
        return AS_OF - timedelta(days=int(r.integers(300, 2600)))

    # ---- rings ----
    rings: Dict[str, dict] = {}
    mp = cp = 0
    for r in range(N_RINGS):
        rid = f"R{r + 1}"
        ms = mule_ids[mp:mp + RING_MULE_SIZES[r]]; mp += RING_MULE_SIZES[r]
        cs = cashout_ids[cp:cp + RING_CASHOUT_SIZES[r]]; cp += RING_CASHOUT_SIZES[r]
        rings[rid] = dict(mules=ms, recruiter=recruiter_ids[r], cashouts=cs,
                          device=f"DEV-RING{r + 1}")

    # ---- mules ----
    for gi, (rid, ring) in enumerate(rings.items()):
        for j, aid in enumerate(ring["mules"]):
            aseed = seed + 1000 + gi * 50 + j
            arng = np.random.default_rng(aseed)
            typ, mode = _assign_mule_typologies(arng)
            open_date, a_start, a_end = _temporal_window(arng, mode)
            kyc_mismatch = T.TYP_KYC in typ
            band = str(arng.choice(("0-25k", "25k-50k"))) if kyc_mismatch \
                else str(arng.choice(INCOME_BANDS[:3]))
            accounts[aid] = AccountProfile(
                account_id=aid, account_type="savings", open_date=open_date,
                kyc_income_band=band, linked_entity_id=None,
                activity_level="high", home_device_id=f"DEV-{aid}",
                is_mule=1, ring_id=rid, role=ROLE_MULE, typologies=typ,
                active_start=a_start, active_end=a_end,
                amount_scale=float(arng.uniform(3.0, 6.0)) if kyc_mismatch else 1.0,
                odd_hours=T.TYP_ODD in typ, seed=aseed,
            )

    # ---- recruiters + cash-out endpoints (ring-associated, is_mule=0) ----
    for gi, (rid, ring) in enumerate(rings.items()):
        rseed = seed + 5000 + gi
        rrng = np.random.default_rng(rseed)
        accounts[ring["recruiter"]] = AccountProfile(
            account_id=ring["recruiter"], account_type="savings",
            open_date=_open_old(rrng), kyc_income_band=str(rrng.choice(INCOME_BANDS[1:3])),
            linked_entity_id=None, activity_level="high",
            home_device_id=f"DEV-{ring['recruiter']}", is_mule=0, ring_id=rid,
            role=ROLE_RECRUITER, typologies=[T.TYP_DEVICE, T.TYP_FAN], seed=rseed,
        )
        for k, aid in enumerate(ring["cashouts"]):
            cseed = seed + 6000 + gi * 20 + k
            crng = np.random.default_rng(cseed)
            accounts[aid] = AccountProfile(
                account_id=aid, account_type="savings", open_date=_open_old(crng),
                kyc_income_band=str(crng.choice(INCOME_BANDS[:3])), linked_entity_id=None,
                activity_level="high", home_device_id=f"DEV-{aid}", is_mule=0,
                ring_id=rid, role=ROLE_CASHOUT,
                typologies=[T.TYP_DEVICE, T.TYP_PASS], seed=cseed,
            )

    # ---- hard negatives (clean high-velocity) ----
    for h, aid in enumerate(hardneg_ids):
        hseed = seed + 9000 + h
        hrng = np.random.default_rng(hseed)
        is_merchant = aid in hardneg_current
        accounts[aid] = AccountProfile(
            account_id=aid,
            account_type="current" if is_merchant else "savings",
            open_date=AS_OF - timedelta(days=int(hrng.integers(200, 1800))),
            kyc_income_band=str(hrng.choice(("25k-50k", "50k-1L", "1L-3L"))),
            linked_entity_id=next(ent_iter) if is_merchant else None,
            activity_level="high", home_device_id=f"DEV-{aid}", is_mule=0,
            ring_id=None, role=ROLE_HARDNEG, is_hard_negative=1,
            typologies=["high_velocity"],  # benign marker, NOT one of the 8
            seed=hseed,
        )

    # ---- ordinary legit accounts ----
    for li, aid in enumerate(legit_ids):
        lseed = seed + 20000 + li
        lrng = np.random.default_rng(lseed)
        is_current = aid in current_legit
        activity = str(lrng.choice(ACTIVITY_LEVELS, p=(0.35, 0.45, 0.20)))
        if is_current:
            band = str(lrng.choice(("50k-1L", "1L-3L", "3L+"), p=(0.35, 0.45, 0.20)))
        else:
            band = str(lrng.choice(INCOME_BANDS, p=(0.20, 0.35, 0.28, 0.13, 0.04)))
        accounts[aid] = AccountProfile(
            account_id=aid, account_type="current" if is_current else "savings",
            open_date=AS_OF - timedelta(days=int(lrng.integers(120, 3000))),
            kyc_income_band=band,
            linked_entity_id=next(ent_iter) if is_current else None,
            activity_level=activity, home_device_id=f"DEV-{aid}",
            is_mule=0, ring_id=None, role=ROLE_LEGIT, seed=lseed,
        )

    return accounts, rings
