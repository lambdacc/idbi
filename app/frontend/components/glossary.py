"""Central glossary for tooltip copy (implementation-plan §6 Copy Bank CB-10).

Every info tooltip in the app imports its text from here so the language stays
consistent across pages. Each entry is <= 25 words, in plain terms aimed at bank
ops / management users (not data scientists). Never inline tooltip strings in
pages — add or reuse a key here instead.
"""
from __future__ import annotations

from typing import Dict

GLOSSARY: Dict[str, str] = {
    "financial_health_score": (
        "Composite 0–100 measure of overall financial health, built from five "
        "dimensions of verified alternate data. Higher is healthier."
    ),
    "grade": (
        "1–10 ranking analogous to a bureau's MSME rank; 1 is best."
    ),
    "pd": (
        "Statistically estimated chance of repayment difficulty in the next 12 "
        "months, from a model trained on similar businesses."
    ),
    "indicative_limit": (
        "A starting exposure suggestion derived from verified turnover and the "
        "onboarding band — not a sanction."
    ),
    "confidence": (
        "How much verified data backs this assessment — more independent "
        "sources, higher confidence."
    ),
    "authenticity": (
        "Cross-check of declared sales against bank credits and goods movement. "
        "Low values suggest inflated declarations."
    ),
    "peer_segment": (
        "Descriptive grouping of similar businesses for context; never part of "
        "the score."
    ),
    "bureau_score": (
        "The same assessment expressed on the familiar 300–900 scale."
    ),
    "onboarding_band": (
        "Routing suggestion: fast-track, manual review, or decline."
    ),
    "sources_connected": (
        "Independent systems (tax, banking, utilities, registries…) with live "
        "records for this business."
    ),
    "fraud_risk": (
        "Blended fraud-risk score: the turnover-authenticity check plus an "
        "independent anomaly cross-check, rated Low, Moderate or Elevated."
    ),
    "anomaly_detection": (
        "A cross-check that learns the normal cross-source profile with no fraud "
        "labels, then flags businesses that look unusual against it."
    ),
    "calibration": (
        "Tuning so a stated X% risk reflects about X in 100 similar businesses "
        "hitting trouble — a real chance, not just a ranking."
    ),
}
