"""Dashboard — the commercial-banking-analytics summary of the current run.

Headline cards (score, grade, risk category, suggested limit, PD, confidence) +
the 5-dimension radar. Renders only the active Assessment; no computation here.
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
from app.frontend.components.glossary import GLOSSARY
from app.frontend.components.stage import render_reasons
from app.frontend.components.ui import (auth_class, band_class, confidence_class, fmt_inr,
                                        kpi, page_setup, risk_class, score_class)

page_setup("Dashboard", icon="📈")
a = state.require_assessment()
hc = a.health_card
out = a.engine_output

st.title("Credit Officer Dashboard")

# Hero
st.markdown(
    f"<div class='cp-hero'><div class='score'>{hc.composite_score:.0f}<small>/100</small></div>"
    f"<div class='meta'><div class='name'>{html.escape(hc.name)}</div>"
    f"<div class='subtle'>{a.entity.get('sector','')} · {a.entity.get('category','')} · "
    f"Grade {hc.grade}/10 · Peer group: {hc.peer_segment}</div></div>"
    f"<div style='text-align:right'><div class='score' style='font-size:1.6rem'>{hc.recommendation}</div>"
    f"<div class='subtle'>Onboarding: {hc.onboarding_band.replace('_',' ')}</div></div></div>",
    unsafe_allow_html=True)

# One-line plain-language inference under the hero (reuse the verdict headline).
if a.verdict:
    st.markdown(f"<div class='cp-finding {band_class(hc.onboarding_band)}'>"
                f"{html.escape(a.verdict[0])}</div>", unsafe_allow_html=True)

# Sub-lines carrying "Model PD" are technical-only wording (G4); reword in simple mode.
_tech = state.is_technical()
risk_sub = (f"Model PD {out['pd']:.1%} · score {out['credit_score_300_900']}/900" if _tech
            else f"Est. default risk {out['pd']:.1%} · score {out['credit_score_300_900']}/900")
peer_sub = "K-Means (descriptive only)" if _tech else "compared with similar businesses"

# KPI row
r1 = st.columns(3)
r1[0].markdown(kpi("Financial Health Score", f"{hc.composite_score:.0f}<small>/100</small>",
               f"CMR-style grade {hc.grade}/10", score_class(hc.composite_score),
               tip=GLOSSARY["financial_health_score"]), unsafe_allow_html=True)
r1[1].markdown(kpi("Risk category", out["risk_category"], risk_sub,
               risk_class(out["risk_category"]), tip=GLOSSARY["pd"]), unsafe_allow_html=True)
r1[2].markdown(kpi("Suggested credit limit", fmt_inr(hc.indicative_limit),
               f"Recommendation: {hc.recommendation}", band_class(hc.onboarding_band),
               tip=GLOSSARY["indicative_limit"]), unsafe_allow_html=True)

r2 = st.columns(3)
r2[0].markdown(kpi("Turnover authenticity", f"{hc.turnover_authenticity_score:.0f}<small>/100</small>",
               "Flagship cross-source check", auth_class(hc.turnover_authenticity_score),
               tip=GLOSSARY["authenticity"]), unsafe_allow_html=True)
r2[1].markdown(kpi("Data confidence", out["confidence_band"],
               out["sources_connected"], confidence_class(out["confidence_band"]),
               tip=GLOSSARY["confidence"]), unsafe_allow_html=True)
r2[2].markdown(kpi("Peer segment", hc.peer_segment or "—", peer_sub,
               tip=GLOSSARY["peer_segment"]), unsafe_allow_html=True)

st.divider()
left, right = st.columns([1, 1])
with left:
    st.subheader("Five Dimensions")
    st.plotly_chart(charts.radar([p.label for p in hc.pillars], [p.score for p in hc.pillars]),
                    use_container_width=True)
with right:
    st.subheader("What Drove This")
    render_reasons([r.model_dump() for r in hc.reasons_positive],
                   [r.model_dump() for r in hc.reasons_negative])

st.divider()
nav = st.columns(4)
nav[0].page_link("pages/2_Pipeline.py", label="⚙️  Pipeline")
nav[1].page_link("pages/3_Financial_Health_Card.py", label="📋  Health Card")
nav[2].page_link("pages/4_Explainability.py", label="🔍  Explainability")
nav[3].page_link("Home.py", label="🏠  New assessment")
