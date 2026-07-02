"""Core-source generators (Appendix A §2, Appendix B §2.2) — full spec.

Sources: GST, Account-Aggregator bank, UPI, EPFO, Credit Bureau, Udyam,
PAN/GSTIN verification, E-way bill.

Design note (the differentiator): GST rows are built from the entity's
*declared* turnover, while bank/UPI/e-way-bill volumes follow its *true* scale.
For a 'genuine' entity declared == true (within noise) so everything agrees; for
an 'inflated' entity declared >> true, so the Turnover-Authenticity composite
(GST vs bank vs e-way-bill) correctly flags the gap.
"""
from __future__ import annotations

import numpy as np

from ..distributions import GST_HISTORY_MONTHS, BANK_HISTORY_MONTHS
from ..profiles import MSMEProfile
from .base import register

_MONTHS = [f"2025-{m:02d}" for m in range(1, 13)] + [f"2026-{m:02d}" for m in range(1, 7)]
_MONTHS = _MONTHS[-GST_HISTORY_MONTHS:]

# Seasonality index (Indian festive Q3/Q4 uplift), length 12 by calendar month.
_SEASON = {1: 0.95, 2: 0.92, 3: 1.05, 4: 0.98, 5: 0.97, 6: 0.95,
           7: 0.98, 8: 1.02, 9: 1.06, 10: 1.15, 11: 1.12, 12: 1.03}

_HEALTH_TREND = {"healthy": 0.010, "stressed": -0.004, "distressed": -0.020}  # monthly
_HEALTH_VOL = {"healthy": 0.06, "stressed": 0.12, "distressed": 0.20}
_LATE_FILING_P = {"healthy": 0.05, "stressed": 0.25, "distressed": 0.55}


def _monthly_series(profile: MSMEProfile, annual: float, salt: int) -> np.ndarray:
    """A trended, seasonal, noisy monthly series summing ~to `annual`."""
    rng = profile.rng(salt)
    base = annual / len(_MONTHS)
    trend = _HEALTH_TREND[profile.true_health]
    vol = _HEALTH_VOL[profile.true_health]
    out = []
    for i, ym in enumerate(_MONTHS):
        month = int(ym.split("-")[1])
        val = base * ((1 + trend) ** i) * _SEASON[month] * (1 + rng.normal(0, vol))
        out.append(max(val, 0.0))
    return np.array(out)


# --------------------------------------------------------------------------- GST
@register("gst", tier="core", columns=[
    "entity_id", "month", "turnover", "taxable_turnover", "exempted_turnover",
    "tax_liability", "igst", "cgst", "sgst", "itc_availed", "credit_notes",
    "filing_days_late", "hsn_sac_code", "num_customers"])
def gen_gst(profile: MSMEProfile):
    if not profile.gst_registered:
        return []  # legally exempt — no GST footprint (a real thin-file case)
    rng = profile.rng(11)
    series = _monthly_series(profile, profile.declared_turnover, salt=11)
    interstate = 0.45 if profile.exports or profile.sector == "Manufacturing" else 0.20
    exempt_share = 0.15 if profile.sector == "Services" else 0.05
    # customer concentration: fewer customers for services / small
    base_customers = max(3, int(profile.true_scale_turnover / 2_000_000))
    rows = []
    for ym, t in zip(_MONTHS, series):
        taxable = t * (1 - exempt_share)
        tax = taxable * 0.12
        igst = tax * interstate
        cgst = sgst = tax * (1 - interstate) / 2
        # ITC/tax-paid ratio: higher (worse) for stressed/thin-margin
        itc_ratio = {"healthy": 0.55, "stressed": 0.72, "distressed": 0.85}[profile.true_health]
        itc = tax * itc_ratio * (1 + rng.normal(0, 0.05))
        credit_notes = t * rng.uniform(0.005, 0.03) * (2.5 if profile.true_health == "distressed" else 1.0)
        late = int(rng.random() < _LATE_FILING_P[profile.true_health]) * int(rng.integers(1, 25))
        rows.append(dict(
            month=ym, turnover=round(t, 2), taxable_turnover=round(taxable, 2),
            exempted_turnover=round(t * exempt_share, 2), tax_liability=round(tax, 2),
            igst=round(igst, 2), cgst=round(cgst, 2), sgst=round(sgst, 2),
            itc_availed=round(itc, 2), credit_notes=round(credit_notes, 2),
            filing_days_late=int(late),
            hsn_sac_code=_hsn_for_sector(profile.sector, rng),
            num_customers=int(max(1, base_customers + rng.integers(-2, 3))),
        ))
    return rows


