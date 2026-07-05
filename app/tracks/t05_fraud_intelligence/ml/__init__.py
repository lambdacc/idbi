"""SentinelPulse detection ML (Track 05, WP-5M).

Public surface for WP-5A (case orchestration + frontend) and the tests:

  * ``FraudEngine``  — fit / score_accounts / typology_hits / expand_ring / save
  * ``TypologyHit``  — the evidence dataclass (citation backbone)
  * ``get_engine`` / ``prefit`` / ``warm`` / ``ENGINE_PICKLE`` — prefit warm + load
"""
from __future__ import annotations

from .model import (BAND_ALERT, BAND_REVIEW, ENGINE_PICKLE, FraudEngine,
                    get_engine, prefit, warm)
from .typologies import TypologyHit

__all__ = [
    "FraudEngine", "TypologyHit", "get_engine", "prefit", "warm",
    "ENGINE_PICKLE", "BAND_ALERT", "BAND_REVIEW",
]
