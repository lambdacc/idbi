"""SHAP explainer (GBM path) runs and returns per-feature contributions."""


def test_shap_explain_returns_all_features(engine):
    feats = engine.feature_matrix.loc["AUTO_COMPONENTS"].to_dict()
    contribs = engine.shap.explain(feats)
    assert set(contribs.keys()) == set(engine.gbm.features_)
    assert all(isinstance(v, float) for v in contribs.values())


def test_shap_top_features(engine):
    feats = engine.feature_matrix.loc["RESTAURANT"].to_dict()
    top = engine.shap.top_features(feats, k=5)
    assert len(top) == 5
    # sorted by descending absolute contribution
    mags = [abs(v) for _, v in top]
    assert mags == sorted(mags, reverse=True)
