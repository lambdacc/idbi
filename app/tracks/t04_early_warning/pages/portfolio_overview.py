"""Track 04 · Portfolio Overview (D11 deep link `track04`).

The book-level early-warning radar: a KPI row, the Green/Amber/Red distribution,
this month's migration, and a flagged-accounts table with per-row plain-language
drivers. Renders only what the backend `MonitoringRun` composed — no computation,
no copy generation here (multi-track D6). Cold-session safe: with no seeded state
it fits the engine and composes a default run rather than raising.
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

_BAND_KIND = {"Red": "risk", "Amber": "warn", "Green": "good"}


def _table_css() -> None:
    st.markdown(
        "<style>"
        ".t04-tbl{width:100%;border-collapse:collapse;font-size:.92rem}"
        ".t04-tbl th{text-align:left;color:#647587;font-weight:600;font-size:.74rem;"
        "text-transform:uppercase;letter-spacing:.04em;padding:.35rem .6rem;"
        "border-bottom:1px solid #dbe2ec}"
        ".t04-tbl td{padding:.5rem .6rem;border-bottom:1px solid #eef2f8;vertical-align:top}"
        ".t04-tbl tr:hover td{background:rgba(11,61,117,0.03)}"
        ".t04-tbl .rz{color:#647587;font-size:.85rem}"
        "</style>", unsafe_allow_html=True)


def render() -> None:
    run = ui_state.get_monitoring_run()
    technical = ui_state.is_technical()

    page_header("Portfolio early warning",
                "Problem Statement 4 (Default Prediction Model) · Early Warning — the book re-scored "
                "monthly on its alt-data footprint. All data synthetic.")

    st.caption(run.honesty_caption)

    # KPI rows (all copy pre-composed by the backend).
    for start in range(0, len(run.kpis), 3):
        cols = st.columns(3)
        for col, k in zip(cols, run.kpis[start:start + 3]):
            col.markdown(kpi(k.label, k.value, k.sub, k.kind, tip=k.tip),
                         unsafe_allow_html=True)
    st.caption(run.exposure_caption)

    st.divider()
    left, right = st.columns([1, 1])
    with left:
        st.subheader("Band distribution")
        st.plotly_chart(charts.band_bar(run.band_counts),
                        use_container_width=True, config=charts.CONFIG,
                        key="t04_band_bar")
    with right:
        st.subheader("This month's movers")
        mig = run.migration
        if mig.get("movers"):
            st.markdown(
                f"<div class='cp-finding warn'><b>{mig['worsened']}</b> account(s) "
                f"escalated a band since last month — {mig['new_red']} newly Red, "
                f"{mig['new_amber']} newly Amber. {mig['improved']} improved.</div>",
                unsafe_allow_html=True)
        else:
            st.markdown("<div class='cp-finding neutral'>No band changes versus last "
                        "month on record.</div>", unsafe_allow_html=True)
        st.caption("Movers are accounts whose traffic-light band changed versus the "
                   "prior monthly re-score.")

    st.divider()
    st.subheader("Flagged accounts")
    st.caption("Red and Amber borrowers, worst first. Open the Watchlist for the "
               "full drilldown and timeline.")
    _table_css()
    rows = run.watchlist[:12]
    if not rows:
        st.info("No borrowers are flagged Red or Amber this month.")
    else:
        body = ["<table class='t04-tbl'><thead><tr>"
                "<th>Band</th><th>Borrower</th><th>Sector</th>"
                "<th>Default risk (12m)</th><th>Exposure</th><th>Why flagged</th>"
                "</tr></thead><tbody>"]
        for r in rows:
            reason = r.reasons[0] if r.reasons else "overall deterioration"
            new = (" " + badge("new", "info")) if r.is_new else ""
            body.append(
                "<tr>"
                f"<td>{badge(r.band, _BAND_KIND.get(r.band, 'info'))}{new}</td>"
                f"<td><b>{html.escape(r.name)}</b></td>"
                f"<td class='rz'>{html.escape(r.sector)}</td>"
                f"<td>{r.pd_pct}</td>"
                f"<td>{html.escape(r.exposure_str)}</td>"
                f"<td class='rz'>{html.escape(reason)}</td>"
                "</tr>")
        body.append("</tbody></table>")
        st.markdown("".join(body), unsafe_allow_html=True)

    st.page_link(tracks.get_page("t04.watchlist"),
                 label="Open the Watchlist & case drilldown →")

    # Technical extras: the eval scorecard + the staged monitoring disclosure.
    if technical:
        st.divider()
        with st.expander("Evaluation scorecard (entity-level holdout)", expanded=False):
            c = st.columns(3)
            c[0].markdown(kpi("Median lead · EWS", f"{run.median_lead_ews:.1f} mo",
                          f"baseline {run.median_lead_baseline:.1f} mo", "good"),
                          unsafe_allow_html=True)
            c[1].markdown(kpi("Capture @ top decile", f"{run.capture_ews:.0%}",
                          f"baseline {run.capture_baseline:.0%}"), unsafe_allow_html=True)
            c[2].markdown(kpi("Red alert precision / recall",
                          f"{run.alert_precision:.0%} / {run.alert_recall:.0%}",
                          f"false-alert {run.false_alert_rate:.0%} · AUC {run.holdout_auc_ews:.2f}"),
                          unsafe_allow_html=True)
            st.caption("Lead time is the headline, not accuracy: how many months "
                       "earlier the alt-data model turns Red than the repayment-only "
                       "baseline. Computed on a held-out slice of the synthetic book.")
        with st.expander("How the monitor ran (deterministic staged orchestration)",
                         expanded=False):
            for s in run.stages:
                st.markdown(f"**Stage {s.index} · {s.title}** — {html.escape(s.headline)}")
                if s.technique:
                    st.caption("Method: " + s.technique.get("algorithm", ""))
            st.caption("No runtime LLM: each stage is a deterministic step in the "
                       "monitoring pipeline, disclosed here for auditability.")
