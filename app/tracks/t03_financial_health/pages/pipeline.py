"""Staged-reveal pipeline (implementation-plan §6.2) — the 9-stage animation.

Renders only `Stage` objects from the orchestrator. The animation is a timed
reveal built from Streamlit primitives (st.empty placeholders + a blocking loop):
stages transition Waiting → Running → Completed while the execution console
accumulates the per-stage log lines.

Each completed stage leaves behind a persistent, notebook-style cell (plan §4
WP-C / D2): an expander with plain-language findings + the stage's visualization.
After a full run the live single-detail area is cleared — the 9 cells ARE the
record. The execution console is technical-view ambience only (D3). "Instant
mode" / "already played" render the full 9-cell record with no sleeps.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

_p = Path(__file__).resolve()
_ROOT = next((par for par in _p.parents if (par / "requirements.txt").exists()), _p.parents[4])
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.frontend.components import state
from app.frontend.components.stage import (console_html, render_detail,
                                           render_stage_cell, stage_list_html)
from app.frontend.components.ui import page_header


def render() -> None:
    a = state.require_assessment()
    technical = state.is_technical()

    def cell_detail(container, stage) -> None:
        """render_detail bound to this run's entity + view mode, header suppressed
        (the expander label already carries `Stage N · Title`)."""
        render_detail(container, stage, a.entity["name"], technical, show_header=False,
                      key_prefix=f"cell{stage.index}_")

    # ------------------------------------------------------------------ header
    page_header("Assessment pipeline",
                f"{a.entity['name']} · {a.entity.get('sector', '')} · "
                f"{a.entity.get('category', '')} · end-to-end alternate-data assessment")

    top = st.columns([1, 1, 2])
    instant = st.session_state.get("cp_instant", False)
    with top[0]:
        if st.button("Skip to result", use_container_width=True):
            state.mark_played()
            instant = True
    with top[1]:
        if st.button("Replay", use_container_width=True):
            st.session_state["cp_pipeline_played"] = False
            st.rerun()

    # Layout (I2 / WP-G): two columns in BOTH views. Left = stage rail + progress
    # (narrower); right = the LIVE stage-output pane that streams each stage as it
    # generates. In Technical view the execution console sits BELOW the live pane
    # (compact `.short` variant); Simple view has no console. Both branches (play /
    # instant) share this one setup so the placeholders always exist — no NameError.
    left, right = st.columns([1, 1.6])
    stage_ph = left.empty()
    progress_ph = left.empty()
    # `.cp-live-anchor` gives CSS a stable hook to fade the live pane content in.
    right.markdown("<div class='cp-live-anchor'></div>", unsafe_allow_html=True)
    # The live single-stage detail area (cleared when the run finishes) now lives in
    # the right column, above the console. The notebook cells (D2) stay full-width below.
    detail_ph = right.empty()
    console_ph = right.empty() if technical else None
    cells = st.container()

    stages = a.stages
    play = not (instant or state.already_played())

    if play:
        log_lines: list[str] = []
        bar = progress_ph.progress(0.0, text="Starting …")

        def _console(ln: str) -> None:
            log_lines.append(ln)
            # Technical view only; tail the console so newest lines stay visible.
            if console_ph is not None:
                console_ph.markdown(console_html(log_lines[-22:], short=True), unsafe_allow_html=True)

        for i, s in enumerate(stages, start=1):
            stage_ph.markdown(stage_list_html(stages, s.index), unsafe_allow_html=True)
            bar.progress((i - 1) / len(stages), text=f"Stage {s.index}/9 · {s.title}")

            if s.key == "ingestion":
                # The deliberate breadth moment (§6.2 stage 2): one console line + one
                # source card per source, so the footprint visibly assembles.
                n_sources = len(s.data["sources"])
                _console(s.log[0])
                for k, ln in enumerate(s.log[1:1 + n_sources], start=1):
                    _console(ln)
                    render_detail(detail_ph, s, a.entity["name"], technical, upto=k,
                                  key_prefix="live_")
                    time.sleep(0.12)
                for ln in s.log[1 + n_sources:]:
                    _console(ln)
            else:
                for ln in s.log:
                    _console(ln)
                    time.sleep(0.05)
            # The running stage stays "open" in the live detail area; each COMPLETED
            # earlier stage drops into the notebook below as a collapsed cell.
            render_detail(detail_ph, s, a.entity["name"], technical, key_prefix="live_")
            time.sleep(min(s.duration, 1.2) * 0.35)
            if i < len(stages):
                with cells:
                    render_stage_cell(s, technical, expanded=False, detail_fn=cell_detail)

        stage_ph.markdown(stage_list_html(stages, len(stages) + 1), unsafe_allow_html=True)
        bar.progress(1.0, text="Assessment complete")
        # Run finished: clear the live area — the notebook cells are the record.
        detail_ph.empty()
        with cells:
            render_stage_cell(stages[-1], technical, expanded=True, detail_fn=cell_detail)
        state.mark_played()
    else:
        # Completed / instant / already-played: no animation, the full 9-cell record.
        stage_ph.markdown(stage_list_html(stages, len(stages) + 1), unsafe_allow_html=True)
        progress_ph.progress(1.0, text="Assessment complete")
        if console_ph is not None:
            all_lines = [ln for s in stages for ln in s.log]
            console_ph.markdown(console_html(all_lines, short=True), unsafe_allow_html=True)
        with cells:
            for s in stages:
                render_stage_cell(s, technical, expanded=(s.index == len(stages)),
                                  detail_fn=cell_detail)
