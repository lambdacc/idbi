"""WP-5A — SentinelPulse case-orchestrator tests (Track 05).

Self-contained: builds the fraud dataset into a temp dir and fits the engine on
it (never depends on a prior build). Covers the five-stage decomposition, the
CITATION GATE (every ground cites a real transaction; an uncited ground raises),
hard-negative clearance, ring-stage payload, backend-owned narrative, the desk
snapshot, and the deterministic audit trail.

Run ONLY this track:  .venv/bin/python -m pytest app/tracks/t05_fraud_intelligence -q
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.tracks.t05_fraud_intelligence import case_orchestrator as co
from app.tracks.t05_fraud_intelligence.case_orchestrator import (CitationError,
                                                                 Ground)
from app.tracks.t05_fraud_intelligence.data_gen import (GROUND_TRUTH_CSV,
                                                        build_all)
from app.tracks.t05_fraud_intelligence.ml.model import FraudEngine
from app.tracks.t05_fraud_intelligence.session import append_audit

_STAGE_ORDER = ["triage", "evidence", "network", "adjudication", "casefile"]


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="module")
def built(tmp_path_factory):
    d = tmp_path_factory.mktemp("t05_case_data")
    tables = build_all(data_dir=d)
    engine = FraudEngine().fit(d)
    return d, tables, engine


@pytest.fixture(scope="module")
def engine(built):
    return built[2]


@pytest.fixture(scope="module")
def data_dir(built):
    return built[0]


@pytest.fixture(scope="module")
def gt(built):
    g = built[1]["fraud_ground_truth"].copy()
    g["ring_id"] = g["ring_id"].fillna("").astype(str)
    return g


@pytest.fixture(scope="module")
def txn_ids(built):
    return set(built[1]["transactions"].txn_id.astype(str))


def _investigate(engine, aid, data_dir):
    return co.investigate(engine, aid, data_dir=data_dir)


def _ring_seed(engine, gt):
    """A ring mule (deterministic desk default) for the network-payload test."""
    return co.desk_snapshot(engine)["default_case"]


# --------------------------------------------------------------------------- #
# stage decomposition
# --------------------------------------------------------------------------- #
def test_case_has_five_stages_in_order(engine, gt, data_dir):
    cf = _investigate(engine, _ring_seed(engine, gt), data_dir)
    assert [s.key for s in cf.stages] == _STAGE_ORDER
    assert [s.index for s in cf.stages] == [1, 2, 3, 4, 5]


def test_stage_dataclass_reused(engine, gt, data_dir):
    from app.backend.services.pipeline_orchestrator import Stage
    cf = _investigate(engine, _ring_seed(engine, gt), data_dir)
    assert all(isinstance(s, Stage) for s in cf.stages)


# --------------------------------------------------------------------------- #
# citation gate — the differentiator
# --------------------------------------------------------------------------- #
def test_uncited_ground_raises():
    """Constructing a ground of suspicion with no citing txn_id RAISES."""
    with pytest.raises(CitationError):
        Ground(typology="x", label="X", plain_label="x", plain="claim", txn_ids=[])


def test_a_cited_ground_is_allowed():
    g = Ground(typology="x", label="X", plain_label="x", plain="claim",
               txn_ids=["TXN0000001"])
    assert g.txn_ids == ["TXN0000001"]


def test_every_ground_cites_real_transactions(engine, gt, txn_ids, data_dir):
    """Across the whole flagged desk, every ground's txn_ids exist in the ledger."""
    for aid in co.desk_snapshot(engine)["queue"][:40]:
        cf = _investigate(engine, aid["account"], data_dir)
        for g in cf.grounds:
            assert g.txn_ids, (aid["account"], g.typology)
            assert set(g.txn_ids) <= txn_ids, (aid["account"], g.typology)


def test_evidence_stage_findings_all_from_grounds(engine, gt, data_dir):
    cf = _investigate(engine, _ring_seed(engine, gt), data_dir)
    ev = cf.stage("evidence")
    # the evidence stage payload only carries grounds that cite transactions
    assert all(g["txn_ids"] for g in ev.data["grounds"])


