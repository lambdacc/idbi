"""Track 05 · Case Investigation — placeholder (multi-track R5). WP-5A replaces
this with the staged agentic investigation + citation-gated case file.
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
    page_header("Case Investigation",
                "Track 05 · Fraud Intelligence — a citation-gated case file assembled for human approval.")
    st.markdown(
        f"<div class='cp-card'>{badge('PS5', 'info')} &nbsp; This track is coming online. "
        "It will assemble each investigation into a case file where every claim resolves to specific "
        "transaction IDs, ready for an analyst to approve or override. All data synthetic.</div>",
        unsafe_allow_html=True)
    st.page_link(tracks.get_page("platform.overview"), label="Back to Overview")
