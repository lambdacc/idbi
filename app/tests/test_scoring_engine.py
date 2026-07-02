"""End-to-end scoring engine + HealthCard service contract."""
import pytest

from app.backend.services.scoring_service import build_health_card
from app.backend.schemas.models import HealthCard, pillar_label_map

ARCHETYPES = ["TEXTILE_MANUFACTURER", "RETAIL_KIRANA", "RESTAURANT",
              "IT_SERVICES", "AUTO_COMPONENTS", "LOGISTICS"]


@pytest.mark.parametrize("eid", ARCHETYPES)
def test_payload_ranges(engine, eid):
    r = engine.score_entity(eid)
    assert 1 <= r["grade"] <= 10
    assert 0.0 <= r["composite_score"] <= 100.0
    assert 0.0 <= r["pd"] <= 1.0
    assert 0.0 <= r["confidence"] <= 1.0
    assert 0.0 <= r["turnover_authenticity_score"] <= 100.0
    assert len(r["pillar_scores"]) == 5
    assert r["onboarding_band"] in {"fast_track", "review", "decline"}


def test_healthy_outranks_stressed(engine):
    textile = engine.score_entity("TEXTILE_MANUFACTURER")
    restaurant = engine.score_entity("RESTAURANT")
    assert textile["composite_score"] > restaurant["composite_score"]
    assert textile["grade"] < restaurant["grade"]      # lower grade number = healthier


def test_inflated_turnover_is_flagged(engine):
    """The fraud showcase: authenticity must catch the inflated auto-components
    profile even if its PD looks benign — the 'harder to fake' differentiator."""
    auto = engine.score_entity("AUTO_COMPONENTS")
    genuine = engine.score_entity("TEXTILE_MANUFACTURER")
    assert auto["turnover_authenticity_score"] < genuine["turnover_authenticity_score"]
    assert auto["turnover_authenticity_score"] < 75


def test_health_card_contract(engine):
    card = build_health_card(engine.score_entity("TEXTILE_MANUFACTURER"))
    assert isinstance(card, HealthCard)
    assert 1 <= card.grade <= 10
    labels = set(pillar_label_map().values())
    assert {p.label for p in card.pillars} == labels    # brief-mandated vocabulary applied
    # pydantic round-trip
    assert HealthCard(**card.model_dump()).entity_id == card.entity_id


def test_prefit_pickle_round_trip(engine, tmp_path):
    """Build-time pre-fit (app.ml.prefit): a pickled engine must reload with SHAP
    rebuilt and produce identical scores — the Cloud Run cold-start path."""
    import pickle

    path = tmp_path / "engine.pkl"
    engine.save(path)
    with open(path, "rb") as fh:
        loaded = pickle.load(fh)

    assert loaded.shap is not None                      # rebuilt in __setstate__
    a = engine.score_entity("TEXTILE_MANUFACTURER")
    b = loaded.score_entity("TEXTILE_MANUFACTURER")
    assert a["composite_score"] == b["composite_score"]
    assert a["grade"] == b["grade"]
    assert a["pd"] == b["pd"]
