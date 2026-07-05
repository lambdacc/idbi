"""Track-04 glossary + Simple-mode jargon guardrail (in-track; not appended to the
shared `components/glossary.py`).

`GLOSSARY` supplies plain-language tooltip copy for the EWS terms the pages use.
`BANNED_SIMPLE` is the Track-04 extension of the platform jargon sweep: any of
these terms must NOT appear in Simple mode without a plain gloss — the track's own
jargon test asserts the two Simple pages are clean.
"""
from __future__ import annotations

from typing import Dict, List

GLOSSARY: Dict[str, str] = {
    "lead_time": (
        "How many months earlier the alt-data model turns Red than a "
        "repayment-only view — the warning you gain."
    ),
    "watchlist": (
        "Borrowers flagged Red or Amber this month, ranked so the ones needing "
        "action come first."
    ),
    "band": (
        "A simple traffic light: Green (routine), Amber (watch closely), Red "
        "(act now)."
    ),
    "exposure": (
        "The rupee amount on the line for a loan — here the synthetic sanctioned "
        "limit, an illustrative planning estimate."
    ),
    "days_late": (
        "How many days behind the borrower is on an EMI. Zero means paid on time."
    ),
    "baseline": (
        "A stand-in for a repayment-only internal model: it can only react once "
        "EMIs start slipping, so it warns late."
    ),
    "default_risk": (
        "The estimated chance this loan runs into serious repayment trouble in "
        "the next 12 months."
    ),
    "projected_default": (
        "A forward projection of when this account would hit default if the "
        "current deterioration continues — not an event that has happened."
    ),
    "early_warning": (
        "Spotting trouble early from a business's digital footprint (GST, bank "
        "inflows, payroll) before repayments slip."
    ),
}

# Terms that must never surface raw in Simple mode (extends the platform sweep).
# These are the model-internal / regulator-shorthand terms Track-04 introduces;
# each has a plain synonym the Simple pages use instead (DPD -> "days late",
# NPA -> "loan gone bad", PD -> "default risk", etc.).
BANNED_SIMPLE: List[str] = [
    "DPD", "NPA", "PD-12m", "capture@decile", "calibrated PD", "LightGBM",
    "monotonic", "AUC", "holdout", "utilisation", "utilization",
    "SAJAG", "isotonic", "calibration",
]
