"""Fast unit tests for the version-guarded prefit-pickle loader.

These never fit a real engine (that's ~7s). They exercise `_load_prefit`'s
version predicate + freshness plumbing with lightweight stand-in pickles, by
monkeypatching the module-level `DATA_DIR` / `ENGINE_PICKLE` to a tmp path.
"""
import os
import pickle
import time

import app.ml.engine as engine_mod
from app.ml.engine import ScoringEngine, _load_prefit


class _WrongVersion:
    """Stand-in engine pickle whose state-version doesn't match current code."""
    _state_version = -1


class _CurrentVersion:
    """Stand-in engine pickle stamped with the current state-version."""
    _state_version = ScoringEngine.STATE_VERSION


def _install(tmp_path, monkeypatch, obj):
    """Write `obj` as engine.pkl in a fresh tmp cohort dir and point the loader at it."""
    master = tmp_path / "msme_master.csv"
    master.write_text("entity_id,name\n")
    pkl = tmp_path / "engine.pkl"
    with open(pkl, "wb") as fh:
        pickle.dump(obj, fh)
    # Make the pickle strictly newer than the cohort so the mtime freshness
    # check passes and we isolate the version predicate.
    now = time.time()
    os.utime(master, (now - 100, now - 100))
    os.utime(pkl, (now, now))
    monkeypatch.setattr(engine_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(engine_mod, "ENGINE_PICKLE", pkl)


def test_load_prefit_rejects_missing_version(tmp_path, monkeypatch):
    # A dict has no `_state_version` -> a pre-upgrade pickle. Must refit.
    _install(tmp_path, monkeypatch, {"stale": True})
    assert _load_prefit() is None


def test_load_prefit_rejects_wrong_version(tmp_path, monkeypatch):
    _install(tmp_path, monkeypatch, _WrongVersion())
    assert _load_prefit() is None


def test_load_prefit_accepts_current_version(tmp_path, monkeypatch):
    # A fresh, correctly-stamped pickle loads (returns the object, not None).
    _install(tmp_path, monkeypatch, _CurrentVersion())
    loaded = _load_prefit()
    assert isinstance(loaded, _CurrentVersion)


def test_load_prefit_rejects_stale_mtime(tmp_path, monkeypatch):
    # Even a correctly-versioned pickle must refit if the cohort is newer.
    _install(tmp_path, monkeypatch, _CurrentVersion())
    pkl = tmp_path / "engine.pkl"
    master = tmp_path / "msme_master.csv"
    now = time.time()
    os.utime(pkl, (now - 100, now - 100))
    os.utime(master, (now, now))
    assert _load_prefit() is None


def test_getstate_stamps_version():
    # __getstate__ embeds the version and still drops shap (rebuilt on load).
    state = ScoringEngine().__getstate__()
    assert state["_state_version"] == ScoringEngine.STATE_VERSION
    assert state["shap"] is None
