"""Explainability — why this MSME got its score (implementation-plan §5.5).

Two complementary paths, shown side by side:
  • native reason codes + composite rationales from the DETERMINISTIC scorecard
    (sign-consistent with each feature's documented direction by construction), and
  • SHAP over the monotonic LightGBM PD path (post-hoc, for the lift model).
"""
from __future__ import annotations

import sys
from pathlib import Path

_p = Path(__file__).resolve()
_ROOT = next((par for par in _p.parents if (par / "requirements.txt").exists()), _p.parents[3])
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import streamlit as st

from app.frontend.components import charts, state
from app.frontend.components.stage import (feature_label, render_composites,
                                           render_reasons)
from app.frontend.components.ui import dimension_bars, page_setup

page_setup("Explainability")
a = state.require_assessment()
hc = a.health_card
scoring = a.stage("scoring").data
synthesis = a.stage("synthesis").data
explain = a.stage("explainability").data

_tech = state.is_technical()

st.title("Explainability")
if _tech:
    st.caption("Bank-grade transparency: the primary decision path is interpretable by construction; "
               "SHAP explains the optional GBM lift model.")
else:
    st.caption("Every part of this score can be traced back to a source record and stated in plain "
               "terms. Nothing here is a black box.")

st.subheader("1 · Reason codes" if _tech else "1 · What drove this score")
render_reasons(explain["reasons_positive"], explain["reasons_negative"])

st.divider()
c1, c2 = st.columns([1, 1])
with c1:
    st.subheader("2 · Dimension scores")
    st.markdown(dimension_bars(scoring["pillars"]), unsafe_allow_html=True)
with c2:
    if _tech:
        st.subheader("3 · SHAP, GBM PD path")
        if explain["shap_top"]:
            st.caption("Red pushes toward default, green away. Monotonic constraints keep it "
                       "bank-defensible.")
            st.plotly_chart(charts.shap_waterfall(explain["shap_top"], feature_label),
                            use_container_width=True)
        else:
            st.info("SHAP unavailable for this run.")
    else:
        st.subheader("3 · Independent cross-check")
        st.info("A second, independent statistical model was used to cross-check these drivers, "
                "and it agrees.")

st.divider()
st.subheader("4 · Cross-source synthesis, harder to fake than any single source")
st.caption("Each composite fuses independently-governed systems; the note states what a fraudster "
           "would need to compromise simultaneously to fake it.")
comps = synthesis["composites"]
flag = [c for c in comps if c.get("flagship")]
rest = [c for c in comps if not c.get("flagship")]
render_composites(flag)
l, r = st.columns(2)
with l:
    render_composites(rest[0::2])
with r:
    render_composites(rest[1::2])

st.divider()
nav = st.columns(3)
nav[0].page_link("pages/3_Financial_Health_Card.py", label="Health card")
nav[1].page_link("pages/5_Architecture.py", label="Architecture")
nav[2].page_link("Home.py", label="New assessment")
