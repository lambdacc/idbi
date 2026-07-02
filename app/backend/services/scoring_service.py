"""Scoring service — turns raw engine output into the typed HealthCard payload.

This is the single point where internal engineering pillar names become the
brief-facing Health Card labels (implementation-plan.md §5.3). `ml/` stays
label-agnostic; `frontend/` consumes only this typed contract.
"""
from __future__ import annotations

from typing import Dict

from ...ml.engine import get_engine, ScoringEngine
from ..schemas.models import HealthCard, PillarScore, ReasonCode, pillar_label_map


def _reason_codes(items) -> list:
    return [ReasonCode(feature=r["feature"], direction=r["direction"],
                       text=r["text"], contribution=r.get("contribution")) for r in items]


def build_health_card(engine_output: Dict) -> HealthCard:
    labels = pillar_label_map()
    pillars = [
        PillarScore(engineering_name=name, label=labels.get(name, name), score=round(score, 1))
        for name, score in engine_output["pillar_scores"].items()
    ]
    return HealthCard(
        entity_id=engine_output["entity_id"],
        name=str(engine_output["name"]),
        composite_score=engine_output["composite_score"],
        grade=engine_output["grade"],
        onboarding_band=engine_output["onboarding_band"],
        recommendation=engine_output["recommendation"],
        confidence=f"{engine_output['confidence_band']} ({engine_output['sources_connected']})",
        pillars=pillars,
        reasons_positive=_reason_codes(engine_output["reasons_positive"]),
        reasons_negative=_reason_codes(engine_output["reasons_negative"]),
        turnover_authenticity_score=engine_output["turnover_authenticity_score"],
        peer_segment=engine_output["peer_segment"],
        indicative_limit=engine_output["indicative_limit"],
    )


def score_msme(entity_id: str, engine: ScoringEngine | None = None) -> HealthCard:
    """Public entry point used by the frontend: entity_id -> typed HealthCard."""
    engine = engine or get_engine()
    return build_health_card(engine.score_entity(entity_id))
