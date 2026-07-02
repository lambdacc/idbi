"""Enrichment-source generators (Appendix A §3, Appendix B §2.3) — compact spec.

All conditioned on the same latents as the core sources so composites are real:
e.g. electricity consumption and factory-licence sanctioned load both scale with
`true_scale_turnover`, and property-tax address matches GST address unless the
entity is an 'inflated'/shell profile.
"""
from __future__ import annotations

import numpy as np

from ..profiles import MSMEProfile
from .base import register

_MONTHS = [f"2025-{m:02d}" for m in range(7, 13)] + [f"2026-{m:02d}" for m in range(1, 7)]


# ------------------------------------------------------------------- MCA21
@register("mca21", columns=[
    "entity_id", "has_mca_record", "cin", "incorporation_date", "num_directors",
    "num_charges", "director_disqualified"])
def gen_mca21(profile: MSMEProfile):
    if not profile.incorporated:
        return [dict(has_mca_record=0, cin="", incorporation_date="",
                     num_directors=0, num_charges=0, director_disqualified=0)]
    rng = profile.rng(101)
    return [dict(
        has_mca_record=1, cin=f"U{rng.integers(10000,99999)}{profile.state[:2].upper()}{2026-int(profile.age_years)}PTC{rng.integers(100000,999999)}",
        incorporation_date=f"{max(2026-int(profile.age_years),2005)}-01-01",
        num_directors=int(rng.integers(2, 6)),
        num_charges=int(rng.integers(0, 4)) if profile.true_scale_turnover > 5_000_000 else 0,
        director_disqualified=int(profile.true_health == "distressed" and rng.random() < 0.1),
    )]


# --------------------------------------------------------------------- ITR/AIS
@register("itr", columns=[
    "entity_id", "assessment_year", "reported_income", "tds_credits", "filed_on_time"])
def gen_itr(profile: MSMEProfile):
    rng = profile.rng(111)
    # Reported income conditioned on TRUE turnover; inflated profiles under-report
    # income relative to their declared GST turnover -> ITR-vs-GST mismatch.
    margin = {"healthy": 0.12, "stressed": 0.05, "distressed": 0.01}[profile.true_health]
    income = profile.true_scale_turnover * margin
    return [dict(
        assessment_year="2025-26", reported_income=round(max(income, 0), 2),
        tds_credits=round(income * rng.uniform(0.05, 0.15), 2),
        filed_on_time=int(rng.random() > {"healthy": 0.05, "stressed": 0.3, "distressed": 0.6}[profile.true_health]),
    )]


# -------------------------------------------------------------------- FASTag
@register("fastag", columns=[
    "entity_id", "month", "toll_crossings", "unique_routes"])
def gen_fastag(profile: MSMEProfile):
    if profile.sector == "Services" and profile.archetype != "logistics":
        return []
    rng = profile.rng(121)
    base = int(profile.true_scale_turnover / 500_000)
    if base <= 0:
        return []
    return [dict(month=m, toll_crossings=int(max(0, base * rng.uniform(0.7, 1.3))),
                 unique_routes=int(max(1, base * rng.uniform(0.2, 0.5)))) for m in _MONTHS]


# --------------------------------------------------------------------- Vahan
@register("vahan", columns=[
    "entity_id", "num_vehicles", "avg_vehicle_age_years", "commercial_class",
    "fitness_valid"])
def gen_vahan(profile: MSMEProfile):
    if profile.sector == "Services" and profile.archetype not in ("logistics",):
        return [dict(num_vehicles=0, avg_vehicle_age_years=0.0, commercial_class="", fitness_valid=1)]
    rng = profile.rng(131)
    n = int(max(0, profile.true_scale_turnover / 3_000_000 * rng.uniform(0.5, 1.5)))
    return [dict(num_vehicles=n, avg_vehicle_age_years=round(float(rng.uniform(1, 12)), 1),
                 commercial_class="LGV" if n else "",
                 fitness_valid=int(rng.random() > (0.3 if profile.true_health == "distressed" else 0.05)))]


# ---------------------------------------------------------------- DGFT/ICEGATE
@register("dgft", columns=[
    "entity_id", "has_iec", "iec_status", "shipping_bill_count", "export_value"])
