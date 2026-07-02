"""Data-completeness confidence score (implementation-plan §5.4, product-framework-notes).

Answers "how thin is this file?" so a thin-file MSME gets a HEDGED score rather
than an auto-reject. Weighted by (sources present for this entity) × (that
source's information value). Ships as a first-class output alongside the pillar
scores — never folded into a pillar.

confidence = Σ_s w_s · present_s / Σ_s w_s ,  w_s = Σ IV over that source's features.
"""
from __future__ import annotations

from typing import Dict, List

from .woe import WOEBinner

# Map every feature to the source that produced it (its `*_present` flag or prefix).
# The engine passes feature->source; here we aggregate IV per source.


class ConfidenceScorer:
    def __init__(self):
        self.source_weight_: Dict[str, float] = {}

    def fit(self, iv: Dict[str, float], feature_source: Dict[str, str]) -> "ConfidenceScorer":
        agg: Dict[str, float] = {}
        for feat, src in feature_source.items():
            agg[src] = agg.get(src, 0.0) + max(iv.get(feat, 0.0), 0.0)
        total = sum(agg.values()) or 1.0
        # Normalise so weights sum to 1 across sources.
        self.source_weight_ = {s: w / total for s, w in agg.items()}
        return self

    # Blend the IV-weighted presence (signal quality) with raw coverage breadth
    # (how much of the footprint is present at all), so a thin file scores lower
    # even when its few present sources happen to be high-IV ones.
    _IV_WEIGHT = 0.6

    def score(self, present_sources: Dict[str, bool]) -> float:
        num = sum(self.source_weight_.get(s, 0.0) for s, present in present_sources.items() if present)
        denom = sum(self.source_weight_.values()) or 1.0
        iv_component = num / denom
        breadth = sum(1 for p in present_sources.values() if p) / max(len(present_sources), 1)
        return float(self._IV_WEIGHT * iv_component + (1 - self._IV_WEIGHT) * breadth)

    @staticmethod
    def band(confidence: float) -> str:
        if confidence >= 0.66:
            return "High"
        if confidence >= 0.4:
            return "Medium"
        return "Low"

    def sources_connected(self, present_sources: Dict[str, bool]) -> str:
        connected = sum(1 for p in present_sources.values() if p)
        return f"{connected} of {len(present_sources)} sources connected"
