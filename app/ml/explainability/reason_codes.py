"""Reason-code generation (solution-design.md §6 — bank-grade explainability).

Reason codes are derived from the DETERMINISTIC pillar component scores, so they
are sign-consistent with each feature's documented direction BY CONSTRUCTION
(Sprint-2 acceptance b): a feature scoring above its neutral midpoint is a
strength (+), below is a risk (-). Text comes from feature_config rationales and
the composite manipulation-resistance strings. The scorecard/SHAP paths explain
the PD model separately (shap_explainer.py).
"""
from __future__ import annotations

from typing import Dict, List, Tuple

_NEUTRAL = 50.0

# Concise human labels for sign-aware phrasing (kept here, not in config, so the
# config stays a pure feature/direction/rationale record).
_LABELS = {
    "bank_avg_balance": "average bank balance",
    "bank_balance_volatility": "balance volatility",
    "bank_low_balance_freq": "low-balance frequency",
    "bank_net_flow_trend": "net cash-flow trend",
    "gst_itc_to_tax_paid": "ITC-to-tax-paid ratio",
    "gst_turnover_level": "GST turnover level",
    "gst_turnover_trend": "GST turnover trend",
    "gst_filing_regularity": "GST filing regularity",
    "gst_customer_concentration": "customer concentration",
    "gst_credit_note_ratio": "credit-note ratio",
    "bureau_delinquency": "bureau delinquency (DPD)",
    "bank_bounce_frequency": "cheque/NACH bounce frequency",
    "dscr": "debt-service coverage (DSCR)",
    "foir": "fixed-obligation-to-income (FOIR)",
    "turnover_authenticity_score": "turnover authenticity",
    "energy_intensity_flag": "energy-intensity consistency",
    "premises_authenticity": "premises authenticity",
    "business_age_years": "business vintage",
    "banking_relationship_months": "banking-relationship length",
    "epfo_workforce_stability": "EPFO workforce stability",
}


def _sign_aware_text(fname: str, direction: int, is_strength: bool) -> str:
    """direction = health direction (+1 higher-is-better, -1 higher-is-worse)."""
    label = _LABELS.get(fname, fname.replace("_", " "))
    if is_strength:
        return f"Strong {label}"
    # Risk phrasing depends on which end of the feature is the bad one.
    return f"{'Weak' if direction > 0 else 'Elevated'} {label}"


def _direction_map(feature_cfg: dict) -> Dict[str, int]:
    out = {}
    for feats in feature_cfg.values():
        for fname, spec in feats.items():
            out[fname] = int(spec["direction"])
    return out


def generate_reason_codes(
    component_scores: Dict[str, float],
    feature_cfg: dict,
    composite_rationales: Dict[str, str] | None = None,
    top_k: int = 3,
    min_deviation: float = 8.0,
) -> Tuple[List[dict], List[dict]]:
    """Return (positive_reasons, negative_reasons), each a list of reason dicts."""
    directions = _direction_map(feature_cfg)
    composite_rationales = composite_rationales or {}

    scored = []
    for fname, comp in component_scores.items():
        deviation = comp - _NEUTRAL           # >0 strength, <0 risk
        if abs(deviation) < min_deviation:
            continue
        is_strength = deviation > 0
        # Prefer a composite's dynamic, already sign-aware manipulation-resistance
        # note; otherwise build sign-aware text from the feature's direction.
        text = composite_rationales.get(fname) or _sign_aware_text(
            fname, directions.get(fname, 1), is_strength)
        scored.append({
            "feature": fname,
            "direction": 1 if is_strength else -1,
            "contribution": round(float(deviation), 2),
            "text": text,
        })

    positives = sorted([s for s in scored if s["direction"] == 1],
                       key=lambda s: -s["contribution"])[:top_k]
    negatives = sorted([s for s in scored if s["direction"] == -1],
                       key=lambda s: s["contribution"])[:top_k]
    return positives, negatives


def reason_feature_set(reasons: List[dict]) -> set:
    return {r["feature"] for r in reasons}
