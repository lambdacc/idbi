"""Cross-source synthesis layer — Appendix A §5 composite-indicator catalog.

Pure functions of already-computed per-source features (never re-reads raw source
data), so the layer is testable in isolation (implementation-plan.md §5.2). Each
composite returns a numeric feature; `composite_rationales` returns the parallel
manipulation-resistance strings surfaced later in reason codes.
"""
from __future__ import annotations

from typing import Dict

from .turnover_authenticity import compute_turnover_authenticity, authenticity_rationale


def _ratio(a: float, b: float) -> float:
    if a <= 0 or b <= 0:
        return 0.0
    return min(a, b) / max(a, b)


def compute_composites(feats: Dict[str, float], master_row: dict) -> Dict[str, float]:
    out: Dict[str, float] = {}

    # 1. Turnover-Authenticity (flagship)
    out.update(compute_turnover_authenticity(feats, master_row))

    declared = feats.get("gst_total_turnover", 0.0)

    # 2. Energy Intensity — turnover consistent with metered electricity.
    #    Flag (1 = inconsistent/red) when declared turnover and kWh diverge.
    if declared > 0 and feats.get("electricity_present", 0.0):
        agree = _ratio(declared, feats.get("electricity_total_kwh", 0.0) * 40.0)  # ~INR40/kWh output
        out["energy_intensity_flag"] = round(1.0 - agree, 3)
    else:
        out["energy_intensity_flag"] = 0.0

    # 3. Estimated Production Capacity — electricity + EPFO headcount + factory licence agree.
    signals = []
    if feats.get("electricity_present", 0.0):
        signals.append(min(feats.get("electricity_sanctioned_load", 0.0) / 100.0, 1.0))
    if feats.get("epfo_present", 0.0):
        signals.append(min(feats.get("epfo_headcount_latest", 0.0) / 50.0, 1.0))
    if feats.get("factory_has_licence", 0.0):
        signals.append(min(feats.get("factory_sanctioned_workers", 0.0) / 50.0, 1.0))
    out["production_capacity_consistency"] = round(
        1.0 - (max(signals) - min(signals)) if len(signals) >= 2 else 0.0, 3)

    # 4. Logistics-Activity Index — e-way bills + vehicles.
    out["logistics_activity_index"] = round(min(
        feats.get("ewb_count_total", 0.0) / 100.0 + feats.get("vahan_num_vehicles", 0.0) / 10.0, 1.0), 3)

    # 5. Premises Authenticity — property-tax address corroborates GST premises.
    out["premises_authenticity"] = round(
        0.5 * feats.get("ptax_address_matches_gst", 0.0)
        + 0.3 * feats.get("ptax_has_record", 0.0)
        + 0.2 * feats.get("shops_registered", 0.0), 3)

    # 6. Business Continuity — bank + UPI + GST filing all continuously active.
    out["business_continuity"] = round(
        (feats.get("bank_present", 0.0) + feats.get("upi_present", 0.0)
         + feats.get("gst_present", 0.0) * feats.get("gst_filing_regularity", 0.0)) / 3.0, 3)

    # 7. Operational Stability — utilities + EPFO obligations met (no arrears/disconnection).
    out["operational_stability"] = round(
        0.5 * feats.get("electricity_bill_ontime_rate", 0.0)
        + 0.5 * (1.0 - feats.get("epfo_arrears_rate", 0.0)), 3)

    # 8. B2G Credibility — confirmed GeM POs + tenders won, minus blacklist.
    out["b2g_credibility"] = round(min(
        feats.get("gem_confirmed_po_count", 0.0) / 20.0
        + feats.get("proc_tenders_won", 0.0) / 15.0, 1.0)
        * (0.0 if feats.get("proc_blacklisted", 0.0) else 1.0), 3)

    # 9. Legal-Risk Overlay — court + insolvency + director-disqualification (higher = worse).
    out["legal_risk_overlay"] = round(min(
        feats.get("court_cheque_bounce_cases", 0.0) * 0.2
        + feats.get("insolvency_cirp_flag", 0.0) * 0.6
        + feats.get("insolvency_promoter_prior", 0.0) * 0.5
        + feats.get("mca_director_disqualified", 0.0) * 0.4, 1.0), 3)

    # 10. Export Orientation — DGFT export value vs GST export markers (IGST-heavy).
    out["export_orientation"] = round(min(
        feats.get("dgft_export_value", 0.0) / max(declared, 1.0)
        + 0.3 * min(feats.get("gst_igst_ratio", 0.0), 1.0), 1.0), 3) if feats.get("dgft_has_iec", 0.0) else 0.0

    # 11. Formal-Identity Integrity — Udyam + PAN/GSTIN + MCA all resolve to one entity.
    out["formal_identity_integrity"] = round(
        0.3 * feats.get("udyam_registered", 0.0)
        + 0.3 * feats.get("gstin_active", 0.0)
        + 0.2 * feats.get("identity_name_match", 0.0)
        + 0.2 * (feats.get("mca_has_record", 0.0) if master_row.get("incorporated") else 1.0), 3)

    # 12. Credit-Exposure Cross-Check — bank EMI debits vs bureau-declared obligations.
    bureau_exp = feats.get("bureau_exposure", 0.0)
    bank_emi = feats.get("foir", 0.0)
    # Undisclosed borrowing: EMI debits present but no matching bureau exposure.
    out["credit_exposure_mismatch"] = round(
        1.0 if (bank_emi > 0.05 and bureau_exp <= 0 and feats.get("bureau_has_record", 0.0)) else 0.0, 3)

    return out


def composite_rationales(feats: Dict[str, float]) -> Dict[str, str]:
    """Manipulation-resistance strings (Appendix A §5 'what must be compromised')."""
    r = {"turnover_authenticity_score": authenticity_rationale(feats)}
    if feats.get("energy_intensity_flag", 0.0) > 0.4:
        r["energy_intensity_flag"] = ("Declared turnover is inconsistent with metered electricity "
                                      "consumption — faking both a self-filed GST return and a "
                                      "DISCOM-metered bill simultaneously is materially harder.")
    if feats.get("premises_authenticity", 0.0) >= 0.7:
        r["premises_authenticity"] = ("Business premises corroborated across independent municipal "
                                      "property-tax and Shops-&-Establishment records, not one self-declared address.")
    if feats.get("legal_risk_overlay", 0.0) > 0.3:
        r["legal_risk_overlay"] = ("Promoter/entity-level court or insolvency records present — an "
                                   "independently-maintained judicial signal that cannot be scrubbed by re-incorporating.")
    if feats.get("b2g_credibility", 0.0) > 0.2:
        r["b2g_credibility"] = ("Government-counterparty-verified revenue (GeM POs / awarded tenders) — "
                                "confirmed by a buyer the applicant does not control. IDBI is a live GeM Sahay partner.")
    return r
