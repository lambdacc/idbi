"""WP-4A frontend tests — the two Track-04 pages driven through the real router.

Uses the WP-S AppTest recipe (callable pages + `_page_hash = calc_md5(url_path)`
navigation; `at.switch_page` is dead under st.navigation). Asserts both pages
render with zero exceptions in BOTH view modes AND on a COLD session (no seeded
state), surface the required demo copy, and — in Simple mode — stay jargon-clean
against the platform banned list plus the Track-04 extension.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from streamlit.util import calc_md5

from app.tracks.t04_early_warning.glossary import BANNED_SIMPLE
from app.tracks.t04_early_warning.service import SHOWCASE_ENTITY

_ROOT = Path(__file__).resolve().parents[4]
_APP = str(_ROOT / "app" / "frontend" / "main.py")

_PORTFOLIO = "track04"
_WATCHLIST = "watchlist"

# Platform §G4 banned terms + the Track-04 extension (both applied in Simple mode).
_PLATFORM_BANNED = ["SHAP", "WOE", "K-Means", "PCA", "centroid", "LightGBM",
                    "GBM", "monotonic", "z-score", "Model PD"]
_BANNED = _PLATFORM_BANNED + BANNED_SIMPLE


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


def _drive(mode: str, url_path: str, cold: bool = False) -> AppTest:
    at = AppTest.from_file(_APP, default_timeout=120)
    if not cold:
        at.session_state["cp_view_mode"] = mode
    at.run()                         # default page (Overview root)
    _goto(at, url_path)
    return at


@pytest.mark.parametrize("mode", ["simple", "technical"])
@pytest.mark.parametrize("url_path", [_PORTFOLIO, _WATCHLIST])
def test_page_renders(mode, url_path):
    at = _drive(mode, url_path)
    assert not at.exception, f"{url_path!r} [{mode}] raised: {at.exception}"


@pytest.mark.parametrize("url_path", [_PORTFOLIO, _WATCHLIST])
def test_page_renders_cold(url_path):
    """No seeded session state -> sensible default, never an exception."""
    at = _drive("simple", url_path, cold=True)
    assert not at.exception, f"{url_path!r} [cold] raised: {at.exception}"


def test_portfolio_shows_loans_kpi():
    body = _text_of(_drive("simple", _PORTFOLIO))
    assert "Loans monitored" in body and "Early-warning lead" in body


def test_watchlist_shows_flagship_and_first_alert():
    at = _drive("simple", _WATCHLIST)
    body = _text_of(at)
    # The flagship deteriorating borrower is the default-selected case.
    assert "Precision Auto Components" in body, "watchlist should open on the flagship"
    assert "Red" in body
    # The narrative money-shot phrasing.
    assert "baseline" in body.lower()


@pytest.mark.parametrize("url_path", [_PORTFOLIO, _WATCHLIST])
def test_simple_mode_jargon_clean(url_path):
    body = _text_of(_drive("simple", url_path)).lower()
    hits = [t for t in _BANNED if t.lower() in body]
    assert not hits, f"{url_path!r} [simple] leaked jargon: {hits}"
