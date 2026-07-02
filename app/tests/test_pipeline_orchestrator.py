"""Sprint-3 acceptance (b): exercise the callable pipeline-orchestrator functions
end-to-end for >=2 archetypes without exceptions — NOT the Streamlit UI itself.

Asserts the 9-stage state machine is well-formed and every stage carries the
structured `data` its visualization needs, so the frontend (a pure renderer) has
a stable contract to consume.
"""
import pytest

from app.backend.schemas.models import HealthCard
from app.backend.services.pipeline_orchestrator import (COMPOSITE_CATALOG, SOURCE_CATALOG,
                                                         list_scenarios, random_entity_id,
                                                         run_assessment)

ARCHETYPES = ["TEXTILE_MANUFACTURER", "AUTO_COMPONENTS"]

# stage key -> keys its .data dict must expose for the frontend
_STAGE_DATA_KEYS = {
    "scenario_lock_in": ["entity"],
    "ingestion": ["sources", "connected", "total"],
    "integration": ["connected", "total_records", "identity_integrity"],
    "features": ["counters", "composite_count", "total_features"],
    "synthesis": ["composites"],
    "clustering": ["scatter", "entity_point", "segment", "k"],
    "scoring": ["pillars", "composite_score", "grade", "onboarding_band", "recommendation",
                "pd", "risk_category", "confidence_band"],
    "explainability": ["reasons_positive", "reasons_negative", "shap_top"],
    "health_card": ["health_card"],
}


def test_list_scenarios_present(engine):
    scenarios = list_scenarios(engine)
    ids = {s["entity_id"] for s in scenarios}
    assert len(scenarios) >= 2
    for eid in ARCHETYPES:
        assert eid in ids
    for s in scenarios:
        assert s["name"] and s["sector"] and s["blurb"]


@pytest.mark.parametrize("entity_id", ARCHETYPES)
def test_run_assessment_nine_stages(engine, entity_id):
    a = run_assessment(entity_id, engine)

    # exactly the 9 stages, in order, each with log + the expected data keys
    assert [s.index for s in a.stages] == list(range(1, 10))
    assert [s.key for s in a.stages] == list(_STAGE_DATA_KEYS.keys())
    for s in a.stages:
        assert s.log, f"stage {s.key} has no log lines"
        assert s.title and s.caption
        for key in _STAGE_DATA_KEYS[s.key]:
            assert key in s.data, f"stage {s.key} missing data['{key}']"

    # terminal health card is a valid typed payload with the full contract
    assert isinstance(a.health_card, HealthCard)
    assert 0 <= a.health_card.composite_score <= 100
    assert 1 <= a.health_card.grade <= 10
    assert len(a.health_card.pillars) == 5

    # ingestion breadth + clustering scatter are populated
    ing = a.stage("ingestion").data
    assert 0 < ing["connected"] <= ing["total"] == len(SOURCE_CATALOG)
    clu = a.stage("clustering").data
    assert len(clu["scatter"]) > 0
    assert set(clu["entity_point"]) == {"x", "y"}

    # every composite in the catalog is surfaced in the synthesis stage
    syn_keys = {c["key"] for c in a.stage("synthesis").data["composites"]}
    assert syn_keys == {c["key"] for c in COMPOSITE_CATALOG}


def test_inflated_archetype_authenticity_lower(engine):
    """The differentiator: the inflated showcase scores materially lower on the
    flagship Turnover-Authenticity check than the clean genuine manufacturer."""
    genuine = run_assessment("TEXTILE_MANUFACTURER", engine).health_card.turnover_authenticity_score
    inflated = run_assessment("AUTO_COMPONENTS", engine).health_card.turnover_authenticity_score
    assert inflated < genuine


def test_random_entity_id_valid(engine):
    eid = random_entity_id(engine, seed=7)
    assert eid in set(engine.tables["msme_master"]["entity_id"])
