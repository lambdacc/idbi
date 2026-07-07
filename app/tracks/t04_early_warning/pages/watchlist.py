"""Track 04 · Watchlist & Cases (D11 deep link `watchlist`).

The ranked watchlist plus a per-borrower case drilldown built on the money chart:
the alt-data footprint rolling over months before repayment slips, with three
markers (EWS first alert · baseline first alert · projected default). Opens on the
flagship deteriorating borrower so the demo lands on the money shot. Renders only
what the backend `MonitoringRun` / `CaseDetail` composed. Cold-session safe.
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
from app.frontend.components.ui import badge, kpi, page_header
from app.tracks.t04_early_warning import charts, ui_state
from app.tracks.t04_early_warning.service import SHOWCASE_ENTITY, case_detail

_BAND_KIND = {"Red": "risk", "Amber": "warn", "Green": "good"}
_SELECT_KEY = "cp_t04_case"


def _watchlist_css() -> None:
    st.markdown(
        "<style>"
        ".t04-wl{width:100%;border-collapse:collapse;font-size:.92rem}"
        ".t04-wl th{text-align:left;color:#647587;font-weight:600;font-size:.74rem;"
        "text-transform:uppercase;letter-spacing:.04em;padding:.35rem .6rem;"
        "border-bottom:1px solid #dbe2ec}"
        ".t04-wl td{padding:.5rem .6rem;border-bottom:1px solid #eef2f8}"
        ".t04-wl .rz{color:#647587;font-size:.85rem}"
        "</style>", unsafe_allow_html=True)


def _default_index(entity_ids: list[str]) -> int:
    if SHOWCASE_ENTITY in entity_ids:
        return entity_ids.index(SHOWCASE_ENTITY)
    return 0


def render() -> None:
    run = ui_state.get_monitoring_run()
    engine = ui_state.get_ews_engine()
    technical = ui_state.is_technical()

    page_header("Watchlist & cases",
                "Early Warning – Default Prediction Model · Problem Statement 4 · flagged borrowers "
                "and the alt-data story behind each flag. All data synthetic.")
    st.caption(run.honesty_caption)

    if not run.watchlist:
        st.info("No borrowers are flagged Red or Amber this month.")
        st.page_link(tracks.get_page("t04.portfolio"), label="← Portfolio Overview")
        return

    # ----------------------------------------------------------- watchlist table
    st.subheader("Watchlist")
    _watchlist_css()

    def _table_html(rows) -> str:
        body = ["<table class='t04-wl'><thead><tr>"
                "<th>Band</th><th>Borrower</th><th>Sector</th>"
                "<th>Default risk (12m)</th><th>Days late</th><th>Exposure</th>"
                "<th>Recommended action</th></tr></thead><tbody>"]
        for r in rows:
            body.append(
                "<tr>"
                f"<td>{badge(r.band, _BAND_KIND.get(r.band, 'info'))}</td>"
                f"<td><b>{html.escape(r.name)}</b></td>"
                f"<td class='rz'>{html.escape(r.sector)}</td>"
                f"<td>{r.pd_pct}</td>"
                f"<td>{r.dpd_current:.0f}</td>"
                f"<td>{html.escape(r.exposure_str)}</td>"
                f"<td class='rz'>{html.escape(r.action)}</td>"
                "</tr>")
        body.append("</tbody></table>")
        return "".join(body)

    # Top slice only, so the case drilldown (the money shot) stays near the fold;
    # the full queue lives one click away.
    _TOP_N = 8
    st.markdown(_table_html(run.watchlist[:_TOP_N]), unsafe_allow_html=True)
    _rest = run.watchlist[_TOP_N:]
    if _rest:
        with st.expander(f"Show the remaining {len(_rest)} flagged borrowers"):
            st.markdown(_table_html(_rest), unsafe_allow_html=True)

    st.divider()

    # --------------------------------------------------------------- case picker
    entity_ids = [r.entity_id for r in run.watchlist]
    names = {r.entity_id: r.name for r in run.watchlist}
    st.subheader("Case drilldown")
    selected = st.selectbox(
        "Borrower", options=entity_ids, index=_default_index(entity_ids),
        format_func=lambda e: names.get(e, e), key=_SELECT_KEY)

    case = case_detail(engine, selected)

    # Case header: band chip + PD + exposure + the plain-language headline.
    st.markdown(
        f"<div class='cp-hero'><div class='meta'>"
        f"<div class='name'>{html.escape(case.name)} "
        f"{badge(case.band, _BAND_KIND.get(case.band, 'info'))}</div>"
        f"<div class='subtle'>{html.escape(case.sector)} · {html.escape(case.product)} · "
        f"default risk {case.pd_pct} · exposure {html.escape(case.exposure_str)}</div></div>"
        f"</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='cp-finding {case.tone}'>{html.escape(case.headline)}</div>",
                unsafe_allow_html=True)

    # ------------------------------------------------------------- the money chart
    st.plotly_chart(charts.ews_timeline(case.timeline),
                    use_container_width=True, config=charts.CONFIG, key="t04_money_chart")
    st.caption(case.marker_note)

    # -------------------------------------------------- reasons + action + verdict
    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("**Why this account is flagged**")
        if case.reasons:
            for rz in case.reasons:
                st.markdown(f"<div class='cp-reason neg'><span class='mk'>−</span>"
                            f"<span class='tx'>{html.escape(rz)}</span></div>",
                            unsafe_allow_html=True)
        else:
            st.caption("No drivers above the alert threshold this month.")
    with right:
        st.markdown("**Recommended action**")
        st.markdown(
            f"<div class='cp-card' style='border-top:3px solid var(--cp-navy)'>"
            f"{badge('RBI early-warning action', 'info')}<br><br>"
            f"<b>{html.escape(case.action)}</b><br>"
            f"<span class='subtle'>{html.escape(case.action_gist)}</span></div>",
            unsafe_allow_html=True)

    st.markdown(f"<div class='cp-finding {case.tone}' style='margin-top:.6rem'>"
                f"{html.escape(case.verdict)}</div>", unsafe_allow_html=True)

    # ------------------------------------------------------ technique disclosure
    method = ""
    if technical:
        method = (f"<div class='method'>Method: "
                  f"{html.escape(case.technique_algorithm)}</div>")
    st.markdown(
        f"<div class='cp-technique'><span class='chip'>Technique</span>"
        f"<span class='nm'>{html.escape(case.technique_plain)}</span>"
        f"<div class='bn'>{html.escape(case.technique_benefit)}</div>{method}</div>",
        unsafe_allow_html=True)

    st.page_link(tracks.get_page("t04.portfolio"), label="← Portfolio Overview")