def _hsn_for_sector(sector: str, rng) -> str:
    pool = {
        "Manufacturing": ["5208", "7308", "8708", "6203"],
        "Trade": ["1006", "2106", "3004", "8517"],
        "Services": ["9983", "9985", "9971", "9967"],
    }[sector]
    return str(rng.choice(pool))


# ---------------------------------------------------------------- AA bank/deposit
@register("bank", tier="core", columns=[
    "entity_id", "month", "avg_balance", "min_balance", "total_inflow",
    "total_outflow", "bounce_count", "od_utilization", "emi_debits"])
def gen_bank(profile: MSMEProfile):
    rng = profile.rng(21)
    # Bank inflows track TRUE scale (real settled money), not declared turnover.
    inflow_series = _monthly_series(profile, profile.true_scale_turnover * 0.85, salt=21)
    bal_level = profile.true_scale_turnover / 12 * {"healthy": 0.9, "stressed": 0.35, "distressed": 0.12}[profile.true_health]
    bounce_p = {"healthy": 0.03, "stressed": 0.20, "distressed": 0.5}[profile.true_health]
    has_emi = profile.true_scale_turnover > 3_000_000 and rng.random() < 0.6
    rows = []
    for ym, inflow in zip(_MONTHS, inflow_series):
        vol = _HEALTH_VOL[profile.true_health]
        avg_bal = max(0, bal_level * (1 + rng.normal(0, vol)))
        min_bal = avg_bal * rng.uniform(0.1, 0.6) - (avg_bal * 0.3 if profile.true_health == "distressed" else 0)
        outflow = inflow * rng.uniform(0.88, 1.05)
        emi = inflow * rng.uniform(0.05, 0.15) if has_emi else 0.0
        rows.append(dict(
            month=ym, avg_balance=round(avg_bal, 2), min_balance=round(min_bal, 2),
            total_inflow=round(inflow, 2), total_outflow=round(outflow, 2),
            bounce_count=int(rng.random() < bounce_p) * int(rng.integers(1, 4)),
            od_utilization=round(float(np.clip(rng.normal(
                {"healthy": 0.3, "stressed": 0.7, "distressed": 0.95}[profile.true_health], 0.1), 0, 1)), 3),
            emi_debits=round(emi, 2),
        ))
    return rows


# ------------------------------------------------------------------------- UPI
@register("upi", tier="core", columns=[
    "entity_id", "month", "p2m_count", "p2p_count", "total_receipts",
    "unique_counterparties", "refund_count"])
def gen_upi(profile: MSMEProfile):
    if not profile.digital_adoption:
        return []
    rng = profile.rng(31)
    # UPI receipts follow true scale too; retail/trade skew digital-heavy.
    digital_share = {"Trade": 0.55, "Services": 0.4, "Manufacturing": 0.2}[profile.sector]
    receipts_series = _monthly_series(profile, profile.true_scale_turnover * digital_share, salt=31)
    rows = []
    for ym, rec in zip(_MONTHS, receipts_series):
        n = max(1, int(rec / 800))  # ~ avg ticket 800
        rows.append(dict(
            month=ym, p2m_count=int(n * 0.8), p2p_count=int(n * 0.2),
            total_receipts=round(rec, 2),
            unique_counterparties=int(max(1, n * rng.uniform(0.3, 0.7))),
            refund_count=int(n * rng.uniform(0.0, 0.03)),
        ))
    return rows


# ------------------------------------------------------------------------ EPFO
@register("epfo", tier="core", columns=[
    "entity_id", "month", "headcount", "wage_bill", "ee_contribution",
    "er_contribution", "arrears_flag"])
def gen_epfo(profile: MSMEProfile):
    if profile.employees < 1:
        return []  # OAE / no formal employees -> not on EPFO
    rng = profile.rng(41)
    base_hc = profile.employees
    arrears_p = {"healthy": 0.02, "stressed": 0.18, "distressed": 0.5}[profile.true_health]
    avg_wage = 15000 * rng.uniform(0.9, 1.6)  # around EPS ceiling
    rows = []
    for i, ym in enumerate(_MONTHS):
        drift = {"healthy": 0.004, "stressed": -0.003, "distressed": -0.015}[profile.true_health]
        hc = max(1, int(round(base_hc * ((1 + drift) ** i) * (1 + rng.normal(0, 0.05)))))
        wage_bill = hc * avg_wage
        pf_wage = min(avg_wage, 15000) * hc
        rows.append(dict(
            month=ym, headcount=hc, wage_bill=round(wage_bill, 2),
            ee_contribution=round(pf_wage * 0.12, 2),
            er_contribution=round(pf_wage * (0.0833 + 0.0367), 2),
            arrears_flag=int(rng.random() < arrears_p),
        ))
    return rows


