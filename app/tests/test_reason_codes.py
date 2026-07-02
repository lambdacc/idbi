"""Sprint-2 acceptance (b): reason codes non-empty and directionally consistent."""
from app.ml.models.pillars import PillarScorer
from app.ml.explainability.reason_codes import generate_reason_codes, reason_feature_set


def test_reasons_nonempty_for_archetypes(engine):
    for eid in ["TEXTILE_MANUFACTURER", "AUTO_COMPONENTS", "RESTAURANT"]:
        r = engine.score_entity(eid)
        assert r["reasons_positive"] or r["reasons_negative"]


def test_reason_sign_matches_component(engine, feature_matrix):
    """A positive reason must come from a feature scoring ABOVE neutral (50),
    a negative reason from BELOW — the contract in implementation-plan §5.5."""
    ps = engine.pillars
    for eid in ["TEXTILE_MANUFACTURER", "AUTO_COMPONENTS", "RESTAURANT", "IT_SERVICES"]:
        feats = engine.feature_matrix.loc[eid].to_dict()
        comps = ps.component_scores(feats)
        pos, neg = generate_reason_codes(comps, ps.feature_cfg)
        for p in pos:
            assert p["direction"] == 1
            assert comps[p["feature"]] > 50.0
        for n in neg:
            assert n["direction"] == -1
            assert comps[n["feature"]] < 50.0


def test_positive_and_negative_are_disjoint(engine):
    r = engine.score_entity("AUTO_COMPONENTS")
    assert reason_feature_set(r["reasons_positive"]).isdisjoint(reason_feature_set(r["reasons_negative"]))


def test_reason_text_is_populated(engine):
    r = engine.score_entity("AUTO_COMPONENTS")
    for item in r["reasons_positive"] + r["reasons_negative"]:
        assert isinstance(item["text"], str) and len(item["text"]) > 3
