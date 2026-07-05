"""Frontend smoke test — platform shell edition (multi-track WP-R / R8).

Drives the real Streamlit app through AppTest in BOTH view modes and asserts, for
every page, that it renders without raising, that the Health Card carries the
plain-language verdict, that Simple mode is jargon-clean (Architecture exempt),
and that Technical Explainability surfaces SHAP.

Migrated from the single-track `Home.py` entrypoint to the `st.navigation` router
`main.py`. Two hard rules from the WP-S nav spike (do not "simplify" away):

  * Pages are registered as CALLABLES (`render()`), so AppTest actually executes
    them — file-path `st.Page` sources render BLANK under MPA v2 (wp-s Q5).
  * `at.switch_page(...)` is DEAD under st.navigation (it hashes file paths; pages
    hash their `url_path`). Navigate by setting the page hash to the url_path hash:
    `at._page_hash = calc_md5(url_path); at.run()` — the `_goto` helper below.

Session keys are seeded INDIVIDUALLY (SafeSessionState has no `.update()`), with
`cp_pipeline_played`/`cp_instant` set so the pipeline skips its real time.sleep.
Pages are addressed by their D11 url_path, never by file location.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest
from streamlit.util import calc_md5

from app.backend.services.pipeline_orchestrator import run_assessment

_ROOT = Path(__file__).resolve().parents[2]
_APP = str(_ROOT / "app" / "frontend" / "main.py")

# Pages addressed by their registry url_path (wp-s Q5/Q7). "" is the Overview root.
_OVERVIEW = ""
_RUN = "track03"
_DASHBOARD = "dashboard"
_PIPELINE = "pipeline"
_HEALTH_CARD = "health_card"
_EXPLAINABILITY = "explainability"
_ARCHITECTURE = "architecture"          # technical by design — jargon-exempt
_T04_PORTFOLIO = "track04"
_T04_WATCHLIST = "watchlist"
_T05_DESK = "track05"
_T05_CASE = "case_investigation"

# Every registered page (render-only assertion for the placeholders at this stage).
_PAGES = [_OVERVIEW, _RUN, _DASHBOARD, _PIPELINE, _HEALTH_CARD, _EXPLAINABILITY,
          _ARCHITECTURE, _T04_PORTFOLIO, _T04_WATCHLIST, _T05_DESK, _T05_CASE]

# The named showcase entity: benign default risk but weak turnover-authenticity,
# so its Health Card verdict includes the flagship divergence narrative.
_ARCHETYPE = "AUTO_COMPONENTS"

# §5 G4 terms that must never appear in Simple mode (Architecture exempt).
_BANNED = ["SHAP", "WOE", "K-Means", "KMeans", "PCA", "centroid", "LightGBM",
           "GBM", "monotonic", "percentile", "z-score", "Model PD", "latent"]


def _text_of(at: AppTest) -> str:
    """Concatenate every text-bearing element's rendered value."""
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


@pytest.fixture(scope="module")
def assessment(engine):
    """One deterministic showcase assessment, built via the shared engine fixture."""
    return run_assessment(_ARCHETYPE, engine)


def _goto(at: AppTest, url_path: str) -> None:
    """Navigate under st.navigation by url_path hash (at.switch_page is dead here)."""
    at._page_hash = calc_md5(url_path)
    at.run()


def _drive(mode: str, assessment, url_path: str) -> AppTest:
    """Boot the router in `mode`, seed the assessment, then navigate to `url_path`."""
    at = AppTest.from_file(_APP, default_timeout=90)
    at.session_state["cp_view_mode"] = mode          # seed keys INDIVIDUALLY
    at.session_state["cp_assessment"] = assessment
    at.session_state["cp_pipeline_played"] = True     # skip the animation …
    at.session_state["cp_instant"] = True             # … no real time.sleep
    at.run()                                          # default page (Overview root)
    if url_path != _OVERVIEW:
        _goto(at, url_path)
    return at


@pytest.mark.parametrize("mode", ["simple", "technical"])
@pytest.mark.parametrize("url_path", _PAGES)
def test_page_renders(mode, url_path, assessment):
    """Every page renders in both view modes without raising."""
    at = _drive(mode, assessment, url_path)
    assert not at.exception, f"{url_path!r} [{mode}] raised: {at.exception}"


@pytest.mark.parametrize("mode", ["simple", "technical"])
def test_view_toggle_exactly_once(mode, assessment):
    """The router-owned Simple/Technical toggle renders exactly once, found by key."""
    at = _drive(mode, assessment, _DASHBOARD)
    toggles = [r for r in at.radio if r.key == "cp_view_mode"]
    assert len(toggles) == 1, f"expected 1 view toggle, got {len(toggles)} [{mode}]"


@pytest.mark.parametrize("mode", ["simple", "technical"])
def test_health_card_shows_verdict(mode, assessment):
    """The Health Card opens with the plain-language verdict (§CB-9)."""
    at = _drive(mode, assessment, _HEALTH_CARD)
    body = _text_of(at)
    assert "scores" in body and "/100" in body, \
        f"verdict narrative missing on Health Card [{mode}]"


@pytest.mark.parametrize("url_path", [_OVERVIEW, _DASHBOARD, _PIPELINE,
                                      _HEALTH_CARD, _EXPLAINABILITY])
def test_simple_mode_jargon_clean(url_path, assessment):
    """Simple mode surfaces none of the §G4 banned terms (Overview + pages 1–4)."""
    at = _drive("simple", assessment, url_path)
    body = _text_of(at).lower()
    hits = [t for t in _BANNED if t.lower() in body]
    assert not hits, f"{url_path!r} [simple] leaked jargon: {hits}"


def test_technical_explainability_has_shap(assessment):
    """Technical mode's Explainability page DOES expose the SHAP cross-check."""
    at = _drive("technical", assessment, _EXPLAINABILITY)
    assert "SHAP" in _text_of(at), "Technical Explainability should mention SHAP"
