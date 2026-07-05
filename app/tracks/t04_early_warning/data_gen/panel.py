"""Loan-book & monthly-panel synthesis for Track 04 (WP-4D spec §"Design").

Latent-driven, same philosophy as `app.data_gen.profiles`: a hidden monthly
`health_t` trajectory drives every observable, so alt-data and repayment series
for one borrower are mutually consistent rather than independently noisy.

The thesis (encode in data, measure in eval, show in UI):
    alt-data responds to `health_t` immediately;
    repayment responds to `health_{t-Δ}` with Δ ~ 5-9 months,
so DPD/bounces only materialise several months *after* GST/UPI/EPFO have sagged.

Determinism: every draw derives from the borrower's `MSMEProfile.seed` (which is
itself pinned by the project base seed), so a given seed → byte-identical CSVs.
"""
from __future__ import annotations

import zlib
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from app.data_gen.build_dataset import build_profiles
from app.data_gen.profiles import MSMEProfile

# --------------------------------------------------------------------------- #
# Locked design parameters (WP-4D §Design).
# --------------------------------------------------------------------------- #
BASE_SEED = 20260701          # matches app.data_gen default → shared cohort
N_RANDOM = 400                # matches app.data_gen default → identical entities
PANEL_MONTHS = 24             # months indexed -23..0 relative to "today" (=0)
MONTHS: List[int] = list(range(-(PANEL_MONTHS - 1), 1))   # [-23 .. 0]

LOAN_SHARE = 0.60             # ~60% of the cohort carries an existing loan
DEFAULTER_SHARE = 0.14        # bottom ~14% by true_health become defaulters
OBSERVED_SHARE = 0.38         # ~1/3 of defaults fall inside the panel (eval)

# Health-model constants.
_FLOOR = 0.05                 # health floor at full collapse
_RAMP_POW = 1.5               # ramp steepens over time (convex decline)
# Pre-deterioration operating health by latent health state (+ jitter).
_BASE_HEALTH = {"healthy": 0.82, "stressed": 0.62, "distressed": 0.50}
# Health value used only to RANK borrowers for defaulter selection.
_RANK_HEALTH = {"healthy": 0.80, "stressed": 0.45, "distressed": 0.15}

# DPD model: repayment stress kicks in below _DPD_THRESHOLD on *lagged* health.
_DPD_THRESHOLD = 0.35
_DPD_GAIN = 600.0             # dpd = (thr - repay_health) * gain  (→90 at ~0.20)
_DPD_MAX = 180

# Alt-data filing-discipline: P(on-time GST filing) falls with health.
_ONTIME_AT_FULL = 0.97
_ONTIME_AT_FLOOR = 0.25

_PRODUCTS = ("term", "cc", "od")

# CSV schemas (authoritative — tests and WP-4M read these).
SCHEMAS: Dict[str, List[str]] = {
    "loan_book": [
        "entity_id", "loan_id", "product", "sanction_month", "tenor_months",
        "sanctioned_limit", "interest_rate", "status",
    ],
    "repayment_history": [
        "entity_id", "month", "emi_due", "emi_paid", "dpd", "bounce_flag",
        "utilization_pct", "overdue_amount",
    ],
    "altdata_monthly": [
        "entity_id", "month", "gst_turnover_declared", "gst_filed_on_time",
        "bank_inflows", "upi_txn_count", "epfo_employee_count", "energy_units",
    ],
    "default_labels": [
        "entity_id", "loan_id", "is_defaulter", "default_observed",
        "default_month", "ramp_start_month", "lead_alt", "repay_lag",
    ],
}

# Flagship (healthy, non-defaulter) + deteriorating showcase (demo star). These
# archetype entity_ids are pinned so the demo/tests always find their story.
FLAGSHIP_ENTITY = "TEXTILE_MANUFACTURER"
SHOWCASE_ENTITY = "AUTO_COMPONENTS"


