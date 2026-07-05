"""WP-5M — SentinelPulse detection-engine tests (Track 05).

Self-contained: a session fixture builds the fraud dataset into a temp dir and
fits the ``FraudEngine`` on it, so the suite never depends on a prior
``make data-gen``. Covers per-typology capture + hard-negative cleanliness,
citation integrity at the ML layer, ring recovery, blend/band determinism,
prefit round-trip + STATE_VERSION rejection, and the ground-truth-isolation
convention (the engine must never read the labels at score time).

Run ONLY this track:  .venv/bin/python -m pytest app/tracks/t05_fraud_intelligence -q
"""
from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd
import pytest

from app.tracks.t05_fraud_intelligence.data_gen import (ACCOUNTS_CSV,
                                                        GROUND_TRUTH_CSV,
                                                        TRANSACTIONS_CSV,
                                                        build_all)
from app.tracks.t05_fraud_intelligence.data_gen.typologies import ALL_TYPOLOGIES
from app.tracks.t05_fraud_intelligence.ml import model as M
from app.tracks.t05_fraud_intelligence.ml.model import (BAND_ALERT, BAND_REVIEW,
                                                        FraudEngine)
from app.tracks.t05_fraud_intelligence.ml.eval import fraud_metrics

TRACK_ROOT = Path(__file__).resolve().parents[1]
SCORE_COLS = ["account", "score", "band", "typology_component",
              "anomaly_component", "n_typologies", "typologies"]
# capture measured over accounts whose behaviour actually expresses the typology
# (the generator only runs its injectors on ROLE_MULE accounts; recruiter/cash-out
# accounts carry structural labels — device sharing is the one they truly express).
CAPTURE_SCOPE_MULE_ONLY = {"rapid_pass_through", "fan_in_fan_out",
                           "dormancy_burst", "new_account_velocity",
                           "kyc_income_mismatch", "round_amount_structuring",
                           "odd_hours"}


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def built(tmp_path_factory):
    d = tmp_path_factory.mktemp("t05_engine_data")
    tables = build_all(data_dir=d)
    engine = FraudEngine().fit(d)
    return d, tables, engine


@pytest.fixture(scope="session")
def engine(built):
    return built[2]


@pytest.fixture(scope="session")
def gt(built):
    g = built[1]["fraud_ground_truth"].copy()
    g["ring_id"] = g["ring_id"].fillna("").astype(str)
    g["typologies_expressed"] = g["typologies_expressed"].fillna("").astype(str)
    return g


def _expresses(gt, typ):
    return gt[gt.typologies_expressed.str.split(";").apply(lambda xs: typ in xs)]


# --------------------------------------------------------------------------- #
# score surface + bands
# --------------------------------------------------------------------------- #
def test_score_accounts_shape_and_range(engine):
    scored = engine.score_accounts()
    assert list(scored.columns) == SCORE_COLS
    assert len(scored) == 800
    assert scored.score.between(0.0, 100.0).all()
    assert set(scored.band) <= {"Alert", "Review", "Clear"}


def test_bands_deterministic_from_score(engine):
    scored = engine.score_accounts()
    for _, r in scored.iterrows():
        expect = "Alert" if r.score >= BAND_ALERT else (
            "Review" if r.score >= BAND_REVIEW else "Clear")
        assert r.band == expect, (r.account, r.score, r.band)


def test_refit_is_deterministic(built):
    d = built[0]
    a = FraudEngine().fit(d).score_accounts()
    b = FraudEngine().fit(d).score_accounts()
    pd.testing.assert_frame_equal(a, b)


# --------------------------------------------------------------------------- #
# per-typology capture + hard-negative cleanliness
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("typ", ALL_TYPOLOGIES)
def test_typology_captures_injected_accounts(engine, gt, typ):
    scope = _expresses(gt, typ)
    if typ in CAPTURE_SCOPE_MULE_ONLY:
        scope = scope[scope.role == "mule"]
    ids = scope.account_id.tolist()
    assert ids, typ
    fired = sum(any(h.name == typ for h in engine.typology_hits(a)) for a in ids)
    assert fired / len(ids) >= 0.7, (typ, fired, len(ids))


def test_hard_negatives_fire_no_typology_at_review(engine, gt):
    """No hard-negative fires any typology at Review strength (the differentiator)."""
    hn = gt[gt.is_hard_negative == "1"].account_id
    for a in hn:
        for h in engine.typology_hits(a):
            assert h.score < BAND_REVIEW, (a, h.name, h.score)


def test_hard_negatives_all_clear(engine, gt):
    scored = engine.score_accounts()
    hn = gt[gt.is_hard_negative == "1"].account_id
    for a in hn:
        assert scored.loc[a, "band"] == "Clear", (a, scored.loc[a, "score"])


