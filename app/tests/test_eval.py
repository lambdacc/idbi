"""Eval-harness tests: metric correctness, leakage-resistant split, PSI, end-to-end."""
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from app.ml.eval import metrics
from app.ml.eval.holdout import split, ARCHETYPE_IDS
from app.ml.eval.psi import psi


def test_metrics_perfect_separation():
    y = [0, 0, 1, 1]
    s = [0.1, 0.2, 0.8, 0.9]
    assert metrics.auc(y, s) == 1.0
    assert metrics.gini(y, s) == 1.0
    assert abs(metrics.ks(y, s) - 1.0) < 1e-9


def test_metrics_single_class_is_nan():
    assert metrics.auc([1, 1, 1], [0.1, 0.2, 0.3]) != metrics.auc([1, 1, 1], [0.1, 0.2, 0.3])  # nan


def test_holdout_no_overlap_and_archetypes_in_train(feature_matrix):
    train, test = split(feature_matrix, seed=1)
    assert set(train.index).isdisjoint(set(test.index))
    present_archetypes = ARCHETYPE_IDS & set(feature_matrix.index)
    assert present_archetypes <= set(train.index)   # never leak demo entities into test
    assert set(test.index).isdisjoint(ARCHETYPE_IDS)


def test_holdout_deterministic(feature_matrix):
    a1, b1 = split(feature_matrix, seed=7)
    a2, b2 = split(feature_matrix, seed=7)
    assert list(b1.index) == list(b2.index)


def test_psi_constant_feature_zero():
    assert psi(np.ones(100), np.ones(100)) == 0.0


def test_psi_identical_is_small():
    x = np.random.default_rng(0).normal(size=500)
    assert psi(x, x) < 0.01


def test_end_to_end_pipeline(feature_matrix):
    """Feature matrix -> split -> fit -> score -> metrics, all wired."""
    train, test = split(feature_matrix, seed=42)
    feats = [c for c in feature_matrix.columns if not c.startswith("label_")]
    scaler = StandardScaler().fit(train[feats])
    m = LogisticRegression(max_iter=1000, class_weight="balanced").fit(
        scaler.transform(train[feats]), train["label_default"])
    proba = m.predict_proba(scaler.transform(test[feats]))[:, 1]
    s = metrics.summary(test["label_default"], proba)
    assert 0.0 <= s["auc"] <= 1.0
    assert s["n"] == len(test)
