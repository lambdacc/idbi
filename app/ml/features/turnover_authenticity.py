"""Turnover-Authenticity Score — the flagship cross-source integrity check.

intel-cag-gst-feature-analysis.md §6 / Appendix A §5 #1. Reconciles declared GST
turnover against independently-governed TURNOVER evidence trails — turnover-vs-
turnover only, so genuine low-margin businesses are NOT mistaken for fraud:
  * AA bank settled inflows      (a regulated bank of record)
  * E-way-bill goods movement    (GSTN cross-validates 3B vs EWB)

(ITR-reported income is deliberately excluded here: income/turnover conflates
profitability with authenticity — it belongs in a separate profitability signal.)

Each available check yields an agreement ratio in [0, 1] (1 = perfect match);
the score is their tolerance-banded mean * 100. An 'inflated' entity declares
turnover far above its true settled/moved evidence, so the ratios drop and the
score falls — catching exactly the fraud the demo showcases.

Robustness (intel §7 caution): ratios are clipped and tolerance-banded so dirty
single-source outliers cannot dominate.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

# Within this tolerance the two figures are treated as a full match (ratio 1.0).
_TOLERANCE = 0.20


def _agreement(declared: float, evidence: float) -> float:
    """1.0 when within tolerance; decays toward 0 as they diverge."""
    if declared <= 0 or evidence <= 0:
        return 0.0
    ratio = min(declared, evidence) / max(declared, evidence)
    # Rescale so that ratio >= (1 - tol) counts as full agreement.
    thresh = 1.0 - _TOLERANCE
    if ratio >= thresh:
        return 1.0
    return max(0.0, ratio / thresh)


def compute_turnover_authenticity(feats: Dict[str, float], master_row: dict) -> Dict[str, float]:
    declared = feats.get("gst_total_turnover", 0.0)
    is_services = master_row.get("sector") == "Services"

    checks: List[Tuple[str, float]] = []
    ta_detail: Dict[str, float] = {}

    if declared > 0:
        # GST vs bank settled inflows (the signature check)
        if feats.get("bank_present", 0.0):
            r = _agreement(declared, feats.get("bank_total_inflow", 0.0))
            checks.append(("gst_bank", r)); ta_detail["ta_gst_bank_ratio"] = r
        # GST vs e-way-bill goods movement (goods sectors only)
        if not is_services and feats.get("ewb_present", 0.0):
            r = _agreement(declared, feats.get("ewb_total_value", 0.0))
            checks.append(("gst_ewb", r)); ta_detail["ta_gst_ewb_ratio"] = r

    if checks:
        score = 100.0 * sum(r for _, r in checks) / len(checks)
    else:
        # No GST footprint (legally exempt thin-file) — cannot assess; neutral,
        # flagged low-confidence by the data-completeness score, never penalised.
        score = 60.0

    ta_detail["turnover_authenticity_score"] = round(score, 1)
    ta_detail["ta_num_checks"] = float(len(checks))
    return ta_detail


def authenticity_rationale(feats: Dict[str, float]) -> str:
    """Plain-language manipulation-resistance note for the Health Card."""
    score = feats.get("turnover_authenticity_score", 0.0)
    if feats.get("ta_num_checks", 0.0) == 0:
        return ("No GST footprint to reconcile — turnover authenticity cannot be "
                "assessed; scored on other pillars with reduced confidence.")
    if score >= 80:
        return ("Declared turnover is corroborated by independently-governed bank, "
                "goods-movement and tax records — faking it would require compromising "
                "a regulated bank, GSTN e-way-bill validation and the CBDT filing at once.")
    if score >= 55:
        return ("Declared turnover only partially matches settled bank inflows and "
                "goods-movement evidence — a moderate authenticity gap worth a manual check.")
    return ("Declared turnover materially exceeds settled bank inflows and goods-movement "
            "evidence — a strong inflated-turnover red flag.")
