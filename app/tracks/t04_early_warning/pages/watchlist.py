"""Track 04 · Watchlist & Cases — placeholder (multi-track R5). WP-4A replaces
this with the watchlist + per-borrower drilldown.
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
    page_header("Watchlist & Cases",
                "Track 04 · Early Warning — flagged borrowers with explained deterioration drivers.")
    st.markdown(
        f"<div class='cp-card'>{badge('PS4', 'info')} &nbsp; This track is coming online. "
        "It will list at-risk borrowers with a drilldown timeline showing which alternate-data signals "
        "turned first and why each account was flagged. All data synthetic.</div>",
        unsafe_allow_html=True)
    st.page_link(tracks.get_page("platform.overview"), label="Back to Overview")
