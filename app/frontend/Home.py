"""CreditPulse — Streamlit entry point: scenario picker + Run Assessment.

The staged-reveal pipeline (§6) plays on the Pipeline page; "Instant mode" skips
straight to the Financial Health Card for repeat runs / judge Q&A. This page only
picks a business and kicks off a run — all computation lives in backend/ml.
"""
from __future__ import annotations

import sys
from pathlib import Path

# --- make the repo root importable when launched via `streamlit run` ---------
_p = Path(__file__).resolve()
_ROOT = next((par for par in _p.parents if (par / "requirements.txt").exists()), _p.parents[2])
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.backend.services.pipeline_orchestrator import list_scenarios, random_entity_id
from app.frontend.components import state
from app.frontend.components.ui import badge, fmt_inr, page_setup

page_setup("Home", icon="📊")

st.title("CreditPulse")
st.caption("MSME Financial Health Card · IDBI Innovate 2026 · PS3 — "
           "deterministic-first, explainable-by-construction")

st.markdown(
    "<div class='cp-card'>Fuse an MSME's fragmented digital footprint — GST, banking, "
    "UPI, EPFO, bureau, e-way bills, electricity, licences, procurement and more — into "
    "one explainable Financial Health Card, with a <b>Turnover-Authenticity</b> check that "
    "is harder to fake than any single document.</div>", unsafe_allow_html=True)

engine = state.get_engine()
scenarios = list_scenarios(engine)

st.subheader("1 · Choose a business to assess")

RANDOM = "🎲  Random MSME (varies each run)"
labels = {f"{s['name']}  —  {s['sector']} · {s['category']}": s for s in scenarios}
choice = st.radio("Demo archetypes", list(labels.keys()) + [RANDOM],
                  label_visibility="collapsed")

if choice == RANDOM:
    st.markdown(
        "<div class='cp-card'><b>Random MSME</b><div class='cp-scn'>A randomised entity "
        "from the synthetic cohort — demonstrates the pipeline is adaptive, not scripted.</div></div>",
        unsafe_allow_html=True)
    selected_id = None
else:
    s = labels[choice]
    st.markdown(
        f"<div class='cp-card'><b>{s['name']}</b> &nbsp; {badge(s['sector'], 'info')} "
        f"{badge(s['category'], 'info')} {badge(fmt_inr(s['turnover']) + ' declared', 'info')}"
        f"<div class='cp-scn' style='margin-top:.5rem'>{s['blurb']}</div></div>",
        unsafe_allow_html=True)
    selected_id = s["entity_id"]

st.subheader("2 · Run")
c1, c2 = st.columns([1, 2])
with c1:
    staged = st.toggle("Staged reveal", value=True,
                       help="Animated 9-stage pipeline. Turn off for Instant mode "
                            "(skip straight to the Health Card).")
with c2:
    go = st.button("▶  Run Assessment", type="primary", use_container_width=True)

if go:
    entity_id = selected_id or random_entity_id(engine)
    with st.spinner("Running the assessment pipeline …"):
        state.run(entity_id)
    st.session_state["cp_instant"] = not staged
    if staged:
        st.switch_page("pages/2_Pipeline.py")
    else:
        st.switch_page("pages/3_Financial_Health_Card.py")

st.divider()
st.caption("Offline: `make data-gen` · `make eval` (holdout scorecard) · `make train` "
           "(6-archetype demo) · `make demo` (this app).")