# --------------------------------------------------------------------------- #
# Per-borrower loan account (derived latent trajectory + loan terms).
# --------------------------------------------------------------------------- #
@dataclass
class LoanAccount:
    profile: MSMEProfile
    loan_id: str
    product: str
    sanction_month: int
    tenor_months: int
    sanctioned_limit: float
    interest_rate: float
    # trajectory params
    health_base: float
    is_defaulter: bool
    ramp_start: Optional[int]      # month the deterioration ramp begins
    lead_alt: Optional[int]        # ramp length (months, U(8,14))
    repay_lag: Optional[int]       # Δ, repayment lags health by this many months
    # derived after simulation
    default_month: Optional[int] = None       # first month DPD>=90 (None=live/none)
    default_observed: bool = False            # DPD>=90 seen inside the panel

    def health_at(self, t: int) -> float:
        """Latent health at panel month `t` (clamped to [_FLOOR, ~base])."""
        base = self.health_base
        if not self.is_defaulter or self.ramp_start is None:
            # Non-defaulters: stable operating health with mild seasonal wobble.
            rng = self.profile.rng(1207)
            wob = 0.04 * np.sin((t + 6) * 0.9) + rng.normal(0, 0.015)
            return float(np.clip(base + wob, _FLOOR, 1.15))
        # Defaulters: convex ramp from base → floor over `lead_alt` months.
        q = np.clip((t - self.ramp_start) / max(self.lead_alt, 1), 0.0, 1.0) ** _RAMP_POW
        return float(np.clip(base - (base - _FLOOR) * q, _FLOOR, 1.15))

    def repay_health_at(self, t: int) -> float:
        """Health the repayment channel 'sees' — lagged by Δ (`repay_lag`)."""
        lag = self.repay_lag or 0
        return self.health_at(t - lag)


# --------------------------------------------------------------------------- #
# Cohort selection & account construction.
# --------------------------------------------------------------------------- #
def _has_loan(profile: MSMEProfile) -> bool:
    """Deterministic ~60% selection by stable hash of entity_id (crc32 — the
    builtin `hash()` is PYTHONHASHSEED-salted and would break determinism)."""
    seed = zlib.crc32(("t04-loan:" + profile.entity_id).encode()) & 0xFFFFFFFF
    return bool(np.random.default_rng(seed).random() < LOAN_SHARE)


def _rank_score(profile: MSMEProfile) -> float:
    """Continuous health proxy for defaulter ranking (lower = weaker)."""
    rng = profile.rng(1301)
    return _RANK_HEALTH[profile.true_health] + float(rng.uniform(-0.10, 0.10))


def _build_account(profile: MSMEProfile, is_defaulter: bool) -> LoanAccount:
    rng = profile.rng(1401)
    scale = profile.true_scale_turnover

    # Product mix by sector (services skew OD/CC; goods skew term/CC).
    if profile.sector == "Services":
        product = str(rng.choice(_PRODUCTS, p=[0.30, 0.35, 0.35]))
    else:
        product = str(rng.choice(_PRODUCTS, p=[0.50, 0.35, 0.15]))

    sanctioned_limit = round(scale * float(rng.uniform(0.18, 0.45)), 2)
    interest_rate = round(float(rng.uniform(9.5, 16.5)), 2)
    tenor_months = int(rng.choice([36, 48, 60, 84])) if product == "term" else 12
    sanction_month = int(rng.integers(-48, -6))

    # Pre-deterioration operating health.
    if is_defaulter:
        # Marginal-but-performing before the ramp, regardless of latent class.
        health_base = float(rng.uniform(0.52, 0.72))
        # ~1/3 observed (ramp early → default inside panel), ~2/3 live watchlist.
        if rng.random() < OBSERVED_SHARE:
            # Early, brisk ramp so DPD>=90 lands inside the panel.
            ramp_start = int(rng.integers(-23, -15))     # observed
            lead_alt = int(rng.integers(8, 13))          # U(8,12)
            repay_lag = int(rng.integers(5, 9))          # Δ ~ U(5,8)
        else:
            # Later ramp: alt-data already sagging, DPD>=90 lies beyond month 0.
            ramp_start = int(rng.integers(-10, -1))      # live-deteriorating
            lead_alt = int(rng.integers(9, 15))          # U(9,14)
            repay_lag = int(rng.integers(6, 10))         # Δ ~ U(6,9)
    else:
        health_base = float(np.clip(
            _BASE_HEALTH[profile.true_health] + rng.uniform(-0.05, 0.05), 0.42, 1.0))
        ramp_start = lead_alt = repay_lag = None

    return LoanAccount(
        profile=profile, loan_id=f"LN-{profile.entity_id}", product=product,
        sanction_month=sanction_month, tenor_months=tenor_months,
        sanctioned_limit=sanctioned_limit, interest_rate=interest_rate,
        health_base=health_base, is_defaulter=is_defaulter,
        ramp_start=ramp_start, lead_alt=lead_alt, repay_lag=repay_lag,
    )


