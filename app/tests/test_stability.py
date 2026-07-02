"""Reason-code stability across recalibration (solution-design.md §6).

Refit the pillar scorer on bootstrap resamples of the cohort; the top reason-code
features for a fixed reference entity should stay largely consistent. Guards the
SHAP/reason-code-instability risk the research flagged.
"""
from app.ml.models.pillars import PillarScorer
from app.ml.explainability.reason_codes import generate_reason_codes, reason_feature_set
from app.ml.explainability.stability import stability_across_refits, jaccard


def test_jaccard_basics():
    assert jaccard(set(), set()) == 1.0
    assert jaccard({"a", "b"}, {"a", "b"}) == 1.0
    assert jaccard({"a"}, {"b"}) == 0.0


def test_reason_codes_stable_across_refits(engine, feature_matrix):
    ref_feats = engine.feature_matrix.loc["RESTAURANT"].to_dict()
    cfg = engine.pillars.feature_cfg

    def refit_reason_features(seed: int):
        sample = feature_matrix.sample(frac=1.0, replace=True, random_state=seed)
        ps = PillarScorer().fit(sample)
        comps = ps.component_scores(ref_feats)
        pos, neg = generate_reason_codes(comps, cfg)
        return reason_feature_set(pos) | reason_feature_set(neg)

    stability = stability_across_refits(refit_reason_features, seeds=[1, 2, 3, 4, 5])
    assert stability >= 0.5, f"reason codes unstable across refits: {stability:.2f}"
