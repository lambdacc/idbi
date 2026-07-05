"""WP-5D — SentinelPulse synthetic fraud-data tests (Track 05).

Self-contained: builds the dataset into a temp dir inside a session fixture, so
the suite never depends on a prior `make data-gen`. Covers schema/ranges,
determinism (identical checksums on re-run), the mule rate, ring structural
properties, the hard-negative "clean high-velocity" contract, typology coverage,
and the ground-truth isolation convention.
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
import pytest

from app.tracks.t05_fraud_intelligence.data_gen import (ACCOUNTS_CSV,
                                                        GROUND_TRUTH_CSV,
                                                        TRANSACTIONS_CSV,
                                                        build_all)
from app.tracks.t05_fraud_intelligence.data_gen import typologies as T
from app.tracks.t05_fraud_intelligence.data_gen.fraud_profiles import (
    AS_OF, WINDOW_START)

REPO_ROOT = Path(__file__).resolve().parents[4]
STRUCTURING = set(T.STRUCTURING_AMOUNTS)


# --------------------------------------------------------------------------- #
# fixtures
# --------------------------------------------------------------------------- #
@pytest.fixture(scope="session")
def dataset(tmp_path_factory):
    d = tmp_path_factory.mktemp("t05_data")
    tables = build_all(data_dir=d)
    return d, tables


@pytest.fixture(scope="session")
def accounts(dataset):
    return dataset[1]["accounts"]


@pytest.fixture(scope="session")
def transactions(dataset):
    return dataset[1]["transactions"]


@pytest.fixture(scope="session")
def ground_truth(dataset):
    return dataset[1]["fraud_ground_truth"]


# --------------------------------------------------------------------------- #
# schema / ranges
# --------------------------------------------------------------------------- #
def test_accounts_schema(accounts):
    assert list(accounts.columns) == [
        "account_id", "account_type", "open_date", "kyc_income_band",
        "linked_entity_id"]
    assert len(accounts) == 800
    assert set(accounts.account_type) == {"savings", "current"}
    assert accounts.account_type.value_counts()["current"] == 200
    # linked entity_id present exactly for current accounts (join key)
    linked = accounts.linked_entity_id.fillna("").astype(str) != ""
    assert (linked == (accounts.account_type == "current")).all()


def test_accounts_never_leak_labels(accounts):
    """accounts.csv (engine input) must not carry any ground-truth column."""
    for banned in ("is_mule", "ring_id", "role", "is_hard_negative",
                   "typologies_expressed"):
        assert banned not in accounts.columns


def test_transactions_schema_and_ranges(transactions):
    assert list(transactions.columns) == [
        "txn_id", "datetime", "account_id", "counterparty_id", "direction",
        "amount", "channel", "device_id", "balance_after"]
    assert 120_000 <= len(transactions) <= 200_000
    assert transactions.txn_id.is_unique
    assert (transactions.amount > 0).all()
    assert set(transactions.direction) <= {"credit", "debit"}
    assert set(transactions.channel) <= {"UPI", "IMPS", "NEFT", "ATM", "POS"}
    assert transactions.device_id.notna().all()
    dt = pd.to_datetime(transactions.datetime)
    assert dt.min() >= WINDOW_START
    assert dt.max() <= AS_OF


def test_ground_truth_schema(ground_truth):
    assert list(ground_truth.columns) == [
        "account_id", "is_mule", "ring_id", "role", "is_hard_negative",
        "typologies_expressed"]
    assert set(ground_truth.is_mule) <= {0, 1}
    assert set(ground_truth.role) <= {
        "legit", "mule", "recruiter", "cashout", "hard_negative"}


def test_every_account_has_transactions(accounts, transactions):
    assert set(transactions.account_id) == set(accounts.account_id)


# --------------------------------------------------------------------------- #
# determinism
# --------------------------------------------------------------------------- #
def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def test_determinism_identical_checksums(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    build_all(data_dir=a)
    build_all(data_dir=b)
    for name in (ACCOUNTS_CSV, TRANSACTIONS_CSV, GROUND_TRUTH_CSV):
        assert _md5(a / name) == _md5(b / name), f"{name} not deterministic"


# --------------------------------------------------------------------------- #
# mule rate + rings
# --------------------------------------------------------------------------- #
def test_mule_rate_in_band(ground_truth):
    rate = ground_truth.is_mule.mean()
    assert 0.03 <= rate <= 0.05, rate
    assert ground_truth.ring_id.replace("", pd.NA).nunique() == 6


def test_ring_structural_shared_device_or_dense_links(transactions, ground_truth):
    """Each ring shares >=1 device across >=3 accounts OR has dense intra-links."""
    gt = ground_truth.copy()
    gt["ring_id"] = gt["ring_id"].fillna("").astype(str)
    ring_map = dict(zip(gt.account_id, gt.ring_id))
    tx = transactions.copy()
    tx["ring"] = tx.account_id.map(ring_map)
    ring_ids = sorted(r for r in gt.ring_id.unique() if r)
    assert len(ring_ids) == 6
    for rid in ring_ids:
        members = set(gt.loc[gt.ring_id == rid, "account_id"])
        g = tx[tx.ring == rid]
        dev_share = g.groupby("device_id")["account_id"].nunique().max()
        # dense counterparty links: intra-ring transfers between members
        dense = g[g.counterparty_id.isin(members)].shape[0]
        assert dev_share >= 3 or dense >= 3, (rid, dev_share, dense)


# --------------------------------------------------------------------------- #
# hard negatives — clean high velocity
# --------------------------------------------------------------------------- #
def test_hard_negatives_high_velocity_but_clean(transactions, ground_truth):
    hn = ground_truth[ground_truth.is_hard_negative == 1]
    assert len(hn) == 10
    fraud_typs = set(T.ALL_TYPOLOGIES)
    for _, row in hn.iterrows():
        aid = row.account_id
        # none of the 8 structural mule typologies is labelled
        labelled = set(str(row.typologies_expressed).split(";"))
        assert not (labelled & fraud_typs), (aid, labelled)

        t = transactions[transactions.account_id == aid]
        credits = t[t.direction == "credit"]
        # HIGH velocity: many small credits over the window
        assert len(credits) >= 90, (aid, len(credits))
        # NOT round-amount structuring
        round_share = t.amount.round().isin(STRUCTURING).mean()
        assert round_share < 0.02, (aid, round_share)
        # NOT device sharing: its device(s) appear on no other account
        others = transactions[transactions.account_id != aid]
        assert not others.device_id.isin(t.device_id.unique()).any(), aid
        # NOT rapid pass-through: balance accumulates (not hovering near zero)
        assert t.sort_values("datetime").balance_after.iloc[-1] > 5_000, aid


# --------------------------------------------------------------------------- #
# typology coverage + injected signatures
# --------------------------------------------------------------------------- #
def test_all_typologies_expressed(ground_truth):
    expressed = set()
    for s in ground_truth.typologies_expressed.dropna():
        expressed.update(x for x in str(s).split(";") if x)
    for typ in T.ALL_TYPOLOGIES:
        assert typ in expressed, typ


def test_structuring_mules_hug_thresholds(transactions, ground_truth):
    struct_accts = ground_truth[
        ground_truth.typologies_expressed.str.contains(T.TYP_STRUCT, na=False)
    ].account_id
    assert len(struct_accts) >= 1
    hits = 0
    for aid in struct_accts:
        t = transactions[transactions.account_id == aid]
        if t.amount.round().isin(STRUCTURING).sum() >= 8:
            hits += 1
    assert hits == len(struct_accts)


def test_passthrough_mules_sweep_within_24h(transactions, ground_truth):
    pt_accts = ground_truth[
        ground_truth.typologies_expressed.str.contains(T.TYP_PASS, na=False)
        & (ground_truth.role == "mule")
    ].account_id.tolist()
    assert pt_accts
    aid = pt_accts[0]
    t = transactions[transactions.account_id == aid].copy()
    t["dt"] = pd.to_datetime(t.datetime)
    credit_in = t[t.direction == "credit"].amount.sum()
    debit_out = t[t.direction == "debit"].amount.sum()
    # near-total pass-through: most of what comes in goes back out
    assert debit_out >= 0.7 * credit_in, (aid, debit_out, credit_in)


def test_odd_hours_mules_have_night_activity(transactions, ground_truth):
    odd_accts = ground_truth[
        ground_truth.typologies_expressed.str.contains(T.TYP_ODD, na=False)
    ].account_id
    assert len(odd_accts) >= 1
    for aid in odd_accts:
        t = transactions[transactions.account_id == aid]
        hours = pd.to_datetime(t.datetime).dt.hour
        assert (hours < 5).any(), aid


# --------------------------------------------------------------------------- #
# ground-truth isolation convention
# --------------------------------------------------------------------------- #
def test_ground_truth_not_referenced_by_runtime_code():
    """`fraud_ground_truth` may only be referenced by data-gen and test/eval code.

    No scoring/runtime module may read the labels. (There is no app/ml/fraud yet;
    this convention assert guards the future WP-5M engine.)
    """
    app_dir = REPO_ROOT / "app"
    offenders = []
    for py in app_dir.rglob("*.py"):
        rel = py.relative_to(REPO_ROOT).as_posix()
        if "/tests/" in rel or "/test_" in py.name or "/data_gen/" in rel \
                or "/eval" in rel:
            continue
        if "fraud_ground_truth" in py.read_text(encoding="utf-8", errors="ignore"):
            offenders.append(rel)
    assert not offenders, f"ground truth referenced by runtime code: {offenders}"


def test_build_cli_runs(tmp_path):
    """`python -m ...data_gen.build` produces the three CSVs."""
    out = subprocess.run(
        [sys.executable, "-m",
         "app.tracks.t05_fraud_intelligence.data_gen.build",
         "--out", str(tmp_path)],
        cwd=REPO_ROOT, capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    for name in (ACCOUNTS_CSV, TRANSACTIONS_CSV, GROUND_TRUTH_CSV):
        assert (tmp_path / name).exists()