def build_accounts(profiles: List[MSMEProfile]) -> List[LoanAccount]:
    """Select the ~60% loan book, mark the bottom ~14% as defaulters, and pin
    the deteriorating showcase archetype into the defaulter set."""
    book = [p for p in profiles if _has_loan(p)]
    # Guarantee both demo stars are in the book.
    have = {p.entity_id for p in book}
    for p in profiles:
        if p.entity_id in (FLAGSHIP_ENTITY, SHOWCASE_ENTITY) and p.entity_id not in have:
            book.append(p)
            have.add(p.entity_id)

    n_def = int(round(len(book) * DEFAULTER_SHARE))
    ranked = sorted(book, key=_rank_score)
    default_ids = {p.entity_id for p in ranked[:n_def]}
    # Showcase is always a (live-deteriorating) defaulter; flagship never is.
    default_ids.add(SHOWCASE_ENTITY)
    default_ids.discard(FLAGSHIP_ENTITY)

    accounts = [_build_account(p, p.entity_id in default_ids) for p in book]

    # Force the showcase to be a *live* deteriorating account (the money-shot
    # watchlist case: alt-data clearly sagging, not yet in NPA).
    for a in accounts:
        if a.profile.entity_id == SHOWCASE_ENTITY:
            a.ramp_start, a.lead_alt, a.repay_lag = -9, 12, 7
            a.health_base = 0.68
    return accounts


# --------------------------------------------------------------------------- #
# Row emission.
# --------------------------------------------------------------------------- #
def _simulate_repayment(acc: LoanAccount) -> List[dict]:
    """Emit the 24-month repayment panel and populate default_month/observed."""
    rng = acc.profile.rng(1501)
    limit = acc.sanctioned_limit
    if acc.product == "term":
        base_emi = limit * (acc.interest_rate / 100 / 12 + 1.0 / max(acc.tenor_months, 12))
    else:
        base_emi = limit * (acc.interest_rate / 100 / 12)   # revolving interest service

    overdue = 0.0
    rows: List[dict] = []
    for t in MONTHS:
        rh = acc.repay_health_at(t)
        dpd = int(np.clip(round((_DPD_THRESHOLD - rh) * _DPD_GAIN), 0, _DPD_MAX))
        # Utilisation (CC/OD only): rises as health falls; term loans → NaN.
        if acc.product in ("cc", "od"):
            util = float(np.clip(1.10 - acc.health_at(t) + rng.normal(0, 0.03), 0.05, 1.0))
            util_pct = round(util * 100, 1)
            emi_due = round(limit * util * (acc.interest_rate / 100 / 12), 2)
        else:
            util_pct = np.nan
            emi_due = round(base_emi, 2)

        pay_frac = float(np.clip(1.0 - dpd / 90.0, 0.0, 1.0))
        emi_paid = round(emi_due * pay_frac, 2)
        bounce = int(emi_paid < emi_due - 1e-6)
        overdue = max(0.0, overdue + (emi_due - emi_paid))
        rows.append(dict(
            entity_id=acc.profile.entity_id, month=t, emi_due=emi_due,
            emi_paid=emi_paid, dpd=dpd, bounce_flag=bounce,
            utilization_pct=util_pct, overdue_amount=round(overdue, 2),
        ))
        if dpd >= 90 and acc.default_month is None:
            acc.default_month = t
            acc.default_observed = True

    # Live-deteriorating defaulters: DPD>=90 lies just beyond the panel — record
    # the (future) event month so WP-4M can build within-12m labels, but mark it
    # unobserved (status stays 'watch', not 'npa').
    if acc.is_defaulter and acc.default_month is None:
        acc.default_month = _project_default_month(acc)
    return rows


def _project_default_month(acc: LoanAccount) -> Optional[int]:
    """Extrapolate the first future month DPD would reach 90 (beyond month 0)."""
    for t in range(1, 25):
        rh = acc.repay_health_at(t)
        if (_DPD_THRESHOLD - rh) * _DPD_GAIN >= 90:
            return t
    return None


