"""Frontend smoke test (UI-humanization plan §4 WP-E step 2).

Drives the real Streamlit multipage app through Streamlit's AppTest harness in
BOTH view modes and asserts, for every page:
  * it renders without raising (`not at.exception`);
  * the Financial Health Card opens with the plain-language verdict narrative;
  * Simple mode is jargon-clean on pages 1–4 (the §5 G4 banned terms) — the
    Architecture page (5) is technical by design and EXEMPT;
  * Technical mode surfaces "SHAP" on the Explainability page.

AppTest pages MUST be driven from the `Home.py` entrypoint via
`at.switch_page(...)`; loading a page file as its own entrypoint throws
harness-only `page_link` errors. The assessment is pre-seeded into
`st.session_state` (built once from the shared `engine` fixture) with
`cp_pipeline_played`/`cp_instant` set so the pipeline page skips its real
`time.sleep` animation — keeping the test fast and deterministic.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from app.backend.services.pipeline_orchestrator import run_assessment

_ROOT = Path(__file__).resolve().parents[2]
_HOME = str(_ROOT / "app" / "frontend" / "Home.py")

# Pages are switch_page targets relative to the Home.py entrypoint directory.
_PAGES = [
    "pages/1_Dashboard.py",
    "pages/2_Pipeline.py",
    "pages/3_Financial_Health_Card.py",
    "pages/4_Explainability.py",
    "pages/5_Architecture.py",
]
_HEALTH_CARD = "pages/3_Financial_Health_Card.py"
_EXPLAINABILITY = "pages/4_Explainability.py"
_ARCHITECTURE = "pages/5_Architecture.py"  # technical by design — jargon-exempt

# The named showcase entity: benign default risk but weak turnover-authenticity,
# so its Health Card verdict includes the flagship divergence narrative.
_ARCHETYPE = "AUTO_COMPONENTS"

# §5 G4 terms that must never appear in Simple mode (Architecture exempt). This is
# the model-internals subset the plan pins for the page-level sweep — substring
# match (the reference verify used the same), so "Model PD" is one phrase.
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


def _drive(mode: str, assessment, rel_page: str) -> AppTest:
    """Boot Home.py in `mode`, seed the assessment, then switch to `rel_page`."""
    at = AppTest.from_file(_HOME, default_timeout=90)
    at.session_state["cp_view_mode"] = mode
    at.session_state["cp_assessment"] = assessment
    at.session_state["cp_pipeline_played"] = True   # skip the animation …
    at.session_state["cp_instant"] = True           # … no real time.sleep
    at.run()
    at.switch_page(rel_page)
    at.run()
    return at


@pytest.mark.parametrize("mode", ["simple", "technical"])
@pytest.mark.parametrize("rel_page", _PAGES)
def test_page_renders(mode, rel_page, assessment):
    """Every page renders in both view modes without raising."""
    at = _drive(mode, assessment, rel_page)
    assert not at.exception, f"{rel_page} [{mode}] raised: {at.exception}"


@pytest.mark.parametrize("mode", ["simple", "technical"])
def test_health_card_shows_verdict(mode, assessment):
    """The Health Card opens with the plain-language verdict (§CB-9)."""
    at = _drive(mode, assessment, _HEALTH_CARD)
    body = _text_of(at)
    assert "scores" in body and "/100" in body, \
        f"verdict narrative missing on Health Card [{mode}]"


@pytest.mark.parametrize("rel_page", ["pages/1_Dashboard.py", "pages/2_Pipeline.py",
                                      _HEALTH_CARD, _EXPLAINABILITY])
def test_simple_mode_jargon_clean(rel_page, assessment):
    """Simple mode surfaces none of the §G4 banned terms on pages 1–4."""
    at = _drive("simple", assessment, rel_page)
    body = _text_of(at).lower()
    hits = [t for t in _BANNED if t.lower() in body]
    assert not hits, f"{rel_page} [simple] leaked jargon: {hits}"


def test_technical_explainability_has_shap(assessment):
    """Technical mode's Explainability page DOES expose the SHAP cross-check."""
    at = _drive("technical", assessment, _EXPLAINABILITY)
    assert "SHAP" in _text_of(at), "Technical Explainability should mention SHAP"