def gen_dgft(profile: MSMEProfile):
    if not profile.exports:
        return [dict(has_iec=0, iec_status="", shipping_bill_count=0, export_value=0.0)]
    rng = profile.rng(141)
    return [dict(has_iec=1, iec_status="active",
                 shipping_bill_count=int(rng.integers(4, 60)),
                 export_value=round(profile.true_scale_turnover * rng.uniform(0.2, 0.7), 2))]


# ----------------------------------------------------------------- Electricity
@register("electricity", columns=[
    "entity_id", "month", "sanctioned_load_kw", "consumption_kwh", "bill_paid_on_time"])
def gen_electricity(profile: MSMEProfile):
    if not profile.has_physical_premises:
        return []
    rng = profile.rng(151)
    # kWh scales with TRUE scale and sector energy-intensity (mfg >> services).
    intensity = {"Manufacturing": 1.0, "Trade": 0.25, "Services": 0.12}[profile.sector]
    monthly_kwh = profile.true_scale_turnover / 12 / 40 * intensity  # ~ INR40/kWh output
    sanctioned = max(5.0, monthly_kwh / 400 * rng.uniform(0.9, 1.3))
    late_p = {"healthy": 0.03, "stressed": 0.2, "distressed": 0.5}[profile.true_health]
    return [dict(month=m, sanctioned_load_kw=round(sanctioned, 1),
                 consumption_kwh=round(max(0, monthly_kwh * (1 + rng.normal(0, 0.1))), 1),
                 bill_paid_on_time=int(rng.random() > late_p)) for m in _MONTHS]


# --------------------------------------------------------------- Property tax
@register("property_tax", columns=[
    "entity_id", "has_record", "assessed_value", "address_matches_gst",
    "tax_paid_current"])
def gen_property_tax(profile: MSMEProfile):
    if not profile.has_physical_premises:
        return [dict(has_record=0, assessed_value=0.0, address_matches_gst=0, tax_paid_current=1)]
    rng = profile.rng(161)
    # Shell/inflated premises: address fails to corroborate GST registration.
    addr_match = int(not (profile.true_honesty == "inflated" and rng.random() < 0.6))
    return [dict(has_record=1,
                 assessed_value=round(profile.true_scale_turnover * rng.uniform(0.2, 0.8), 2),
                 address_matches_gst=addr_match,
                 tax_paid_current=int(rng.random() > (0.3 if profile.true_health == "distressed" else 0.05)))]


# --------------------------------------------------------------------- FSSAI
@register("fssai", columns=["entity_id", "has_licence", "licence_tier", "valid"])
def gen_fssai(profile: MSMEProfile):
    is_food = profile.archetype in ("restaurant",) or (profile.sector != "Manufacturing" and profile.rng(171).random() < 0.15)
    if not is_food:
        return [dict(has_licence=0, licence_tier="", valid=0)]
    rng = profile.rng(171)
    tier = "central" if profile.true_scale_turnover > 200_000_000 else ("state" if profile.true_scale_turnover > 1_200_000 else "basic")
    return [dict(has_licence=1, licence_tier=tier, valid=int(rng.random() > 0.05))]


# ------------------------------------------------------------- Factory licence
@register("factory_licence", columns=[
    "entity_id", "has_licence", "sanctioned_workers", "sanctioned_power_hp", "valid"])
def gen_factory_licence(profile: MSMEProfile):
    if profile.sector != "Manufacturing":
        return [dict(has_licence=0, sanctioned_workers=0, sanctioned_power_hp=0.0, valid=0)]
    rng = profile.rng(181)
    return [dict(has_licence=1,
                 sanctioned_workers=int(max(profile.employees, profile.true_scale_turnover / 1_000_000 * rng.uniform(0.8, 1.4))),
                 sanctioned_power_hp=round(profile.true_scale_turnover / 500_000 * rng.uniform(0.7, 1.3), 1),
                 valid=int(rng.random() > 0.05))]


# --------------------------------------------------------- Pollution control
@register("pollution", columns=["entity_id", "has_consent", "category", "valid"])
def gen_pollution(profile: MSMEProfile):
    if profile.sector != "Manufacturing":
        return [dict(has_consent=0, category="", valid=0)]
    rng = profile.rng(191)
    cat = str(rng.choice(["Red", "Orange", "Green", "White"], p=[0.15, 0.3, 0.4, 0.15]))
    return [dict(has_consent=int(cat != "White"), category=cat, valid=int(rng.random() > 0.08))]


