"""Staged-reveal pipeline (implementation-plan §6.2) — the 9-stage animation.

Renders only `Stage` objects from the orchestrator. The animation is a timed
reveal built from Streamlit primitives (st.empty placeholders + a blocking loop):
stages transition Waiting → Running → Completed while the execution console
accumulates the per-stage log lines. "Instant mode" / "already played" render the
completed state with no sleeps.
"""
from __future__ import annotations

import html
import sys
import time
from pathlib import Path

_p = Path(__file__).resolve()
_ROOT = next((par for par in _p.parents if (par / "requirements.txt").exists()), _p.parents[3])
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.frontend.components import charts, state
from app.frontend.components.stage import (console_html, feature_label, kpi_mini,
                                           render_composites, render_feature_counters,
                                           render_reasons, render_source_grid, stage_list_html)
from app.frontend.components.ui import badge, band_class, fmt_inr, kpi, page_setup, risk_class

page_setup("Pipeline", icon="⚙️")
a = state.require_assessment()


# --------------------------------------------------------- per-stage detail
def render_detail(container, stage, upto: int | None = None) -> None:
    """Render a stage's detail panel. `upto` (ingestion only) shows just the first
    k source cards — the §6.2 breadth-reveal lights them up one by one."""
    d = stage.data
    with container.container():
        st.markdown(f"#### Stage {stage.index} · {stage.title}")
        st.caption(stage.caption)

        if stage.key == "scenario_lock_in":
            e = d["entity"]
            cols = st.columns(5)
            cols[0].markdown(kpi("Sector", e.get("sector", "—")), unsafe_allow_html=True)
            cols[1].markdown(kpi("Udyam category", e.get("category", "—")), unsafe_allow_html=True)
            cols[2].markdown(kpi("Vintage", f"{e.get('age_years', '—')} y"), unsafe_allow_html=True)
            cols[3].markdown(kpi("Employees", str(e.get("employees", "—"))), unsafe_allow_html=True)
            cols[4].markdown(kpi("Declared turnover", fmt_inr(e.get("declared_turnover"))),
                             unsafe_allow_html=True)

        elif stage.key == "ingestion":
            render_source_grid(d["sources"], limit=upto)
            if upto is None:
                st.caption(f"{d['connected']} of {d['total']} sources carry a live signal for this entity.")

        elif stage.key == "integration":
            cols = st.columns(3)
            cols[0].markdown(kpi("Raw records reconciled", f"{d['total_records']:,}"),
                             unsafe_allow_html=True)
            cols[1].markdown(kpi("Sources merged", str(d["connected"])), unsafe_allow_html=True)
            cols[2].markdown(kpi("Identity integrity", f"{d['identity_integrity']:.2f}",
                             "1.0 = all registries agree"), unsafe_allow_html=True)

        elif stage.key == "features":
            render_feature_counters(d["counters"], d["composite_count"])
            st.caption(f"{d['total_features']} engineered signals across 5 pillars + composites.")

        elif stage.key == "synthesis":
            comps = d["composites"]
            flag = [c for c in comps if c.get("flagship")]
            rest = [c for c in comps if not c.get("flagship")]
            render_composites(flag)
            left, right = st.columns(2)
            with left:
                render_composites(rest[0::2])
            with right:
                render_composites(rest[1::2])

        elif stage.key == "clustering":
            st.markdown(badge(f"Peer group: {d['segment']}", "info") +
                        f" &nbsp; <span class='cp-scn'>K-Means, k={d['k']} · descriptive only</span>",
                        unsafe_allow_html=True)
            st.plotly_chart(charts.cluster_scatter(d["scatter"], d["entity_point"],
                            a.entity["name"]), use_container_width=True)

        elif stage.key == "scoring":
            labels = [p["label"] for p in d["pillars"]]
            vals = [p["score"] for p in d["pillars"]]
            c1, c2 = st.columns([1.3, 1])
            with c1:
                st.plotly_chart(charts.pillar_bars(labels, vals), use_container_width=True)
            with c2:
                st.markdown(kpi("Composite score", f"{d['composite_score']:.0f}<small>/100</small>",
                            f"Grade {d['grade']}/10", score_kind(d["onboarding_band"])),
                            unsafe_allow_html=True)
                st.markdown(kpi("Model PD", f"{d['pd']:.1%}", d["risk_category"] + " risk",
                            risk_class(d["risk_category"])), unsafe_allow_html=True)

        elif stage.key == "explainability":
            render_reasons(d["reasons_positive"], d["reasons_negative"])
            if d["shap_top"]:
                st.markdown("**SHAP cross-check** — monotonic GBM PD path")
                st.plotly_chart(charts.shap_waterfall(d["shap_top"], feature_label),
                                use_container_width=True)

        elif stage.key == "health_card":
            hc = d["health_card"]
            st.markdown(
                f"<div class='cp-hero'><div class='score'>{hc['composite_score']:.0f}"
                f"<small>/100</small></div><div class='meta'>"
                f"<div class='name'>{html.escape(str(hc['name']))}</div>"
                f"<div class='subtle'>Grade {hc['grade']}/10 · {hc['recommendation']} · "
                f"Confidence {hc['confidence']}</div></div></div>", unsafe_allow_html=True)
            st.page_link("pages/3_Financial_Health_Card.py",
                         label="📋  Open the full Financial Health Card", use_container_width=True)


