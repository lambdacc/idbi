"""Platform Overview — the default landing page (multi-track R4 / D11 root).

Static platform pitch: brandmark hero, the one-paragraph story, one card per
INSTALLED track (auto-detected via the registry, so a deleted track folder drops
its card with no edits), and the honesty note. No computation — pure copy, and
jargon-clean in Simple mode (the banned-term sweep covers this page).
"""
from __future__ import annotations

import sys
from pathlib import Path

_p = Path(__file__).resolve()
_ROOT = next((par for par in _p.parents if (par / "requirements.txt").exists()), _p.parents[3])
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.frontend import tracks
from app.frontend.components import state


def render() -> None:
    _tech = state.is_technical()

    # The navbar already carries the wordmark, so the landing headline is the
    # platform story itself rather than a second brandmark.
    st.markdown("<h1 class='cp-ov-hero'>One platform, three problem statements</h1>",
                unsafe_allow_html=True)
    st.caption("The MSME lending lifecycle on one data spine · IDBI Innovate 2026 · all data synthetic")

    # NB: this string lands inside an HTML card, so emphasis must be HTML tags —
    # markdown syntax is not parsed inside an unsafe_allow_html block.
    story = (
        "CreditPulse turns an MSME's scattered digital footprint into decisions a bank can act on. "
        "One platform runs the whole lending lifecycle: <b>underwrite the credit-invisible</b> (Problem Statement 3), "
        "then <b>monitor the book</b> for early signs of stress (Problem Statement 4), then <b>protect the payment "
        "rails</b> from mule-account fraud (Problem Statement 5) — the same data spine, the same explainability "
        "discipline, three problem statements."
    )
    st.markdown(f"<div class='cp-card'>{story}</div>", unsafe_allow_html=True)

    # One card per installed track that carries a badge (the three problem
    # statements); platform/reference groups are navigation, not products.
    track_cards = [t for t in tracks.installed_tracks() if t.badge]
    cols = st.columns(len(track_cards)) if track_cards else []
    for col, track in zip(cols, track_cards):
        with col:
            caps = "".join(f"<li>{c}</li>" for c in track.capabilities)
            st.markdown(
                f"<div class='cp-card' style='height:100%'>"
                f"<span class='cp-track-badge'>{track.badge}</span>"
                f"<h4 style='margin-top:.5rem'>{track.label.split('·')[-1].strip()}</h4>"
                f"<div class='cp-scn' style='margin-bottom:.6rem;min-height:6.4em'>{track.blurb}</div>"
                f"<ul class='cp-caps'>{caps}</ul></div>",
                unsafe_allow_html=True)
            st.page_link(tracks.get_page(track.start_key),
                         label=f"Open {track.label.split('·')[-1].strip()}",
                         use_container_width=True)

    st.divider()
    arch = tracks.get_page("ref.architecture")
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(
            "**One stack underneath.** 25 alternate-data sources → cross-source synthesis → "
            "explainable scoring, all in a single Cloud-Run container. See the Reference · "
            "Architecture page for the full diagram."
            if _tech else
            "**One system underneath.** Every track reads the same verified data sources and explains "
            "every decision in plain terms. See the Reference · Architecture page for the big picture.",
            unsafe_allow_html=True)
    with c2:
        st.page_link(arch, label="Architecture", use_container_width=True)

    st.info("All data shown across the platform is synthetic and clearly labelled. Real GST / Account "
            "Aggregator / EPFO integration and real-outcome recalibration are the pilot steps, stated "
            "honestly — nothing here claims live-data performance.")