# ---------------------------------------------------------------------- Bureau
@register("bureau", tier="core", columns=[
    "entity_id", "has_bureau_record", "num_active_loans", "total_exposure",
    "max_dpd_12m", "num_enquiries_6m", "oldest_tradeline_months", "msme_rank"])
def gen_bureau(profile: MSMEProfile):
    rng = profile.rng(51)
    # NTC entities (young, no formal credit) frequently have no bureau record.
    has_record = not (profile.age_years < 3 and rng.random() < 0.6)
    if not has_record:
        return [dict(has_bureau_record=0, num_active_loans=0, total_exposure=0.0,
                     max_dpd_12m=0, num_enquiries_6m=int(rng.integers(0, 3)),
                     oldest_tradeline_months=0, msme_rank=0)]
    dpd = {"healthy": rng.integers(0, 15), "stressed": rng.integers(15, 60),
           "distressed": rng.integers(60, 180)}[profile.true_health]
    n_loans = int(rng.integers(1, 5))
    return [dict(
        has_bureau_record=1, num_active_loans=n_loans,
        total_exposure=round(profile.true_scale_turnover * rng.uniform(0.1, 0.5), 2),
        max_dpd_12m=int(dpd), num_enquiries_6m=int(rng.integers(0, 6)),
        oldest_tradeline_months=int(profile.age_years * 12 * rng.uniform(0.4, 0.9)),
        msme_rank=int({"healthy": rng.integers(1, 4), "stressed": rng.integers(4, 7),
                       "distressed": rng.integers(7, 11)}[profile.true_health]),
    )]


# ----------------------------------------------------------------------- Udyam
@register("udyam", tier="core", columns=[
    "entity_id", "urn", "category", "nic_code", "sector", "registration_date",
    "state", "declared_investment", "declared_turnover"])
def gen_udyam(profile: MSMEProfile):
    rng = profile.rng(61)
    reg_year = 2026 - int(profile.age_years)
    return [dict(
        urn=f"UDYAM-{profile.state[:2].upper()}-{rng.integers(10,99):02d}-{rng.integers(1000000,9999999)}",
        category=profile.category, nic_code=str(rng.integers(10000, 99999)),
        sector=profile.sector, registration_date=f"{max(reg_year,2020)}-{rng.integers(1,13):02d}-01",
        state=profile.state,
        declared_investment=round(profile.true_scale_turnover * rng.uniform(0.15, 0.5), 2),
        declared_turnover=round(profile.declared_turnover, 2),
    )]


# ------------------------------------------------------------ PAN/GSTIN verify
@register("pan_gstin", tier="core", columns=[
    "entity_id", "pan_status", "gstin_status", "name_match_score"])
def gen_pan_gstin(profile: MSMEProfile):
    rng = profile.rng(71)
    gstin_status = "active"
    if profile.gst_registered and profile.true_health == "distressed" and rng.random() < 0.15:
        gstin_status = "suspended"
    if not profile.gst_registered:
        gstin_status = "not_registered"
    return [dict(
        pan_status="active",
        gstin_status=gstin_status,
        name_match_score=round(float(np.clip(rng.normal(0.95, 0.05), 0, 1)), 3),
    )]


# -------------------------------------------------------------------- E-way bill
@register("ewaybill", tier="core", columns=[
    "entity_id", "month", "ewb_count", "ewb_value", "avg_distance_km", "hsn_code"])
def gen_ewaybill(profile: MSMEProfile):
    # Services rarely move goods; e-way bills apply to goods movement.
    if profile.sector == "Services":
        return []
    rng = profile.rng(81)
    # EWB value tracks TRUE goods movement (real scale), not declared turnover.
    ewb_series = _monthly_series(profile, profile.true_scale_turnover * 0.9, salt=81)
    rows = []
    for ym, val in zip(_MONTHS, ewb_series):
        cnt = max(0, int(val / 50_000))
        rows.append(dict(
            month=ym, ewb_count=cnt, ewb_value=round(val, 2),
            avg_distance_km=round(float(rng.uniform(20, 600)), 1),
            hsn_code=_hsn_for_sector(profile.sector, rng),
        ))
    return rows
