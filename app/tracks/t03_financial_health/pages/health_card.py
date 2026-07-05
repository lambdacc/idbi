"""Financial Health Card — the executive credit assessment (implementation-plan §5.4 output).

Five labelled dimensions + composite score + 1-10 grade + confidence + peer segment
+ recommendation + top reason codes + the flagship Turnover-Authenticity signal.
"""
from __future__ import annotations

import sys
from pathlib import Path

_p = Path(__file__).resolve()
_ROOT = next((par for par in _p.parents if (par / "requirements.txt").exists()), _p.parents[4])
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import html

import streamlit as st

from app.frontend import tracks
from app.frontend.components import state
from app.frontend.components.glossary import GLOSSARY
from app.frontend.components.stage import render_reasons
from app.frontend.components.ui import (auth_class, badge, band_class, confidence_class,
                                        dimension_bars, fmt_inr, kpi, page_header, risk_class)


def render() -> None:
    a = state.require_assessment()
    hc = a.health_card
    out = a.engine_output

    page_header("Financial health card")

    # Hero + recommendation banner
    st.markdown(
        f"<div class='cp-hero'><div class='score'>{hc.composite_score:.0f}<small>/100</small></div>"
        f"<div class='meta'><div class='name'>{html.escape(hc.name)}</div>"
        f"<div class='subtle'>{a.entity.get('sector','')} · {a.entity.get('category','')} · "
        f"vintage {a.entity.get('age_years','?')}y · {out['sources_connected']}</div>"
        f"<div style='margin-top:.5rem'>{badge('Grade ' + str(hc.grade) + '/10', band_class(hc.onboarding_band))} "
        f"{badge(hc.peer_segment or '-', 'info')}</div></div></div>", unsafe_allow_html=True)

    rk = band_class(hc.onboarding_band)
    st.markdown(
        f"<div class='cp-rec {rk}'>Recommendation: <b>{hc.recommendation}</b> &nbsp;·&nbsp; "
        f"Indicative limit <b>{fmt_inr(hc.indicative_limit)}</b> &nbsp;·&nbsp; "
        f"Onboarding band <b>{hc.onboarding_band.replace('_',' ')}</b></div>", unsafe_allow_html=True)

    # Plain-language verdict — the Issue-1 centrepiece (backend-generated, §CB-9).
    # Sentence 1 carries the band tone, the driver is neutral, the divergence note is a risk.
    _verdict_tones = [band_class(hc.onboarding_band), "neutral", "risk"]
    for _i, _sentence in enumerate(a.verdict):
        _tone = _verdict_tones[_i] if _i < len(_verdict_tones) else "neutral"
        st.markdown(f"<div class='cp-finding {_tone}'>{html.escape(_sentence)}</div>",
                    unsafe_allow_html=True)

    st.write("")
    st.subheader("Five dimensions")
    st.markdown(dimension_bars(hc.pillars, show_eng=state.is_technical()), unsafe_allow_html=True)

    st.divider()
    # "Model PD" is technical-only wording (G4); in simple mode call it by its meaning.
    pd_label = "Model PD" if state.is_technical() else "Estimated default risk"
    # Fraud risk (blended authenticity + unsupervised anomaly cross-check) sits next to
    # the flagship authenticity KPI when available; tone by band.
    _fraud_tone = {"Elevated": "risk", "Moderate": "warn", "Low": "good"}
    has_fraud = hc.fraud_band is not None
    k = st.columns(5 if has_fraud else 4)
    k[0].markdown(kpi("Turnover authenticity", f"{hc.turnover_authenticity_score:.0f}<small>/100</small>",
                  "Flagship check", auth_class(hc.turnover_authenticity_score),
                  tip=GLOSSARY["authenticity"]), unsafe_allow_html=True)
    _i = 1
    if has_fraud:
        k[1].markdown(kpi("Fraud risk", hc.fraud_band,
                      f"{(hc.fraud_risk_score or 0):.0f}/100 blended",
                      _fraud_tone.get(hc.fraud_band, "info"),
                      tip=GLOSSARY["fraud_risk"]), unsafe_allow_html=True)
        _i = 2
    k[_i].markdown(kpi(pd_label, f"{out['pd']:.1%}", out["risk_category"] + " risk",
                  risk_class(out["risk_category"]), tip=GLOSSARY["pd"]), unsafe_allow_html=True)
    k[_i + 1].markdown(kpi("Bureau-style score", f"{out['credit_score_300_900']}<small>/900</small>",
                  "300-900 analogue", tip=GLOSSARY["bureau_score"]), unsafe_allow_html=True)
    k[_i + 2].markdown(kpi("Data confidence", out["confidence_band"], out["sources_connected"],
                  confidence_class(out["confidence_band"]), tip=GLOSSARY["confidence"]),
                  unsafe_allow_html=True)

    st.divider()
    st.subheader("Key strengths and risks")
    render_reasons([r.model_dump() for r in hc.reasons_positive],
                   [r.model_dump() for r in hc.reasons_negative])

    # Authenticity call-out (the differentiator, spelled out)
    auth_reason = next((r.text for r in (hc.reasons_negative + hc.reasons_positive)
                        if r.feature == "turnover_authenticity_score"), None)
    if auth_reason:
        st.markdown(f"<div class='cp-card'><h4>Turnover-authenticity note</h4>{html.escape(auth_reason)}</div>",
                    unsafe_allow_html=True)

    # Honest synthetic-data disclosure + ground-truth reveal for judges.
    with st.expander("Synthetic ground truth (for verification)"):
        st.caption("All data is synthetic. The true ground-truth labels below are hidden from the "
                   "model's scoring path, shown only so you can confirm the assessment caught what it should.")
        g1, g2 = st.columns(2)
        g1.metric("True health", str(a.entity.get("_true_health", "-")))
        g2.metric("True honesty", str(a.entity.get("_true_honesty", "-")))
        if a.entity.get("_true_honesty") == "inflated":
            st.warning("This entity's declared turnover is inflated above its true scale. The "
                       "Turnover-Authenticity composite is designed to catch exactly this, even when "
                       "the raw PD looks benign.")

    st.divider()
    nav = st.columns(3)
    nav[0].page_link(tracks.get_page("t03.explainability"), label="Why this score (explainability)")
    nav[1].page_link(tracks.get_page("t03.dashboard"), label="Dashboard")
    nav[2].page_link(tracks.get_page("t03.run"), label="New assessment")
