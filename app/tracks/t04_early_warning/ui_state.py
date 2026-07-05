"""Track-04 session/engine helpers (in-track; not appended to the shared
`components/state.py`, per the isolation rules).

The fitted EWS engine is expensive to build, so it is cached once per process via
`st.cache_resource`; the composed `MonitoringRun` is cached in `st.session_state`
so both pages render the same monitoring result within a session. View mode is
read from the shared session contract (`state.is_technical()`), which is
read-only.
"""
from __future__ import annotations

import streamlit as st

from app.frontend.components import state as _core_state
from .ml.model import EWSEngine, get_engine as _get_engine
from .service import MonitoringRun, run_monitoring

_RUN_KEY = "cp_monitoring_run"


@st.cache_resource(show_spinner="First launch: fitting the early-warning model on "
                                "the synthetic loan book, one time, about ten "
                                "seconds. Later runs load instantly.")
def get_ews_engine() -> EWSEngine:
    """Cached fitted EWS engine singleton (prefit pickle when fresh, else fit)."""
    return _get_engine()


def get_monitoring_run() -> MonitoringRun:
    """Session-cached monitoring result (composed once per session by the backend)."""
    run = st.session_state.get(_RUN_KEY)
    if run is None:
        run = run_monitoring(get_ews_engine())
        st.session_state[_RUN_KEY] = run
    return run


def is_technical() -> bool:
    return _core_state.is_technical()
