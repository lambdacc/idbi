"""Track 05 · Fraud Desk (SentinelPulse) — the flagged-account queue (WP-5A).

Renders ONLY the ``desk_snapshot`` payload the backend composes (module boundary
D6): a KPI row, the alert queue (band colours + pattern chips), the desk-wide
pattern distribution, and a "why this track" card. Selecting an account seeds
``cp_case_account`` and switches to Case Investigation. Two prominent shortcuts
open the flagship ring and — the differentiator — a cleared high-velocity account.
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
from app.frontend.components.ui import kpi, page_header

from .. import charts, session
from ..case_orchestrator import desk_snapshot
from ..glossary import GLOSSARY

_CSS = """
<style>
.t05-chip{display:inline-block;background:#eef2f8;color:#0b3d75;border:1px solid #d6deea;
  border-radius:10px;padding:1px 8px;margin:1px 3px 1px 0;font-size:.72rem;white-space:nowrap;}
.t05-qtable{width:100%;border-collapse:collapse;font-size:.86rem;}
.t05-qtable th{text-align:left;color:#647587;font-weight:600;font-size:.74rem;
  text-transform:uppercase;letter-spacing:.03em;padding:6px 10px;border-bottom:2px solid #dbe2ec;}
.t05-qtable td{padding:8px 10px;border-bottom:1px solid #eef2f8;vertical-align:top;}
.t05-qtable td.acc{font-family:'IBM Plex Mono',ui-monospace,monospace;font-weight:600;}
.t05-qtable td.sc{font-family:'IBM Plex Mono',ui-monospace,monospace;text-align:right;}
.t05-why{border-top:3px solid #0b3d75;}
.t05-why li{margin:.25rem 0;}
</style>
"""

_BAND_KIND = {"Alert": "risk", "Review": "warn", "Clear": "good"}


def _band_badge(band: str) -> str:
    kind = _BAND_KIND.get(band, "info")
    return f"<span class='cp-badge {kind}'>{html.escape(band)}</span>"


def _queue_table(queue, technical: bool, limit: int = 25) -> str:
    key = "typology_labels" if technical else "typology_labels_plain"
    rows = []
    for q in queue[:limit]:
        chips = "".join(f"<span class='t05-chip'>{html.escape(c)}</span>"
                        for c in q[key]) or "<span class='t05-chip'>—</span>"
        rows.append(
            f"<tr><td class='acc'>{html.escape(q['account'])}</td>"
            f"<td class='sc'>{q['score']:.0f}</td>"
            f"<td>{_band_badge(q['band'])}</td>"
            f"<td>{chips}</td>"
            f"<td class='sc'>{html.escape(q['exposure_display'])}</td></tr>")
    return (
        "<table class='t05-qtable'><thead><tr>"
        "<th>Account</th><th>Score</th><th>Band</th>"
        "<th>Behaviour patterns</th><th>Est. exposure</th>"
        "</tr></thead><tbody>" + "".join(rows) + "</tbody></table>")


def _open_case(account_id: str) -> None:
    session.set_case_account(account_id)
    st.switch_page(tracks.get_page("t05.case"))


def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    technical = state.is_technical()
    engine = session.get_fraud_engine()
    snap = desk_snapshot(engine)

    page_header("Fraud Desk",
                "Problem Statement 5 (Open Innovation) · SentinelPulse — explainable detection of "
                "rented-out accounts, queued for citation-gated investigation.")

    st.caption(snap["scope_note"] + "  All figures illustrative on synthetic data.")

    # KPI row
    cols = st.columns(len(snap["kpis"]))
    for col, k in zip(cols, snap["kpis"]):
        col.markdown(kpi(k["label"], k["value"], k["sub"], k["kind"]),
                     unsafe_allow_html=True)

    # Why-this-track card
    lis = "".join(f"<li>{html.escape(line)}</li>" for line in snap["why_track"])
    st.markdown(
        f"<div class='cp-card t05-why'><h4>Why this desk exists</h4>"
        f"<ul>{lis}</ul></div>", unsafe_allow_html=True)

    st.divider()

    left, right = st.columns([1.7, 1])
    with left:
        st.subheader("Accounts on the desk")
        st.markdown(_queue_table(snap["queue"], technical), unsafe_allow_html=True)
        if len(snap["queue"]) > 25:
            st.caption(f"Showing the 25 highest-scoring of {len(snap['queue'])} "
                       "flagged accounts.")
    with right:
        st.subheader("Pattern distribution")
        st.plotly_chart(charts.typology_bar(snap["typology_distribution"],
                                            plain=not technical),
                        use_container_width=True, key="t05_desk_typbar")

    st.divider()

    # Investigation launchers — one account picker + two prominent shortcuts.
    st.subheader("Open an investigation")
    ids = [q["account"] for q in snap["queue"]]
    default = snap["default_case"] if snap["default_case"] in ids else (ids[0] if ids else None)
    pick_cols = st.columns([2, 1])
    with pick_cols[0]:
        chosen = st.selectbox(
            "Pick a flagged account", ids,
            index=ids.index(default) if default in ids else 0,
            help="Every account here scored into the Review or Alert band.")
    with pick_cols[1]:
        st.markdown("<div style='height:1.75rem'></div>", unsafe_allow_html=True)
        if st.button("Investigate", use_container_width=True, type="primary"):
            _open_case(chosen)

    shortcut = st.columns(2)
    with shortcut[0]:
        if snap["default_case"] and st.button(
                f"🕸  Open the flagged ring · {snap['default_case']}",
                use_container_width=True):
            _open_case(snap["default_case"])
        st.caption("A top-band account sitting inside a linked cluster of accounts.")
    with shortcut[1]:
        if snap["hard_negative"] and st.button(
                f"✅  A cleared high-velocity account · {snap['hard_negative']}",
                use_container_width=True):
            _open_case(snap["hard_negative"])
        st.caption("Busy, but genuine — the desk explains why it stays cleared "
                   "(the case rules can't make).")

    # Glossary. Titles are the plain synonym so Simple mode never shows raw jargon;
    # the "typology" term itself is Technical-only.
    _titles = {"mule_account": "Rented-out (mule) account" if technical else "Rented-out account",
               "ring": "Account ring", "cash_out": "Cash-out point",
               "typology": "Typology (behaviour pattern)", "citation_gate": "Citation gate"}
    with st.expander("What the words mean"):
        keys = ["mule_account", "ring", "cash_out"]
        if technical:
            keys.append("typology")
        keys.append("citation_gate")
        for k in keys:
            st.markdown(f"**{_titles[k]}** — {GLOSSARY[k]}")