# --------------------------------------------------------- Shops & Establishment
@register("shops_establishment", columns=[
    "entity_id", "has_registration", "registration_year", "renewed"])
def gen_shops(profile: MSMEProfile):
    if not profile.has_physical_premises:
        return [dict(has_registration=0, registration_year=0, renewed=0)]
    rng = profile.rng(201)
    return [dict(has_registration=1, registration_year=max(2026 - int(profile.age_years), 2010),
                 renewed=int(rng.random() > 0.15))]


# -------------------------------------------------------------- GeM / GeM Sahay
@register("gem", columns=[
    "entity_id", "is_gem_seller", "confirmed_po_count", "po_value"])
def gen_gem(profile: MSMEProfile):
    if not profile.sells_to_govt:
        return [dict(is_gem_seller=0, confirmed_po_count=0, po_value=0.0)]
    rng = profile.rng(211)
    return [dict(is_gem_seller=1, confirmed_po_count=int(rng.integers(1, 30)),
                 po_value=round(profile.true_scale_turnover * rng.uniform(0.1, 0.4), 2))]


# ---------------------------------------------------------- E-commerce seller
@register("ecommerce", columns=[
    "entity_id", "is_seller", "gmv", "return_rate", "seller_rating"])
def gen_ecommerce(profile: MSMEProfile):
    is_seller = profile.sector in ("Trade", "Manufacturing") and profile.digital_adoption and profile.rng(221).random() < 0.3
    if not is_seller:
        return [dict(is_seller=0, gmv=0.0, return_rate=0.0, seller_rating=0.0)]
    rng = profile.rng(221)
    return [dict(is_seller=1, gmv=round(profile.true_scale_turnover * rng.uniform(0.1, 0.5), 2),
                 return_rate=round(float(rng.uniform(0.02, 0.15)), 3),
                 seller_rating=round(float(np.clip(rng.normal(4.1, 0.4), 1, 5)), 2))]


# ------------------------------------------------------------------ Insurance
@register("insurance", columns=[
    "entity_id", "has_policy", "sum_insured", "claims_count"])
def gen_insurance(profile: MSMEProfile):
    asset_heavy = profile.sector == "Manufacturing" or profile.archetype in ("logistics",)
    if not (asset_heavy and profile.rng(231).random() < 0.6):
        return [dict(has_policy=0, sum_insured=0.0, claims_count=0)]
    rng = profile.rng(231)
    return [dict(has_policy=1, sum_insured=round(profile.true_scale_turnover * rng.uniform(0.2, 0.6), 2),
                 claims_count=int(rng.integers(0, 3)))]


# --------------------------------------------------------------- Court records
@register("courts", columns=[
    "entity_id", "cheque_bounce_cases", "commercial_disputes", "pending_cases"])
def gen_courts(profile: MSMEProfile):
    rng = profile.rng(241)
    base = {"healthy": 0.03, "stressed": 0.25, "distressed": 0.6}[profile.true_health]
    bounce = int(rng.random() < base) * int(rng.integers(1, 4))
    disputes = int(rng.random() < base * 0.5) * int(rng.integers(1, 3))
    return [dict(cheque_bounce_cases=bounce, commercial_disputes=disputes,
                 pending_cases=bounce + disputes)]


# ------------------------------------------------------------------- Insolvency
@register("insolvency", columns=[
    "entity_id", "cirp_flag", "liquidation_flag", "promoter_prior_insolvency"])
def gen_insolvency(profile: MSMEProfile):
    rng = profile.rng(251)
    cirp = int(profile.true_health == "distressed" and rng.random() < 0.15)
    return [dict(cirp_flag=cirp, liquidation_flag=int(cirp and rng.random() < 0.3),
                 promoter_prior_insolvency=int(rng.random() < 0.03))]


# ---------------------------------------------------------- Govt procurement
@register("procurement", columns=[
    "entity_id", "tenders_won", "tender_value", "blacklisted"])
def gen_procurement(profile: MSMEProfile):
    if not profile.sells_to_govt:
        return [dict(tenders_won=0, tender_value=0.0, blacklisted=0)]
    rng = profile.rng(261)
    return [dict(tenders_won=int(rng.integers(0, 15)),
                 tender_value=round(profile.true_scale_turnover * rng.uniform(0.05, 0.3), 2),
                 blacklisted=int(profile.true_health == "distressed" and rng.random() < 0.05))]
