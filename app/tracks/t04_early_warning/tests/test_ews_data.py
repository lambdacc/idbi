"""WP-4D acceptance tests for the Track-04 early-warning panel data.

Self-contained: the panel is built in-memory in a session fixture (no dependence
on a `make data-gen` run). Covers schema/ranges, determinism (identical
checksums on re-build), the encoded thesis (alt-data leads repayment), the
default-rate envelope, and Track-03 cross-source consistency.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd
import pytest

from app.data_gen.build_dataset import build_profiles
from app.tracks.t04_early_warning.data_gen import build, panel, paths


# --------------------------------------------------------------------------- #
# Fixtures.
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def tables():
    return build.build_panel()


@pytest.fixture(scope="session")
def profiles_by_id():
    profs = build_profiles(n_random=panel.N_RANDOM, base_seed=panel.BASE_SEED)
    return {p.entity_id: p for p in profs}


# --------------------------------------------------------------------------- #
# Schema / dtype / ranges.
# --------------------------------------------------------------------------- #
def test_all_tables_present_with_exact_columns(tables):
    assert set(tables) == set(panel.SCHEMAS)
    for name, cols in panel.SCHEMAS.items():
        assert list(tables[name].columns) == cols, f"{name}: column mismatch"


def test_paths_constants_match_tables():
    # The Wave-2 ML agent locates CSVs via these constants.
    assert paths.DATA_DIR.name == "data"
    assert set(paths.CSV_PATHS) == set(panel.SCHEMAS)


def test_panel_shape_and_month_index(tables):
    rep, alt = tables["repayment_history"], tables["altdata_monthly"]
    n_loans = len(tables["loan_book"])
    assert n_loans > 150            # ~60% of the cohort carry a loan
    assert sorted(rep["month"].unique().tolist()) == panel.MONTHS
    assert sorted(alt["month"].unique().tolist()) == panel.MONTHS
    # One 24-month row block per borrower in each panel table.
    assert len(rep) == n_loans * panel.PANEL_MONTHS
    assert len(alt) == n_loans * panel.PANEL_MONTHS


def test_loan_book_ranges(tables):
    lb = tables["loan_book"]
    assert lb["entity_id"].is_unique
    assert set(lb["product"]) <= {"term", "cc", "od"}
    assert set(lb["status"]) <= {"regular", "watch", "npa", "closed"}
    assert (lb["sanctioned_limit"] > 0).all()
    assert lb["interest_rate"].between(5, 25).all()
    assert (lb["sanction_month"] < 0).all()


def test_repayment_ranges(tables):
    rep = tables["repayment_history"]
    assert rep["dpd"].between(0, 180).all()
    assert set(rep["bounce_flag"]) <= {0, 1}
    assert (rep["emi_due"] >= 0).all()
    assert (rep["emi_paid"] >= 0).all()
    assert (rep["overdue_amount"] >= 0).all()
    util = rep["utilization_pct"].dropna()
    assert util.between(0, 100).all()


def test_altdata_ranges(tables):
    alt = tables["altdata_monthly"]
    assert (alt["gst_turnover_declared"] >= 0).all()
    assert set(alt["gst_filed_on_time"]) <= {0, 1}
    assert (alt["bank_inflows"] >= 0).all()
    assert (alt["upi_txn_count"] >= 0).all()
    assert (alt["epfo_employee_count"] >= 0).all()
    assert (alt["energy_units"] >= 0).all()


# --------------------------------------------------------------------------- #
# Determinism.
# --------------------------------------------------------------------------- #
def test_rebuild_is_byte_identical(tables):
    again = build.build_panel()
    for name in panel.SCHEMAS:
        h1 = hashlib.md5(tables[name].to_csv(index=False).encode()).hexdigest()
        h2 = hashlib.md5(again[name].to_csv(index=False).encode()).hexdigest()
        assert h1 == h2, f"{name}: non-deterministic build"


# --------------------------------------------------------------------------- #
# Default-rate envelope + label hygiene.
# --------------------------------------------------------------------------- #
def test_default_rate_in_band(tables):
    lab = tables["default_labels"]
    rate = lab["is_defaulter"].mean()
    assert 0.10 <= rate <= 0.18, f"default rate {rate:.3f} outside 10-18%"
    # A meaningful minority of defaults are observed inside the panel (eval),
    # the rest are live-deteriorating watchlist cases.
    observed = lab["default_observed"].sum()
    total = lab["is_defaulter"].sum()
    assert 0.15 * total <= observed <= 0.55 * total


def test_no_default_among_top_quartile_health(tables, profiles_by_id):
    lab = tables["default_labels"]
    defaulters = lab.loc[lab["is_defaulter"] == 1, "entity_id"]
    healths = {profiles_by_id[e].true_health for e in defaulters}
    assert "healthy" not in healths, "healthy borrowers must not default"


def test_status_matches_labels(tables):
    lb = tables["loan_book"].set_index("entity_id")
    lab = tables["default_labels"].set_index("entity_id")
    # Every observed default is NPA; every live defaulter is on the watchlist.
    obs = lab.index[lab["default_observed"] == 1]
    assert (lb.loc[obs, "status"] == "npa").all()
    live = lab.index[(lab["is_defaulter"] == 1) & (lab["default_observed"] == 0)]
    assert (lb.loc[live, "status"] == "watch").all()


# --------------------------------------------------------------------------- #
# THESIS: alt-data deteriorates several months before repayment.
# --------------------------------------------------------------------------- #
def _first_month(series_months: pd.Series):
    return int(series_months.min()) if len(series_months) else None


def test_altdata_drop_precedes_dpd_by_four_months(tables):
    rep, alt = tables["repayment_history"], tables["altdata_monthly"]
    lab = tables["default_labels"]
    defaulters = lab.loc[lab["is_defaulter"] == 1, "entity_id"].tolist()

    gaps = []
    for eid in defaulters:
        r = rep[rep["entity_id"] == eid]
        a = alt[alt["entity_id"] == eid]
        first_dpd = _first_month(r.loc[r["dpd"] > 0, "month"])
        baseline = a.loc[a["month"] <= -18, "gst_turnover_declared"].mean()
        first_drop = _first_month(a.loc[a["gst_turnover_declared"] < 0.75 * baseline, "month"])
        if first_dpd is not None and first_drop is not None:
            gaps.append(first_dpd - first_drop)

    assert len(gaps) >= 8, "too few defaulters exhibit both events to test the thesis"
    gaps = np.array(gaps)
    assert np.median(gaps) >= 4, f"median alt-lead only {np.median(gaps)} months"
    assert (gaps > 0).all(), "alt-data drop must precede DPD for every case"


def test_showcase_is_live_deteriorating(tables):
    """The demo star sags on alt-data but has NOT yet gone NPA (watchlist)."""
    lab = tables["default_labels"].set_index("entity_id")
    assert panel.SHOWCASE_ENTITY in lab.index
    assert lab.loc[panel.SHOWCASE_ENTITY, "is_defaulter"] == 1
    assert lab.loc[panel.SHOWCASE_ENTITY, "default_observed"] == 0
    alt = tables["altdata_monthly"]
    a = alt[alt["entity_id"] == panel.SHOWCASE_ENTITY].sort_values("month")
    early = a.loc[a["month"] <= -18, "gst_turnover_declared"].mean()
    late = a.loc[a["month"] >= -2, "gst_turnover_declared"].mean()
    assert late < 0.85 * early, "showcase GST turnover should be visibly sagging"


# --------------------------------------------------------------------------- #
# Track-03 consistency: recent-12m GST ≈ the cross-sectional declared turnover.
# --------------------------------------------------------------------------- #
def test_flagship_gst_consistent_with_track03(tables, profiles_by_id):
    alt = tables["altdata_monthly"]
    a = alt[alt["entity_id"] == panel.FLAGSHIP_ENTITY]
    recent_12m = a.loc[a["month"] >= -11, "gst_turnover_declared"].sum()
    declared = profiles_by_id[panel.FLAGSHIP_ENTITY].declared_turnover
    ratio = recent_12m / declared
    assert 0.85 <= ratio <= 1.15, f"flagship GST/declared ratio {ratio:.3f} off"

    # The flagship is a healthy, non-defaulting account.
    lab = tables["default_labels"].set_index("entity_id")
    assert lab.loc[panel.FLAGSHIP_ENTITY, "is_defaulter"] == 0
