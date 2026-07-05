"""Session/engine state for the multipage app.

The fitted ScoringEngine is expensive to build, so it is cached once per process
via st.cache_resource. The current Assessment (produced by the pipeline
orchestrator) lives in st.session_state so every page renders the same run.
"""
from __future__ import annotations

from typing import Optional

import streamlit as st

from app.backend.services.pipeline_orchestrator import Assessment, run_assessment
from app.ml.engine import ScoringEngine, get_engine as _get_engine

_ASSESSMENT_KEY = "cp_assessment"
_PLAYED_KEY = "cp_pipeline_played"
_VIEW_MODE_KEY = "cp_view_mode"


@st.cache_resource(show_spinner="First launch: fitting the scoring models on the synthetic cohort, one time, about ten seconds. Later runs load instantly.")
def get_engine() -> ScoringEngine:
    return _get_engine()


def run(entity_id: str) -> Assessment:
    """Run an assessment and store it as the active one (resets the play flag)."""
    a = run_assessment(entity_id, get_engine())
    st.session_state[_ASSESSMENT_KEY] = a
    st.session_state[_PLAYED_KEY] = False
    return a


def get_assessment() -> Optional[Assessment]:
    return st.session_state.get(_ASSESSMENT_KEY)


def has_assessment() -> bool:
    return _ASSESSMENT_KEY in st.session_state


def require_assessment() -> Optional[Assessment]:
    """Guard for pages that need a run; nudges the user to Home if none exists."""
    a = get_assessment()
    if a is None:
        # Leading heading occupies the "beside the toggle" slot (the page's own
        # st.title never runs because we st.stop() here); the card then flows
        # below normally instead of being pulled up under the toggle.
        st.markdown("<h1>No assessment yet</h1>", unsafe_allow_html=True)
        st.markdown(
            "<div class='cp-card' style='border-top:3px solid var(--cp-navy)'>"
            "Pick a business on the <b>Run Assessment</b> page and click <b>Run assessment</b>. "
            "The health card, pipeline and explainability views populate from that run."
            "</div>", unsafe_allow_html=True)
        # Object-form link via the registry (path strings don't resolve against
        # callable-registered pages — wp-s Q4); guarded so core never hard-imports
        # a track (D10). Called only from T03 pages, so the target always exists.
        from app.frontend import tracks
        st.page_link(tracks.get_page("t03.run"), label="Go to Run Assessment")
        st.stop()
    return a


def view_mode() -> str:
    """Active view mode: 'simple' (default) or 'technical'.

    'simple' hides model internals (SHAP, clustering, execution trace) and
    engineering names; 'technical' shows everything.
    """
    return st.session_state.get(_VIEW_MODE_KEY, "simple")


def is_technical() -> bool:
    """True when the user has opted into the technical (model-internals) view."""
    return view_mode() == "technical"


def mark_played() -> None:
    st.session_state[_PLAYED_KEY] = True


def already_played() -> bool:
    return bool(st.session_state.get(_PLAYED_KEY))