# --------------------------------------------------------------------------- #
# hard-negative clearance
# --------------------------------------------------------------------------- #
def test_hard_negatives_adjudicate_to_clear(engine, gt, data_dir):
    hn = gt[gt.is_hard_negative.astype(str) == "1"].account_id.tolist()
    assert hn
    for aid in hn:
        cf = _investigate(engine, aid, data_dir)
        assert cf.recommendation == co.REC_CLEAR, (aid, cf.recommendation)
        assert cf.band == "Clear"
        joined = " ".join(cf.rationale).lower()
        assert "gig" in joined and "no " in joined, (aid, cf.rationale)


# --------------------------------------------------------------------------- #
# ring stage payload
# --------------------------------------------------------------------------- #
def test_ring_stage_has_at_least_three_nodes(engine, gt, data_dir):
    cf = _investigate(engine, _ring_seed(engine, gt), data_dir)
    net = cf.stage("network").data
    assert net["ring"]["seed"] == cf.account_id
    assert len(net["ring"]["members"]) >= 3
    assert net["ring"]["layout"][cf.account_id] == {"x": 0.0, "y": 0.0}
    assert set(net["roles"].values()) & {"this"}


def test_alert_case_freezes_and_files_str(engine, gt, data_dir):
    cf = _investigate(engine, _ring_seed(engine, gt), data_dir)
    assert cf.band == "Alert"
    assert cf.recommendation == co.REC_FREEZE
    assert cf.grounds  # an alert case must carry evidenced grounds


# --------------------------------------------------------------------------- #
# narrative originates in the backend
# --------------------------------------------------------------------------- #
def test_all_stages_carry_backend_narrative(engine, gt, data_dir):
    cf = _investigate(engine, _ring_seed(engine, gt), data_dir)
    for s in cf.stages:
        assert s.headline and isinstance(s.headline, str)
        assert s.findings and all(f["text"] for f in s.findings)
        assert s.technique and s.technique.get("plain") and s.technique.get("benefit")
    assert cf.rationale and all(isinstance(x, str) and x for x in cf.rationale)
    for g in cf.grounds:
        assert g.plain and g.label and g.plain_label


# --------------------------------------------------------------------------- #
# desk snapshot
# --------------------------------------------------------------------------- #
def test_desk_snapshot_shape(engine):
    snap = co.desk_snapshot(engine)
    assert {"kpis", "queue", "typology_distribution", "why_track", "scope_note",
            "default_case", "hard_negative"} <= set(snap)
    assert len(snap["kpis"]) == 4
    assert len(snap["why_track"]) == 3
    assert all(q["band"] in ("Alert", "Review") for q in snap["queue"])
    assert snap["default_case"] and snap["hard_negative"]
    assert snap["default_case"] != snap["hard_negative"]


def test_default_case_is_alert_hard_negative_is_clear(engine):
    snap = co.desk_snapshot(engine)
    scored = engine.score_accounts()
    assert scored.loc[snap["default_case"], "band"] == "Alert"
    assert scored.loc[snap["hard_negative"], "band"] == "Clear"


# --------------------------------------------------------------------------- #
# audit trail — deterministic, ordinal, no wall-clock
# --------------------------------------------------------------------------- #
def test_audit_trail_orders_two_decisions():
    audit: list = []
    append_audit(audit, "ACC1", "Approved", co.REC_FREEZE)
    append_audit(audit, "ACC1", "Overridden", co.REC_FREEZE, note="disagree")
    assert [e["n"] for e in audit] == [1, 2]
    assert [e["action"] for e in audit] == ["Approved", "Overridden"]
    assert audit[1]["note"] == "disagree"
    # entries carry no wall-clock timestamp (tests must stay deterministic)
    assert all("time" not in e and "timestamp" not in e for e in audit)


# --------------------------------------------------------------------------- #
# module boundary — the orchestrator never reads the labels file
# --------------------------------------------------------------------------- #
def test_orchestrator_never_reads_ground_truth():
    from pathlib import Path
    src = Path(co.__file__).read_text(encoding="utf-8")
    assert GROUND_TRUTH_CSV not in src
    assert "fraud_ground_truth" not in src
