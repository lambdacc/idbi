"""Canonical API/payload contract (implementation-plan.md §3, §5.3).

The internal engineering pillar names live in ml/ and config/; the brief-facing
Health Card labels (Repayment Capacity, Growth Trajectory, Creditworthiness,
Risk Profile, Stability & Vintage) are applied ONCE here — the single display-
layer mapping point, so ml/ stays label-agnostic.

Sprint 1 defines the contract; scoring_service (Sprint 2) populates it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

import yaml
from pydantic import BaseModel, Field

_CONFIG = Path(__file__).resolve().parents[2] / "config" / "scoring_config.yaml"


def pillar_label_map() -> Dict[str, str]:
    """engineering_name -> brief-facing Health Card label (from scoring_config.yaml)."""
    cfg = yaml.safe_load(_CONFIG.read_text())
    return {name: spec["label"] for name, spec in cfg["pillars"].items()}


class PillarScore(BaseModel):
    engineering_name: str          # e.g. "cash_flow_health"
    label: str                     # e.g. "Repayment Capacity"
    score: float = Field(ge=0, le=100)


class ReasonCode(BaseModel):
    feature: str
    direction: int                 # +1 strength, -1 risk
    text: str                      # plain-language reason
    contribution: Optional[float] = None


class HealthCard(BaseModel):
    entity_id: str
    name: str
    composite_score: float = Field(ge=0, le=100)
    grade: int = Field(ge=1, le=10)             # 1 = healthiest (CMR-style)
    onboarding_band: str                        # fast_track / review / decline
    recommendation: str
    confidence: str                             # data-completeness confidence
    pillars: List[PillarScore]
    reasons_positive: List[ReasonCode] = []
    reasons_negative: List[ReasonCode] = []
    turnover_authenticity_score: float = Field(ge=0, le=100)
    # Unsupervised fraud cross-check (Isolation Forest) + blended fraud risk.
    anomaly_score: Optional[float] = None           # 0-100, higher = more unusual profile
    fraud_risk_score: Optional[float] = None        # 0-100, blended authenticity + anomaly
    fraud_band: Optional[str] = None                # Low / Moderate / Elevated
    peer_segment: Optional[str] = None
    indicative_limit: Optional[float] = None
