"""Sprint-2 acceptance (a): monotonicity of the scoring output in each feature
per its documented direction; plus WOE/IV, confidence, and clustering checks.
"""
import numpy as np
import pandas as pd
import pytest

from app.ml.models.woe import WOEBinner
from app.ml.models.pillars import PillarScorer
from app.ml.models.confidence_score import ConfidenceScorer


# --------------------------------------------------------------- monotonicity
def _baseline(feature_matrix):
    return feature_matrix.median(numeric_only=True).to_dict()


def test_deterministic_composite_monotonic(feature_matrix):
    """Composite must not improve as a risk feature rises, nor fall as a
    protective feature rises (percentile transform + linear composite)."""
    ps = PillarScorer().fit(feature_matrix)
    base = _baseline(feature_matrix)

    # bank_bounce_frequency: direction -1 (higher = worse) -> composite non-increasing
    grid = np.linspace(0, feature_matrix["bank_bounce_frequency"].max() + 1, 12)
    scores = []
    for v in grid:
        f = dict(base); f["bank_bounce_frequency"] = v
        scores.append(ps.composite(ps.pillar_scores(f)))
    assert all(scores[i + 1] <= scores[i] + 1e-9 for i in range(len(scores) - 1)), scores

    # bank_avg_balance: direction +1 -> composite non-decreasing
    grid = np.linspace(0, feature_matrix["bank_avg_balance"].max() + 1, 12)
    scores = []
    for v in grid:
        f = dict(base); f["bank_avg_balance"] = v
        scores.append(ps.composite(ps.pillar_scores(f)))
    assert all(scores[i + 1] >= scores[i] - 1e-9 for i in range(len(scores) - 1)), scores


def test_gbm_pd_monotonic_in_constrained_feature(engine, feature_matrix):
    """Monotonic LightGBM: PD must not decrease as a risk feature increases."""
    base = _baseline(feature_matrix)
    cols = engine.gbm.features_
    grid = np.linspace(0, feature_matrix["bank_bounce_frequency"].max() + 1, 15)
    rows = []
    for v in grid:
        f = dict(base); f["bank_bounce_frequency"] = v
        rows.append({c: f.get(c, 0.0) for c in cols})
    pd_vals = engine.gbm.predict_pd(pd.DataFrame(rows))
    assert all(pd_vals[i + 1] >= pd_vals[i] - 1e-9 for i in range(len(pd_vals) - 1)), pd_vals


# ------------------------------------------------------------------- WOE / IV
def test_woe_iv_nonnegative_and_transform_shape(feature_matrix):
    X = feature_matrix.drop(columns=["label_default", "label_fraud"])
    y = feature_matrix["label_default"].to_numpy()
    b = WOEBinner(n_bins=5).fit(X, y)
    assert all(v >= -1e-9 for v in b.iv_.values())     # IV is non-negative
    Xw = b.transform(X)
    assert Xw.shape == X.shape
    assert not Xw.isna().any().any()


# ----------------------------------------------------------------- confidence
def test_confidence_bands_monotone():
    c = ConfidenceScorer()
    c.source_weight_ = {"a": 0.5, "b": 0.3, "c": 0.2}
    full = c.score({"a": True, "b": True, "c": True})
    partial = c.score({"a": True, "b": False, "c": False})
    none = c.score({"a": False, "b": False, "c": False})
    assert full > partial > none
    assert c.band(full) in {"High", "Medium", "Low"}
    assert c.band(0.9) == "High" and c.band(0.0) == "Low"


# ----------------------------------------------------------------- clustering
def test_clustering_k_in_range_and_named(engine):
    assert 3 <= engine.segmenter.k <= 5
    assert engine.segmenter.name(0)
