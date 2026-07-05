"""Track 05 · Fraud Desk — placeholder (multi-track R5; D11 deep link `track05`).
WP-5A replaces this with the live fraud-desk queue.
"""
from __future__ import annotations

import sys
from pathlib import Path

_p = Path(__file__).resolve()
_ROOT = next((par for par in _p.parents if (par / "requirements.txt").exists()), _p.parents[4])
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.frontend import tracks
from app.frontend.components.ui import badge, page_header


def render() -> None:
    page_header("Fraud Desk",
                "Track 05 · Fraud Intelligence — explainable mule-account detection (SentinelPulse).")
    st.markdown(
        f"<div class='cp-card'>{badge('PS5', 'info')} &nbsp; This track is coming online. "
        "It will queue suspected mule accounts flagged by typology rules and an anomaly cross-check, "
        "expand suspected rings across the transaction graph, and hand each to an agentic, "
        "citation-gated investigation. All data synthetic.</div>",
        unsafe_allow_html=True)
    st.page_link(tracks.get_page("platform.overview"), label="Back to Overview")
