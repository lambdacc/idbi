"""WP-5A — Track-05 page smoke + Simple-mode jargon sweep.

Drives the real st.navigation router through AppTest (wp-s recipe: callable pages
+ navigate by url_path hash, never at.switch_page). Asserts both Track-05 pages
render in both view modes with no exception, that Case Investigation is
cold-session safe (empty state, not a crash, when no account is seeded), and that
Simple mode never leaks the fraud-desk jargon the track glosses.

Run ONLY this track:  .venv/bin/python -m pytest app/tracks/t05_fraud_intelligence -q
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from streamlit.util import calc_md5

from app.tracks.t05_fraud_intelligence.case_orchestrator import desk_snapshot
from app.tracks.t05_fraud_intelligence.ml.model import get_engine

_ROOT = Path(__file__).resolve().parents[4]
_APP = str(_ROOT / "app" / "frontend" / "main.py")

_DESK = "track05"
_CASE = "case_investigation"

# Track terms the Simple pages must gloss, not surface raw. `\bmule\b` deliberately
# does NOT match the product name "MuleHunter"; `\bSTR\b` matches only the acronym.
_BANNED = [r"\bmule\b", r"\bstr\b", r"typology", r"pass-through", r"structuring"]


@pytest.fixture(scope="module")
def cases():
    """Deterministic default account ids (same on-disk data the pages fit on)."""
    snap = desk_snapshot(get_engine())
    return snap["default_case"], snap["hard_negative"]


def _text_of(at: AppTest) -> str:
    chunks = []
    for attr in ("markdown", "caption", "title", "header", "subheader",
                 "text", "info", "warning", "error", "success"):
        try:
            for el in getattr(at, attr):
                val = getattr(el, "value", None)
                if val:
                    chunks.append(str(val))
        except Exception:
            pass
    return "\n".join(chunks)


def _goto(at: AppTest, url_path: str) -> None:
    at._page_hash = calc_md5(url_path)
    at.run()


def _drive(mode: str, url_path: str, case_account: str | None) -> AppTest:
    at = AppTest.from_file(_APP, default_timeout=120)
    at.session_state["cp_view_mode"] = mode
    at.session_state["cp_instant"] = True
    if case_account is not None:
        at.session_state["cp_case_account"] = case_account
    at.run()                              # Overview (root)
    _goto(at, url_path)
    return at


# --------------------------------------------------------------------------- #
# render smoke — both pages, both modes
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("mode", ["simple", "technical"])
def test_desk_renders(mode, cases):
    at = _drive(mode, _DESK, None)
    assert not at.exception, f"Fraud Desk [{mode}] raised: {at.exception}"


@pytest.mark.parametrize("mode", ["simple", "technical"])
def test_case_renders_for_ring(mode, cases):
    at = _drive(mode, _CASE, cases[0])
    assert not at.exception, f"Case (ring) [{mode}] raised: {at.exception}"


@pytest.mark.parametrize("mode", ["simple", "technical"])
def test_case_renders_for_hard_negative(mode, cases):
    at = _drive(mode, _CASE, cases[1])
    assert not at.exception, f"Case (hard-neg) [{mode}] raised: {at.exception}"


def test_case_cold_session_is_empty_state_not_crash(cases):
    """No cp_case_account seeded → friendly empty state, never an exception."""
    at = _drive("simple", _CASE, None)
    assert not at.exception
    assert "No case selected" in _text_of(at)


# --------------------------------------------------------------------------- #
# Simple-mode jargon sweep
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("url_path,seed", [(_DESK, None), (_CASE, "ring"),
                                           (_CASE, "hardneg")])
def test_simple_pages_are_jargon_clean(url_path, seed, cases):
    account = None
    if seed == "ring":
        account = cases[0]
    elif seed == "hardneg":
        account = cases[1]
    at = _drive("simple", url_path, account)
    assert not at.exception
    body = _text_of(at)
    hits = [p for p in _BANNED if re.search(p, body, flags=re.IGNORECASE)]
    assert not hits, f"{url_path!r}[{seed}] leaked jargon: {hits}"


def test_technical_case_surfaces_the_recommendation(cases):
    at = _drive("technical", _CASE, cases[0])
    assert "STR" in _text_of(at)  # technical view shows the raw STR recommendation
