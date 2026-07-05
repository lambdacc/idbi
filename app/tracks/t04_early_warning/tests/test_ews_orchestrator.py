"""WP-4A backend tests — the monitoring orchestrator (`service.py`).

Covers the `MonitoringRun` / `CaseDetail` shapes, that every watchlist row carries
at least one plain-language reason and an RBI-EWS action, that the case markers are
ordered (EWS alert <= baseline alert <= projected default) for defaulters, and that
the flagship showcase borrower produces the EWS-early / baseline-late money-shot
story. Also asserts all user-facing copy originates in the backend module.
"""
from __future__ import annotations

import pytest

from app.tracks.t04_early_warning.ml.model import EWSEngine
from app.tracks.t04_early_warning.service import (ACTIONS, SHOWCASE_ENTITY,
                                                  CaseDetail, MonitoringRun,
                                                  case_detail, run_monitoring)


@pytest.fixture(scope="module")
def engine():
    return EWSEngine().fit()


@pytest.fixture(scope="module")
def run(engine):
    return run_monitoring(engine)


# --------------------------------------------------------------- MonitoringRun
def test_monitoring_run_shape(run):
    assert isinstance(run, MonitoringRun)
    assert run.n_loans > 0
    assert run.exposure_total > 0
    assert set(run.band_counts) >= {"Red", "Amber", "Green"}
    assert run.red_count + run.amber_count + run.green_count == sum(run.band_counts.values())
    assert run.kpis and all(k.value for k in run.kpis)
    assert run.stages and len(run.stages) == 5


def test_watchlist_rows_have_reason_and_action(run):
    assert run.watchlist, "expected at least one flagged borrower"
    for r in run.watchlist:
        assert r.band in ("Red", "Amber")
        assert r.reasons, f"{r.entity_id} has no plain-language reason"
        assert r.action == ACTIONS[r.band]["action"]
        assert r.rationale.endswith(".")
        assert r.exposure_str.startswith("₹")


def test_watchlist_ranked_red_before_amber(run):
    order = {"Red": 0, "Amber": 1}
    keys = [(order[r.band], -r.pd_12m) for r in run.watchlist]
    assert keys == sorted(keys), "watchlist not ranked Red-first then by PD"


def test_exposure_at_risk_matches_flagged(run):
    assert run.exposure_at_risk == pytest.approx(
        sum(r.exposure for r in run.watchlist), rel=1e-6)


# ------------------------------------------------------------------ CaseDetail
def test_case_detail_shape(engine, run):
    case = case_detail(engine, run.watchlist[0].entity_id)
    assert isinstance(case, CaseDetail)
    assert case.timeline["months"], "timeline carries no months"
    assert case.headline and case.verdict
    assert case.action == ACTIONS[case.band]["action"]
    assert case.technique_algorithm  # technical disclosure present


def test_case_markers_ordered_for_defaulters(engine, run):
    """For any defaulted entity with alerts, EWS alert <= baseline alert <= default."""
    seen = 0
    for r in run.watchlist:
        case = case_detail(engine, r.entity_id)
        if not case.is_defaulter:
            continue
        seen += 1
        ews, base, dm = case.ews_first_alert, case.baseline_first_alert, case.default_month
        if ews is not None and dm is not None:
            assert ews <= dm, f"{r.entity_id}: EWS alert after default"
        if ews is not None and base is not None:
            assert ews <= base, f"{r.entity_id}: EWS alert later than baseline"
    assert seen >= 1, "no defaulted watchlist entity to check ordering"


def test_showcase_money_shot(engine):
    """The flagship borrower: EWS fired early, baseline never fired, default projected
    ahead — and the narrative says so, in plain language."""
    case = case_detail(engine, SHOWCASE_ENTITY)
    assert case.is_defaulter
    assert case.ews_first_alert is not None, "EWS should have alerted on the showcase"
    assert case.baseline_first_alert is None, "baseline should NOT fire on the showcase"
    assert case.default_month is not None and case.default_month > case.ews_first_alert
    assert case.lead_time and case.lead_time > 0
    # Narrative asserts the mechanism honestly (projected, not observed).
    low = case.verdict.lower()
    assert "red" in low and "baseline" in low
    assert "project" in low  # projected default, never presented as observed


# ------------------------------------------------- copy originates in backend
def test_pages_do_not_compose_narrative():
    """Guardrail: the page modules render backend-composed strings; they must not
    build narrative/action copy with their own f-strings (spot-check)."""
    from pathlib import Path
    pages = Path(__file__).resolve().parents[1] / "pages"
    for name in ("portfolio_overview.py", "watchlist.py"):
        src = (pages / name).read_text()
        # No page should hand-write an RBI action label or a verdict sentence.
        for banned in ("Review limit", "Enhanced monitoring", "moved to Red",
                       "repayment-only baseline"):
            assert banned not in src, f"{name} composes narrative copy: {banned!r}"
