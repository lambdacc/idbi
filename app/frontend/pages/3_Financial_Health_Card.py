"""Financial Health Card — the executive credit assessment (implementation-plan §5.4 output).

Five labelled dimensions + composite score + 1-10 grade + confidence + peer segment
+ recommendation + top reason codes + the flagship Turnover-Authenticity signal.
"""
from __future__ import annotations

import sys
from pathlib import Path

_p = Path(__file__).resolve()
_ROOT = next((par for par in _p.parents if (par / "requirements.txt").exists()), _p.parents[3])
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import html

import streamlit as st

from app.frontend.components import charts, state
from app.frontend.components.stage import render_reasons
from app.frontend.components.ui import (auth_class, badge, band_class, confidence_class,
                                        fmt_inr, kpi, page_setup, risk_class, score_class)

page_setup("Financial Health Card", icon="📋")
a = state.require_assessment()
hc = a.health_card
out = a.engine_output

st.title("Financial Health Card")

# Hero + recommendation banner
st.markdown(
    f"<div class='cp-hero'><div class='score'>{hc.composite_score:.0f}<small>/100</small></div>"
    f"<div class='meta'><div class='name'>{hc.name}</div>"
    f"<div class='subtle'>{a.entity.get('sector','')} · {a.entity.get('category','')} · "
    f"vintage {a.entity.get('age_years','?')}y · {out['sources_connected']}</div>"
    f"<div style='margin-top:.5rem'>{badge('Grade ' + str(hc.grade) + '/10', band_class(hc.onboarding_band))} "
    f"{badge(hc.peer_segment or '—', 'info')}</div></div></div>", unsafe_allow_html=True)

rk = band_class(hc.onboarding_band)
st.markdown(
    f"<div class='cp-rec {rk}'>Recommendation: <b>{hc.recommendation}</b> &nbsp;·&nbsp; "
    f"Indicative limit <b>{fmt_inr(hc.indicative_limit)}</b> &nbsp;·&nbsp; "
    f"Onboarding band <b>{hc.onboarding_band.replace('_',' ')}</b></div>", unsafe_allow_html=True)

st.write("")
left, right = st.columns([1, 1])
with left:
    st.subheader("Five dimensions")
    st.plotly_chart(charts.radar([p.label for p in hc.pillars], [p.score for p in hc.pillars]),
                    use_container_width=True)
with right:
    st.subheader("Dimension scores")
    for p in hc.pillars:
        cls = score_class(p.score)
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;padding:.3rem 0'>"
            f"<span>{html.escape(p.label)} "
            f"<span class='cp-scn'>({html.escape(p.engineering_name)})</span></span>"
            f"{badge(f'{p.score:.0f}/100', cls)}</div>", unsafe_allow_html=True)

st.divider()
k = st.columns(4)
k[0].markdown(kpi("Turnover authenticity", f"{hc.turnover_authenticity_score:.0f}<small>/100</small>",
              "Flagship check", auth_class(hc.turnover_authenticity_score)), unsafe_allow_html=True)
k[1].markdown(kpi("Model PD", f"{out['pd']:.1%}", out["risk_category"] + " risk",
              risk_class(out["risk_category"])), unsafe_allow_html=True)
k[2].markdown(kpi("Bureau-style score", f"{out['credit_score_300_900']}<small>/900</small>",
              "300-900 analogue"), unsafe_allow_html=True)
k[3].markdown(kpi("Data confidence", out["confidence_band"], out["sources_connected"],
              confidence_class(out["confidence_band"])), unsafe_allow_html=True)

st.divider()
st.subheader("Key strengths & risks")
render_reasons([r.model_dump() for r in hc.reasons_positive],
               [r.model_dump() for r in hc.reasons_negative])

# Authenticity call-out (the differentiator, spelled out)
auth_reason = next((r.text for r in (hc.reasons_negative + hc.reasons_positive)
                    if r.feature == "turnover_authenticity_score"), None)
if auth_reason:
    st.markdown(f"<div class='cp-card'><h4>Turnover-Authenticity note</h4>{html.escape(auth_reason)}</div>",
                unsafe_allow_html=True)

# Honest synthetic-data disclosure + ground-truth reveal for judges.
with st.expander("Synthetic ground truth (for verification)"):
    st.caption("All data is synthetic. The latent ground-truth labels below are hidden from the "
               "model's scoring path — shown only so you can confirm the assessment caught what it should.")
    g1, g2 = st.columns(2)
    g1.metric("Latent health", str(a.entity.get("_true_health", "—")))
    g2.metric("Latent honesty", str(a.entity.get("_true_honesty", "—")))
    if a.entity.get("_true_honesty") == "inflated":
        st.warning("This entity's declared turnover is inflated above its true scale — the "
                   "Turnover-Authenticity composite is designed to catch exactly this, even when "
                   "the raw PD looks benign.")

st.divider()
nav = st.columns(3)
nav[0].page_link("pages/4_Explainability.py", label="🔍  Why this score (Explainability)")
nav[1].page_link("pages/1_Dashboard.py", label="📈  Dashboard")
nav[2].page_link("Home.py", label="🏠  New assessment")
