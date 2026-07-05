"""Track 04 · Portfolio Overview — placeholder (multi-track R5; D11 deep link
`track04`). WP-4A replaces this with the real portfolio early-warning page.
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
    page_header("Portfolio Overview",
                "Track 04 · Early Warning — 12-month MSME default early-warning on the synthetic loan book.")
    st.markdown(
        f"<div class='cp-card'>{badge('PS4', 'info')} &nbsp; This track is coming online. "
        "It will surface portfolio-wide deterioration from alternate data (monthly GST, UPI inflows, "
        "EPFO payroll) months before repayment behaviour slips, with lead-time measured against a "
        "repayment-only baseline. All data synthetic.</div>",
        unsafe_allow_html=True)
    st.page_link(tracks.get_page("platform.overview"), label="Back to Overview")
