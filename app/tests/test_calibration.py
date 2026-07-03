"""Probability calibration: the machinery is sound and the displayed PD is honest."""
import numpy as np
import pandas as pd
import pytest

from app.ml.eval import metrics
from app.ml.models.calibration import PostHocCalibrator, out_of_fold_pd


def test_brier_and_ece_perfect_predictions():
    y = np.array([0, 1, 0, 1, 1, 0])
    assert metrics.brier(y, y.astype(float)) == pytest.approx(0.0)
    assert metrics.ece(y, y.astype(float)) == pytest.approx(0.0)


def test_brier_bounds_and_worst_case():
    y = np.array([0, 1])
    assert metrics.brier(y, np.array([1.0, 0.0])) == pytest.approx(1.0)  # fully wrong
    assert 0.0 <= metrics.ece(y, np.array([0.5, 0.5])) <= 1.0


def test_out_of_fold_returns_none_when_too_few_events():
    X = pd.DataFrame({"a": np.arange(20.0)})
    y = np.array([0] * 19 + [1])          # a single positive -> cannot stratify
    assert out_of_fold_pd(lambda: _DummyEstimator(), X, y) is None


def test_calibrator_identity_when_no_oof():
    cal = PostHocCalibrator().fit(None, np.array([0, 1, 0, 1]))
    assert not cal.fitted and cal.kind_ == "identity"
    raw = np.array([0.1, 0.9])
    assert np.allclose(cal.transform(raw), raw)


def test_sigmoid_calibration_reduces_ece_on_overconfident_scores():
    rng = np.random.default_rng(0)
    n = 2000
    # True event probability 0.3; raw score is a pushed-to-extremes (overconfident)
    # version of it -> poorly calibrated, good ranking.
    y = (rng.random(n) < 0.3).astype(int)
    base = np.where(y == 1, rng.beta(6, 4, n), rng.beta(4, 6, n))   # separable-ish
    raw = np.clip(base ** 3 / (base ** 3 + (1 - base) ** 3), 1e-4, 1 - 1e-4)  # sharpened
    cal = PostHocCalibrator(method="sigmoid").fit(raw, y)
    assert cal.kind_ == "sigmoid"
    out = cal.transform(raw)
    assert out.min() >= 0.0 and out.max() <= 1.0
    # Calibration should not destroy ranking and should lower calibration error.
    assert metrics.ece(y, out) <= metrics.ece(y, raw) + 1e-9
    assert metrics.brier(y, out) <= metrics.brier(y, raw) + 1e-9


def test_auto_picks_isotonic_only_with_enough_events():
    rng = np.random.default_rng(1)
    y = (rng.random(400) < 0.5).astype(int)          # ~200 per class
    raw = np.clip(0.2 + 0.6 * y + rng.normal(0, 0.1, 400), 1e-3, 1 - 1e-3)
    assert PostHocCalibrator(method="auto").fit(raw, y).kind_ == "isotonic"
    # Rare-event cohort should fall back to the more data-frugal sigmoid.
    y2 = np.array([0] * 380 + [1] * 20)
    raw2 = np.clip(rng.random(400), 1e-3, 1 - 1e-3)
    assert PostHocCalibrator(method="auto").fit(raw2, y2).kind_ == "sigmoid"


def test_scorecard_exposes_calibration_and_valid_pd(feature_matrix):
    from app.ml.models.scorecard import WOEScorecard
    fm = feature_matrix
    X = fm[[c for c in fm.columns if c not in ("label_default", "label_fraud")]]
    y = fm["label_default"].to_numpy()
    sc = WOEScorecard().fit(X, y)
    assert isinstance(sc.calibration_kind, str)
    pd_cal, pd_raw = sc.predict_pd(X), sc.predict_pd_raw(X)
    assert pd_cal.shape == pd_raw.shape == (len(X),)
    assert float(pd_cal.min()) >= 0.0 and float(pd_cal.max()) <= 1.0


class _DummyEstimator:
    def fit(self, X, y):
        self._p = float(np.mean(y)); return self
    def predict_proba(self, X):
        p = np.full(len(X), self._p)
        return np.column_stack([1 - p, p])
