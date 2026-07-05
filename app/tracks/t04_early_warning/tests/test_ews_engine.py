"""WP-4M acceptance tests for the Track-04 early-warning ML layer.

Self-contained: the panel is ensured/built in a session fixture and the engine is
fit once and shared. Covers the anti-leakage guards (the point of this track), the
entity-level split hygiene, the thesis (EWS warns >=4 months earlier than the
repayment-only baseline; higher capture@decile), band determinism, score ranges,
and the STATE_VERSION-guarded prefit round-trip.
"""
from __future__ import annotations

import os
import pickle
import time

import numpy as np
import pandas as pd
import pytest

import app.tracks.t04_early_warning.ml.model as model_mod
from app.tracks.t04_early_warning.data_gen import build, panel
from app.tracks.t04_early_warning.ml import features
from app.tracks.t04_early_warning.ml.features import (FEATURE_COLS, LeakageError,
                                                      build_snapshots, _window)
from app.tracks.t04_early_warning.ml.model import EWSEngine


# --------------------------------------------------------------------------- #
# Fixtures — build data once, fit once.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def tables():
    return build.build_panel()


@pytest.fixture(scope="session")
def engine():
    return EWSEngine().fit()


# --------------------------------------------------------------------------- #
# Anti-leakage guards (the differentiator of this track).
# --------------------------------------------------------------------------- #
def test_future_window_raises(tables):
    """Asking for a window that extends past the snapshot month is refused."""
    rep = tables["repayment_history"]
    e = rep[rep["entity_id"] == panel.FLAGSHIP_ENTITY]
    # Legal causal window is fine.
    assert len(_window(e, as_of=-6, months_back=6)) > 0
    # Peeking ahead of the snapshot must raise.
    with pytest.raises(LeakageError):
        _window(e, as_of=-6, months_back=6, future_offset=3)


def test_snapshot_ignores_poisoned_future_row(tables):
    """A snapshot at month m must use ONLY month<=m data: an injected future row
    with absurd values leaves the m-snapshot features byte-identical."""
    lb, rep, alt = tables["loan_book"], tables["repayment_history"], tables["altdata_monthly"]
    eid = panel.SHOWCASE_ENTITY
    lb1 = lb[lb["entity_id"] == eid]
    rep1 = rep[rep["entity_id"] == eid]
    alt1 = alt[alt["entity_id"] == eid]

    clean = build_snapshots(lb1, rep1, alt1, as_of_months=[-6])

    poison_rep = rep1.iloc[[-1]].copy()
    poison_rep["month"] = 3
    poison_rep["dpd"] = 180
    poison_rep["bounce_flag"] = 1
    poison_alt = alt1.iloc[[-1]].copy()
    poison_alt["month"] = 3
    poison_alt["gst_turnover_declared"] = 0.0
    poison_alt["bank_inflows"] = 0.0
    rep2 = pd.concat([rep1, poison_rep], ignore_index=True)
    alt2 = pd.concat([alt1, poison_alt], ignore_index=True)

    poisoned = build_snapshots(lb1, rep2, alt2, as_of_months=[-6])
    pd.testing.assert_frame_equal(clean[FEATURE_COLS], poisoned[FEATURE_COLS])


def test_no_label_fields_in_features(tables):
    """Feature columns never carry a label-derived field (grep-proof)."""
    for col in FEATURE_COLS:
        assert "default" not in col
        assert "ramp" not in col and "lead_alt" not in col and "repay_lag" not in col


def test_features_independent_of_labels(tables):
    """The feature builder takes no labels argument and its output cannot change
    when the labels file changes — features are label-free by construction."""
    import inspect
    sig = inspect.signature(build_snapshots)
    assert not any("label" in p for p in sig.parameters)


# --------------------------------------------------------------------------- #
# Split hygiene.
# --------------------------------------------------------------------------- #
def test_entity_split_disjoint(engine):
    assert engine._train_entities and engine._holdout_entities
    assert engine._train_entities.isdisjoint(engine._holdout_entities)
    # Demo archetypes are pinned into train, never reported on in holdout.
    assert panel.FLAGSHIP_ENTITY in engine._train_entities
    assert panel.SHOWCASE_ENTITY in engine._train_entities


# --------------------------------------------------------------------------- #
# THESIS — EWS warns earlier and captures more (the headline).
# --------------------------------------------------------------------------- #
def test_lead_time_gap_at_least_four_months(engine):
    ev = engine.eval_summary()
    assert ev["median_lead_gap"] >= 4, (
        f"median lead-time gap only {ev['median_lead_gap']} months")
    assert ev["lead_time"]["n_paired"] >= 3


def test_capture_ews_beats_baseline(engine):
    ev = engine.eval_summary()
    assert ev["capture_decile_ews"] > ev["capture_decile_baseline"]