# --------------------------------------------------------------------------- #
# citation integrity at the ML layer
# --------------------------------------------------------------------------- #
def test_every_hit_txn_id_exists(engine, built):
    tx_ids = set(built[1]["transactions"].txn_id.astype(str))
    for a in built[1]["accounts"].account_id:
        for h in engine.typology_hits(a):
            assert h.txn_ids, (a, h.name)  # a fired hit must carry >=1 citation
            assert set(h.txn_ids) <= tx_ids, (a, h.name)


def test_hit_dataclass_fields(engine, gt):
    aid = gt[gt.role == "mule"].account_id.iloc[0]
    hits = engine.typology_hits(aid)
    assert hits
    h = hits[0]
    assert isinstance(h.name, str) and 0.0 <= h.score <= 100.0
    assert isinstance(h.txn_ids, list) and isinstance(h.counterparties, list)
    assert isinstance(h.device_ids, list) and isinstance(h.plain_summary_inputs, dict)


# --------------------------------------------------------------------------- #
# ring expansion
# --------------------------------------------------------------------------- #
def test_ring_expansion_recovers_rings(engine, gt):
    rings = sorted(r for r in gt.ring_id.unique() if r)
    recovered = 0
    for rid in rings:
        members = set(gt[gt.ring_id == rid].account_id)
        seed = gt[(gt.ring_id == rid) & (gt.role == "mule")].account_id.iloc[0]
        found = set(engine.expand_ring(seed)["members"])
        if len(found & members) / len(members) >= 0.60:
            recovered += 1
    assert recovered >= 5, recovered


def test_expand_ring_shape_and_layout(engine, gt):
    seed = gt[gt.role == "mule"].account_id.iloc[0]
    res = engine.expand_ring(seed)
    assert set(res) == {"seed", "members", "edges", "layout"}
    assert res["seed"] == seed and seed in res["members"]
    assert set(res["layout"]) == set(res["members"])
    assert res["layout"][seed] == {"x": 0.0, "y": 0.0}
    mset = set(res["members"])
    for e in res["edges"]:
        assert e["source"] in mset and e["target"] in mset
        assert e["type"] in {"device", "transfer"}


# --------------------------------------------------------------------------- #
# eval headline (green on the synthetic desk)
# --------------------------------------------------------------------------- #
def test_eval_scorecard_headline(engine, built):
    m = fraud_metrics.evaluate(engine, built[0])
    assert m["rings_caught"] >= 5
    assert m["hard_negative_fp_rate"] == 0.0
    assert m["recall_at_alert"] >= 0.9
    assert m["precision_ring_at_alert"] >= 0.9


# --------------------------------------------------------------------------- #
# prefit round-trip + STATE_VERSION rejection
# --------------------------------------------------------------------------- #
def test_prefit_round_trip_and_version_guard(built, monkeypatch):
    d, _, engine = built
    pkl = d / "fraud_engine.pkl"
    monkeypatch.setattr(M, "DATA_DIR", d)
    monkeypatch.setattr(M, "ENGINE_PICKLE", pkl)
    engine.save(pkl)
    # fresh, current-version pickle loads and scores identically
    loaded = M._load_prefit()
    assert loaded is not None
    pd.testing.assert_frame_equal(loaded.score_accounts(), engine.score_accounts())
    # a pickle stamped with a wrong STATE_VERSION is rejected
    obj = pickle.loads(pkl.read_bytes())
    state = obj.__dict__.copy()
    state["_state_version"] = 999
    with open(pkl, "wb") as fh:
        pickle.dump(_Stamped(state), fh)
    assert M._load_prefit() is None


class _Stamped:
    """A pickled object carrying an arbitrary _state_version for guard testing."""
    def __init__(self, state):
        self.__dict__.update(state)


# --------------------------------------------------------------------------- #
# ground-truth isolation — the engine never reads the labels at score time
# --------------------------------------------------------------------------- #
def test_engine_scores_without_labels_file(built):
    """Fitting + scoring succeeds even when the labels CSV is absent."""
    d = built[0]
    scratch = d.parent / "no_labels"
    scratch.mkdir(exist_ok=True)
    for name in (ACCOUNTS_CSV, TRANSACTIONS_CSV):
        (scratch / name).write_bytes((d / name).read_bytes())
    assert not (scratch / GROUND_TRUTH_CSV).exists()
    eng = FraudEngine().fit(scratch)
    scored = eng.score_accounts()
    assert len(scored) == 800
    aid = scored.index[0]
    assert eng.typology_hits(aid) is not None
    assert "members" in eng.expand_ring(aid)


def test_serving_modules_never_reference_labels():
    """No serving module in ml/ (outside ml/eval) references the labels file."""
    ml_dir = TRACK_ROOT / "ml"
    offenders = []
    for py in ml_dir.rglob("*.py"):
        rel = py.relative_to(TRACK_ROOT).as_posix()
        if "/eval" in rel or "/tests/" in rel:
            continue
        text = py.read_text(encoding="utf-8")
        if "GROUND_TRUTH_CSV" in text or "fraud_ground_truth" in text:
            offenders.append(rel)
    assert not offenders, offenders
