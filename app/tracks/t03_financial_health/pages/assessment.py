"""Track 03 · Assessment — pick a business, run, and watch the pipeline build.

Merges the former Run Assessment + Pipeline pages (multi-track issue #5): the
scenario picker and the staged-reveal animation now live on one page (deep link
`track03`). The reveal is the **stage rail** (Waiting → Running → Completed)
beside the live per-stage output, with a **minimum dwell per stage** (issue #4).
There is no skip / instant path (issue #2): the assessment is precomputed in
`state.run`, and the animation narrates it.

All computation lives in backend/ml; this page only picks an entity and renders
`Stage` objects from the orchestrator.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# --- make the repo root importable (the router bootstraps this too) -----------
_p = Path(__file__).resolve()
_ROOT = next((par for par in _p.parents if (par / "requirements.txt").exists()), _p.parents[4])
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import html

import streamlit as st
import streamlit.components.v1 as components

from app.backend.services.pipeline_orchestrator import list_scenarios, random_entity_id
from app.frontend.components import state
from app.frontend.components.stage import (console_html, render_detail,
                                           render_stage_cell, stage_list_html)
from app.frontend.components.ui import badge, fmt_inr, page_header

# Minimum seconds a stage stays "running" before the next appears (issue #4).
STAGE_MIN_SECONDS = 3.0


def _scroll_to_pipeline() -> None:
    """Bring the live pipeline into view when a run starts. The picker sits above
    the fold, so without this the animation plays off-screen. Same parent-document
    technique as ui._inject_css; the delay lets the streamed layout settle."""
    components.html(
        "<script>setTimeout(function () {"
        "const el = window.parent.document.querySelector('.cp-live-anchor');"
        "if (el) el.scrollIntoView({behavior: 'smooth', block: 'center'});"
        "}, 300);</script>",
        height=0,
    )


def render() -> None:
    page_header("Assessment",
                "MSME financial health card · IDBI Innovate 2026 · Problem Statement 3 · "
                "deterministic-first, explainable by construction")

    st.markdown(
        "<div class='cp-card'>Fuse an MSME's fragmented digital footprint (GST, banking, "
        "UPI, EPFO, bureau, e-way bills, electricity, licences, procurement and more) into "
        "one explainable financial health card, with a <b>turnover-authenticity</b> check that "
        "is harder to fake than any single document.</div>", unsafe_allow_html=True)

    engine = state.get_engine()
    scenarios = list_scenarios(engine)

    # Once an assessment exists, the picker compacts into an expander so reruns
    # and revisits land on the pipeline record instead of a full page of chooser.
    has_run = state.get_assessment() is not None
    picker = (st.expander("Choose a business and rerun", expanded=False)
              if has_run else st.container())
    with picker:
        if not has_run:
            st.subheader("1 · Choose a business to assess")
        RANDOM = "Random MSME (varies each run)"
        labels = {f"{s['name']}  ·  {s['sector']} · {s['category']}": s for s in scenarios}
        choice = st.radio("Demo archetypes", list(labels.keys()) + [RANDOM],
                          label_visibility="collapsed")

        if choice == RANDOM:
            st.markdown(
                "<div class='cp-card'><b>Random MSME</b><div class='cp-scn'>A randomised entity "
                "from the synthetic cohort. Demonstrates the pipeline is adaptive, not scripted.</div></div>",
                unsafe_allow_html=True)
            selected_id = None
        else:
            s = labels[choice]
            st.markdown(
                f"<div class='cp-card'><b>{html.escape(str(s['name']))}</b> &nbsp; {badge(s['sector'], 'info')} "
                f"{badge(s['category'], 'info')} {badge(fmt_inr(s['turnover']) + ' declared', 'info')}"
                f"<div class='cp-scn' style='margin-top:.5rem'>{s['blurb']}</div></div>",
                unsafe_allow_html=True)
            selected_id = s["entity_id"]

        if not has_run:
            st.subheader("2 · Run")
        if st.button("Run assessment", type="primary", use_container_width=True):
            state.run(selected_id or random_entity_id(engine))   # resets the play flag

    a = state.get_assessment()
    if a is None:
        st.info("Pick a business above and click **Run assessment** to build its health card "
                "step by step — each stage leaves a plain-language record of what it found and why.")
        return

    st.divider()
    _render_pipeline(a, state.is_technical())


def _render_pipeline(a, technical: bool) -> None:
    """The staged-reveal itself: a stage rail (left) beside the live per-stage
    output (right), with the notebook-cell record accumulating below."""
    st.subheader("Assessment pipeline")
    st.caption(f"{a.entity['name']} · {a.entity.get('sector', '')} · "
               f"{a.entity.get('category', '')} · end-to-end alternate-data assessment")

    if st.button("Rerun computation", use_container_width=False):
        st.session_state["cp_pipeline_played"] = False
        st.rerun()

    stages = a.stages

    def cell_detail(container, stage) -> None:
        render_detail(container, stage, a.entity["name"], technical, show_header=False,
                      key_prefix=f"cell{stage.index}_")

    left, right = st.columns([1, 1.4])
    stage_ph = left.empty()
    progress_ph = left.empty()
    right.markdown("<div class='cp-live-anchor'></div>", unsafe_allow_html=True)
    detail_ph = right.empty()
    console_ph = right.empty() if technical else None
    cells = st.container()

    play = not state.already_played()

    if play:
        _scroll_to_pipeline()
        log_lines: list[str] = []
        bar = progress_ph.progress(0.0, text="Starting …")

        def _console(ln: str) -> None:
            log_lines.append(ln)
            if console_ph is not None:
                console_ph.markdown(console_html(log_lines[-22:], short=True), unsafe_allow_html=True)

        for i, s in enumerate(stages, start=1):
            stage_ph.markdown(stage_list_html(stages, s.index), unsafe_allow_html=True)
            bar.progress((i - 1) / len(stages), text=f"Stage {s.index}/{len(stages)} · {s.title}")
            t0 = time.time()

            if s.key == "ingestion":
                # The deliberate breadth moment (§6.2 stage 2): one source card per
                # source, so the footprint visibly assembles.
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

            render_detail(detail_ph, s, a.entity["name"], technical, key_prefix="live_")
            # Minimum dwell per stage (issue #4): hold the running stage on screen
            # for at least STAGE_MIN_SECONDS before the next stage appears.
            elapsed = time.time() - t0
            if elapsed < STAGE_MIN_SECONDS:
                time.sleep(STAGE_MIN_SECONDS - elapsed)
            if i < len(stages):
                with cells:
                    render_stage_cell(s, technical, expanded=False, detail_fn=cell_detail)

        stage_ph.markdown(stage_list_html(stages, len(stages) + 1), unsafe_allow_html=True)
        bar.progress(1.0, text="Assessment complete")
        detail_ph.empty()
        with cells:
            render_stage_cell(stages[-1], technical, expanded=True, detail_fn=cell_detail)
        state.mark_played()
    else:
        # Completed / already-played: the full stage rail + 9-cell record, no sleeps.
        stage_ph.markdown(stage_list_html(stages, len(stages) + 1), unsafe_allow_html=True)
        progress_ph.progress(1.0, text="Assessment complete")
        if console_ph is not None:
            all_lines = [ln for s in stages for ln in s.log]
            console_ph.markdown(console_html(all_lines, short=True), unsafe_allow_html=True)
        with cells:
            for s in stages:
                render_stage_cell(s, technical, expanded=(s.index == len(stages)),
                                  detail_fn=cell_detail)