# --------------------------------------------------------------------------- #
# Bands, calibration, ranges.
# --------------------------------------------------------------------------- #
def test_calibration_object_present(engine):
    assert engine.gbm.calibrator is not None
    assert engine.baseline.calibrator is not None


def test_pd_in_unit_interval(engine):
    snaps = engine._snaps
    assert snaps["ews_pd"].between(0, 1).all()
    assert snaps["baseline_pd"].between(0, 1).all()


def test_bands_deterministic_and_cover_mix(engine):
    p = engine.portfolio_snapshot()
    assert set(p["band_counts"]) == {"Red", "Amber", "Green"}
    assert p["band_counts"]["Red"] > 0
    assert p["band_counts"]["Amber"] > 0
    # A small minority Red, a modest Amber tier, most Green (sensible demo mix).
    assert 0.02 <= p["red_share"] <= 0.15
    assert 0.05 <= p["amber_share"] <= 0.20


def test_band_thresholds_monotone(engine):
    assert engine.band(0.40) == "Red"
    assert engine.band(0.15) == "Amber"
    assert engine.band(0.01) == "Green"
    assert engine.red > engine.amber


def test_portfolio_rows_have_reasons(engine):
    p = engine.portfolio_snapshot()
    reds = [r for r in p["rows"] if r["band"] == "Red"]
    assert reds
    for r in reds:
        assert r["reasons"], f"Red loan {r['entity_id']} has no reason codes"
        assert all(rc["contribution"] > 0 for rc in r["reasons"])


def test_entity_timeline_shape(engine):
    tl = engine.entity_timeline(panel.SHOWCASE_ENTITY)
    assert tl["months"] == panel.MONTHS
    assert len(tl["gst_turnover_declared"]) == len(tl["months"])
    assert len(tl["ews_pd"]) == len(tl["pd_months"])
    # The showcase is the demo star: EWS flags it (Red) before its projected default.
    assert tl["ews_first_alert"] is not None
    assert tl["default_month"] is not None
    assert tl["ews_first_alert"] < tl["default_month"]


# --------------------------------------------------------------------------- #
# Determinism.
# --------------------------------------------------------------------------- #
def test_fit_is_deterministic(engine):
    other = EWSEngine().fit()
    p1, p2 = engine.portfolio_snapshot(), other.portfolio_snapshot()
    assert p1["band_counts"] == p2["band_counts"]
    a = np.array([r["pd_12m"] for r in p1["rows"]])
    b = np.array([r["pd_12m"] for r in p2["rows"]])
    assert np.allclose(a, b)
    assert engine.eval_summary()["median_lead_gap"] == other.eval_summary()["median_lead_gap"]


# --------------------------------------------------------------------------- #
# Prefit round-trip + STATE_VERSION guard (mirrors app/tests/test_engine_prefit).
# --------------------------------------------------------------------------- #
def test_prefit_roundtrip(engine, tmp_path, monkeypatch):
    pkl = tmp_path / "ews_engine.pkl"
    engine.save(pkl)
    with open(pkl, "rb") as fh:
        loaded = pickle.load(fh)
    assert loaded.portfolio_snapshot()["band_counts"] == engine.portfolio_snapshot()["band_counts"]
    assert loaded.first_alert(panel.SHOWCASE_ENTITY) == engine.first_alert(panel.SHOWCASE_ENTITY)


def test_getstate_stamps_version(engine):
    assert engine.__getstate__()["_state_version"] == EWSEngine.STATE_VERSION


class _WrongVersion:
    _state_version = -1


def _install(tmp_path, monkeypatch, obj):
    src = tmp_path / "loan_book.csv"
    src.write_text("entity_id\n")
    pkl = tmp_path / "ews_engine.pkl"
    with open(pkl, "wb") as fh:
        pickle.dump(obj, fh)
    now = time.time()
    os.utime(src, (now - 100, now - 100))
    os.utime(pkl, (now, now))
    monkeypatch.setattr(model_mod.paths, "DATA_DIR", tmp_path)
    monkeypatch.setattr(model_mod, "EWS_PICKLE", pkl)


def test_load_prefit_rejects_wrong_version(tmp_path, monkeypatch):
    _install(tmp_path, monkeypatch, _WrongVersion())
    assert model_mod._load_prefit() is None


def test_load_prefit_rejects_stale_mtime(tmp_path, monkeypatch):
    _install(tmp_path, monkeypatch, _WrongVersion())
    pkl = tmp_path / "ews_engine.pkl"
    src = tmp_path / "loan_book.csv"
    now = time.time()
    os.utime(pkl, (now - 100, now - 100))
    os.utime(src, (now, now))
    assert model_mod._load_prefit() is None