def score_kind(band: str) -> str:
    return band_class(band)


# ------------------------------------------------------------------ header
st.title("Assessment Pipeline")
st.caption(f"{a.entity['name']} · {a.entity.get('sector', '')} · "
           f"{a.entity.get('category', '')} — end-to-end alternate-data assessment")

top = st.columns([1, 1, 2])
instant = st.session_state.get("cp_instant", False)
with top[0]:
    if st.button("⏩  Instant (skip)", use_container_width=True):
        state.mark_played()
        instant = True
with top[1]:
    if st.button("↻  Replay", use_container_width=True):
        st.session_state["cp_pipeline_played"] = False
        st.rerun()

left, right = st.columns([1, 1.25])
stage_ph = left.empty()
progress_ph = left.empty()
console_ph = right.empty()
detail_ph = st.empty()

stages = a.stages
play = not (instant or state.already_played())

if play:
    log_lines: list[str] = []
    bar = progress_ph.progress(0.0, text="Starting …")
    for i, s in enumerate(stages, start=1):
        stage_ph.markdown(stage_list_html(stages, s.index), unsafe_allow_html=True)
        bar.progress((i - 1) / len(stages), text=f"Stage {s.index}/9 · {s.title}")

        def _console(ln: str) -> None:
            log_lines.append(ln)
            # Tail the console so the newest lines stay visible (CSS can't auto-scroll).
            console_ph.markdown(console_html(log_lines[-22:]), unsafe_allow_html=True)

        if s.key == "ingestion":
            # The deliberate breadth moment (§6.2 stage 2): one console line + one
            # source card per source, so the footprint visibly assembles.
            n_sources = len(s.data["sources"])
            _console(s.log[0])
            for k, ln in enumerate(s.log[1:1 + n_sources], start=1):
                _console(ln)
                render_detail(detail_ph, s, upto=k)
                time.sleep(0.12)
            for ln in s.log[1 + n_sources:]:
                _console(ln)
        else:
            for ln in s.log:
                _console(ln)
                time.sleep(0.05)
        render_detail(detail_ph, s)
        time.sleep(min(s.duration, 1.2) * 0.35)
    stage_ph.markdown(stage_list_html(stages, len(stages) + 1), unsafe_allow_html=True)
    bar.progress(1.0, text="Assessment complete ✓")
    state.mark_played()
else:
    # Completed state, no animation.
    stage_ph.markdown(stage_list_html(stages, len(stages) + 1), unsafe_allow_html=True)
    progress_ph.progress(1.0, text="Assessment complete ✓")
    all_lines = [ln for s in stages for ln in s.log]
    console_ph.markdown(console_html(all_lines), unsafe_allow_html=True)
    render_detail(detail_ph, stages[-1])