def _emit_altdata(acc: LoanAccount) -> List[dict]:
    """Alt-data footprint driven by `health_t` (immediate, unlagged)."""
    p = acc.profile
    rng = p.rng(1601)
    gst_monthly = p.declared_turnover / 12.0
    inflow_monthly = p.true_scale_turnover * 0.85 / 12.0
    digital_share = {"Trade": 0.55, "Services": 0.40, "Manufacturing": 0.20}[p.sector]
    upi_base = max(1.0, p.true_scale_turnover * digital_share / 12.0 / 800.0)
    energy_base = max(50.0, p.true_scale_turnover / 12.0 / 400.0)
    hc_base = max(1, p.employees)
    # Seasonal index by panel-month position (festive uplift), length-12 cycle.
    season = {i: s for i, s in enumerate(
        [0.95, 0.92, 1.05, 0.98, 0.97, 0.95, 0.98, 1.02, 1.06, 1.15, 1.12, 1.03])}

    rows: List[dict] = []
    for t in MONTHS:
        h = acc.health_at(t)
        rel = float(np.clip(h / acc.health_base, 0.05, 1.15))   # =1 at operating level
        s = season[t % 12]
        gst = max(0.0, gst_monthly * s * rel * (1 + rng.normal(0, 0.05)))
        inflow = max(0.0, inflow_monthly * s * rel * (1 + rng.normal(0, 0.06)))
        upi = int(max(0, round(upi_base * rel * (1 + rng.normal(0, 0.05)))))
        headcount = int(max(0, round(hc_base * np.clip(rel, 0.0, 1.05))))
        energy = round(max(0.0, energy_base * s * (0.5 + 0.5 * rel) * (1 + rng.normal(0, 0.04))), 1)
        p_ontime = _ONTIME_AT_FLOOR + (_ONTIME_AT_FULL - _ONTIME_AT_FLOOR) * float(np.clip(rel, 0, 1))
        filed_on_time = int(rng.random() < p_ontime) if p.gst_registered else 0
        rows.append(dict(
            entity_id=p.entity_id, month=t,
            gst_turnover_declared=round(gst, 2),
            gst_filed_on_time=filed_on_time,
            bank_inflows=round(inflow, 2),
            upi_txn_count=upi,
            epfo_employee_count=headcount,
            energy_units=energy,
        ))
    return rows


def _loan_row(acc: LoanAccount) -> dict:
    if acc.default_observed:
        status = "npa"
    elif acc.is_defaulter:
        status = "watch"
    else:
        # A few healthy accounts are fully repaid/closed within the panel.
        status = "closed" if acc.profile.rng(1701).random() < 0.04 else "regular"
    return dict(
        entity_id=acc.profile.entity_id, loan_id=acc.loan_id, product=acc.product,
        sanction_month=acc.sanction_month, tenor_months=acc.tenor_months,
        sanctioned_limit=acc.sanctioned_limit, interest_rate=acc.interest_rate,
        status=status,
    )


def _label_row(acc: LoanAccount) -> dict:
    return dict(
        entity_id=acc.profile.entity_id, loan_id=acc.loan_id,
        is_defaulter=int(acc.is_defaulter),
        default_observed=int(acc.default_observed),
        default_month=acc.default_month if acc.default_month is not None else "",
        ramp_start_month=acc.ramp_start if acc.ramp_start is not None else "",
        lead_alt=acc.lead_alt if acc.lead_alt is not None else "",
        repay_lag=acc.repay_lag if acc.repay_lag is not None else "",
    )


def generate_tables(profiles: List[MSMEProfile]) -> Dict[str, list]:
    """Return {csv_name: list-of-row-dicts} for all four outputs."""
    accounts = build_accounts(profiles)
    repay: List[dict] = []
    altdata: List[dict] = []
    for acc in accounts:
        repay.extend(_simulate_repayment(acc))   # sets default_month/observed
        altdata.extend(_emit_altdata(acc))
    loan_book = [_loan_row(a) for a in accounts]   # after simulation → status set
    labels = [_label_row(a) for a in accounts]
    return {
        "loan_book": loan_book,
        "repayment_history": repay,
        "altdata_monthly": altdata,
        "default_labels": labels,
    }
