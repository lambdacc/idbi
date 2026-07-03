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


@st.cache_resource(show_spinner="Fitting scoring models on the synthetic cohort …")
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
        st.info("No assessment yet — pick a scenario on the **Home** page and click **Run Assessment**.")
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
