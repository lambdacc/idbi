"""Track 05 · Case Investigation (SentinelPulse) — the showpiece (WP-5A).

The staged agentic investigation for one flagged account, rendered with the
existing pipeline components (stage rail left · live output right · notebook cells
below — the same contract as the T03 pipeline; instant mode honoured via
``cp_instant``). Below the run sits the case file: grounds of suspicion with
citation expanders that open the actual transactions, the suspected-ring diagram,
the recommendation, and an Approve / Override gate that appends to a deterministic
audit trail.

Renders ONLY the ``CaseFile`` the orchestrator composes (D6). Cold-session safe:
with no ``cp_case_account`` seeded it shows a friendly empty state, never an error.
"""
from __future__ import annotations

import sys
from pathlib import Path

_p = Path(__file__).resolve()
_ROOT = next((par for par in _p.parents if (par / "requirements.txt").exists()), _p.parents[4])
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import html
import time

import streamlit as st

from app.frontend import tracks
from app.frontend.components import state
from app.frontend.components.stage import (console_html, render_findings,
                                           render_stage_cell, render_technique,
                                           stage_list_html)
from app.frontend.components.ui import badge, kpi, page_header

from .. import charts, session
from ..case_orchestrator import investigate
from ..glossary import GLOSSARY

_CSS = """
<style>
.t05-rec{border-top:4px solid var(--cp-navy);padding:1rem 1.1rem;}
.t05-rec.risk{border-top-color:#c0392b;}
.t05-rec.warn{border-top-color:#8f5c13;}
.t05-rec.good{border-top-color:#147347;}
.t05-rec .rc{font-size:1.15rem;font-weight:700;margin-bottom:.35rem;}
.t05-atable{width:100%;border-collapse:collapse;font-size:.86rem;}
.t05-atable th{text-align:left;color:#647587;font-weight:600;font-size:.72rem;
  text-transform:uppercase;letter-spacing:.03em;padding:6px 10px;border-bottom:2px solid #dbe2ec;}
.t05-atable td{padding:7px 10px;border-bottom:1px solid #eef2f8;}
.t05-atable td.n{font-family:'IBM Plex Mono',ui-monospace,monospace;color:#647587;}
.t05-dtable td{padding:2px 8px;font-size:.85rem;}
</style>
"""

_PLAYED_KEY = "cp_case_played"
_TXN_COLS = ["txn_id", "datetime", "direction", "amount", "channel",
             "counterparty_id", "device_id", "balance_after"]


# --------------------------------------------------------------------- empty state
def _empty_state() -> None:
    st.markdown("<h1>No case selected</h1>", unsafe_allow_html=True)
    st.markdown(
        "<div class='cp-card' style='border-top:3px solid var(--cp-navy)'>"
        "Pick an account on the <b>Fraud Desk</b> and open its investigation. "
        "SentinelPulse will run its specialist agents and assemble a "
        "citation-gated case file for your decision.</div>",
        unsafe_allow_html=True)
    st.page_link(tracks.get_page("t05.desk"), label="Go to the Fraud Desk")


# --------------------------------------------------------------- per-stage detail
def _stage_detail(container, stage, cf, technical: bool) -> None:
    """Track-05 per-stage visualization (the ring chart + citations live in the
    dedicated case-file section below, so stage cells stay light)."""
    d = stage.data
    with container.container():
        if stage.key == "triage":
            c = st.columns(4)
            c[0].markdown(kpi("Blended score", f"{d['score']:.0f}<small>/100</small>",
                          d["band"], _BAND_KIND.get(d["band"], "")), unsafe_allow_html=True)
            c[1].markdown(kpi("Pattern strength", f"{d['typology_component']:.0f}",
                          "rule-based leg"), unsafe_allow_html=True)
            c[2].markdown(kpi("Anomaly reading", f"{d['anomaly_component']:.0f}",
                          "independent leg"), unsafe_allow_html=True)
            c[3].markdown(kpi("Patterns fired", str(d["n_typologies"]),
                          "behavioural tells"), unsafe_allow_html=True)

        elif stage.key == "evidence":
            grounds = d["grounds"]
            if not grounds:
                st.caption("No evidenced grounds — see the clearance reasoning below.")
            for g in grounds:
                label = g["label"] if technical else g["plain_label"]
                st.markdown(
                    f"<div class='cp-finding {_hit_tone(g['score'])}' "
                    "style='display:flex;justify-content:space-between'>"
                    f"<span>{html.escape(label)}</span>"
                    f"<span style='color:#647587'>{g['citation_count']} cited txn(s)</span>"
                    "</div>", unsafe_allow_html=True)

        elif stage.key == "network":
            c = st.columns(4)
            c[0].markdown(kpi("Linked accounts", str(d["size"]),
                          "in the cluster"), unsafe_allow_html=True)
            c[1].markdown(kpi("Cash-out points", str(d["n_cashout"]),
                          "money leaves as cash", "risk" if d["n_cashout"] else ""),
                          unsafe_allow_html=True)
            c[2].markdown(kpi("Forwarding hubs", str(d["n_recruiter"]),
                          "pass funds onward"), unsafe_allow_html=True)
            c[3].markdown(kpi("Top-band members", str(d["n_alert"]),
                          "confirmed high-risk", "risk" if d["n_alert"] else ""),
                          unsafe_allow_html=True)

        elif stage.key == "adjudication":
            rec = d["recommendation"] if technical else d["recommendation_plain"]
            tone = {"Freeze + file STR draft": "risk", "Enhanced monitoring": "warn",
                    "Clear with note": "good"}.get(d["recommendation"], "info")
            st.markdown(badge(rec, tone), unsafe_allow_html=True)
            if technical:
                rows = "".join(
                    f"<tr><td>{'✓' if r['hit'] else '·'}</td>"
                    f"<td>{html.escape(r['rule'])}</td></tr>" for r in d["decision_rows"])
                st.markdown(f"<table class='t05-dtable'>{rows}</table>",
                            unsafe_allow_html=True)

        elif stage.key == "casefile":
            c = st.columns(3)
            c[0].markdown(kpi("Grounds", str(len(d["grounds"])),
                          "of suspicion"), unsafe_allow_html=True)
            c[1].markdown(kpi("Cited transactions", str(len(d["txn_annexure_ids"])),
                          "every claim sourced"), unsafe_allow_html=True)
            c[2].markdown(kpi("Ring annexure", str(len(d["ring_annexure"])),
                          "account(s)"), unsafe_allow_html=True)


_BAND_KIND = {"Alert": "risk", "Review": "warn", "Clear": "good"}


def _hit_tone(score: float) -> str:
    return "risk" if score >= 65 else ("warn" if score >= 45 else "neutral")


# --------------------------------------------------------------- staged run
def _run_stages(cf, technical: bool) -> None:
    stages = cf.stages
    instant = st.session_state.get("cp_instant", False)
    already = st.session_state.get(_PLAYED_KEY) == cf.account_id

    top = st.columns([1, 1, 3])
    with top[0]:
        if st.button("Skip to result", use_container_width=True):
            st.session_state[_PLAYED_KEY] = cf.account_id
            already = True
    with top[1]:
        if st.button("Replay", use_container_width=True):
            st.session_state[_PLAYED_KEY] = None
            st.rerun()

    left, right = st.columns([1, 1.6])
    stage_ph = left.empty()
    progress_ph = left.empty()
    right.markdown("<div class='cp-live-anchor'></div>", unsafe_allow_html=True)
    detail_ph = right.empty()
    console_ph = right.empty() if technical else None
    cells = st.container()

    def cell_detail(container, stage) -> None:
        _stage_detail(container, stage, cf, technical)

    play = not (instant or already)
    if play:
        log_lines: list[str] = []
        bar = progress_ph.progress(0.0, text="Starting …")
        for i, s in enumerate(stages, start=1):
            stage_ph.markdown(stage_list_html(stages, s.index), unsafe_allow_html=True)
            bar.progress((i - 1) / len(stages),
                         text=f"Stage {s.index}/{len(stages)} · {s.title}")
            for ln in s.log:
                log_lines.append(ln)
                if console_ph is not None:
                    console_ph.markdown(console_html(log_lines[-22:], short=True),
                                        unsafe_allow_html=True)
                time.sleep(0.04)
            with detail_ph.container():
                st.markdown(f"#### Stage {s.index} · {s.title}")
                st.caption(s.caption)
                render_technique(s.technique, technical)
                render_findings(s.findings, technical)
                _stage_detail(st.container(), s, cf, technical)
            time.sleep(min(s.duration, 1.2) * 0.3)
            if i < len(stages):
                with cells:
                    render_stage_cell(s, technical, expanded=False, detail_fn=cell_detail)
        stage_ph.markdown(stage_list_html(stages, len(stages) + 1), unsafe_allow_html=True)
        bar.progress(1.0, text="Investigation complete")
        detail_ph.empty()
        with cells:
            render_stage_cell(stages[-1], technical, expanded=True, detail_fn=cell_detail)
        st.session_state[_PLAYED_KEY] = cf.account_id
    else:
        stage_ph.markdown(stage_list_html(stages, len(stages) + 1), unsafe_allow_html=True)
        progress_ph.progress(1.0, text="Investigation complete")
        if console_ph is not None:
            all_lines = [ln for s in stages for ln in s.log]
            console_ph.markdown(console_html(all_lines, short=True), unsafe_allow_html=True)
        with cells:
            for s in stages:
                render_stage_cell(s, technical, expanded=(s.index == len(stages)),
                                  detail_fn=cell_detail)


# --------------------------------------------------------------- case-file section
def _citation_table(txn_ids, txns):
    present = [t for t in txn_ids if t in txns.index]
    if not present:
        return None
    sub = txns.loc[present]
    cols = [c for c in _TXN_COLS if c in sub.columns]
    return sub[cols].reset_index(drop=True)


def _render_grounds(cf, technical: bool, txns) -> None:
    st.subheader("Grounds of suspicion")
    if not cf.grounds:
        st.markdown(
            f"<div class='cp-finding good'>{html.escape(cf.rationale[0] if cf.rationale else '')}"
            "</div>", unsafe_allow_html=True)
        return
    st.caption("Every ground opens the exact transactions that triggered it — "
               "no claim without a receipt.")
    for i, g in enumerate(cf.grounds, start=1):
        label = g.label if technical else g.plain_label
        with st.expander(f"Ground {i} · {label} — {len(g.txn_ids)} cited transaction(s)",
                         expanded=(i == 1)):
            st.markdown(f"<div class='cp-finding {_hit_tone(g.score)}'>"
                        f"{html.escape(g.plain)}</div>", unsafe_allow_html=True)
            tbl = _citation_table(g.txn_ids, txns)
            if tbl is not None:
                st.dataframe(tbl, use_container_width=True, hide_index=True)
                if len(g.txn_ids) > len(tbl):
                    st.caption(f"Showing {len(tbl)} of {len(g.txn_ids)} cited "
                               "transactions (representative sample).")
            if technical and g.counterparties:
                st.caption("Counterparties implicated: "
                           + ", ".join(map(str, g.counterparties[:12])))


def _render_ring(cf, technical: bool) -> None:
    net = cf.stage("network").data
    st.subheader("Suspected ring")
    if net["size"] <= 1:
        st.caption("This account is not linked to any other in the ledger.")
        return
    st.caption("Nodes are accounts; dotted links are a shared device, solid links "
               "are repeated transfers. Red marks a confirmed top-band account.")
    st.plotly_chart(charts.ring_network(cf.ring, cf.roles, net["bands"],
                                        plain=not technical),
                    use_container_width=True, key="t05_ring")


def _render_recommendation(cf, technical: bool) -> None:
    tone = _BAND_KIND.get(cf.band, "info")
    rec = cf.recommendation if technical else cf.recommendation_plain
    body = "".join(f"<p style='margin:.2rem 0'>{html.escape(line)}</p>"
                   for line in cf.rationale)
    st.markdown(
        f"<div class='cp-card t05-rec {tone}'><div class='rc'>Recommendation · "
        f"{html.escape(rec)}</div>{body}</div>", unsafe_allow_html=True)


def _render_decision_gate(cf) -> None:
    st.subheader("Analyst decision")
    st.caption("SentinelPulse only recommends — you decide. Every decision is "
               "recorded in the audit trail below.")
    note = st.text_input("Note (optional — recommended for an override)", key="t05_note")
    cols = st.columns(2)
    with cols[0]:
        if st.button("✅ Approve recommendation", use_container_width=True, type="primary"):
            session.record_decision(cf.account_id, "Approved", cf.recommendation, note)
            st.rerun()
    with cols[1]:
        if st.button("✋ Override", use_container_width=True):
            session.record_decision(cf.account_id, "Overridden", cf.recommendation, note)
            st.rerun()

    audit = session.get_audit()
    if audit:
        rows = "".join(
            f"<tr><td class='n'>{e['n']}</td><td>{html.escape(str(e['account']))}</td>"
            f"<td>{html.escape(e['action'])}</td>"
            f"<td>{html.escape(e['recommendation'])}</td>"
            f"<td>{html.escape(e.get('note') or '—')}</td></tr>" for e in audit)
        st.markdown(
            "<table class='t05-atable'><thead><tr><th>#</th><th>Account</th>"
            "<th>Decision</th><th>On recommendation</th><th>Note</th></tr></thead>"
            f"<tbody>{rows}</tbody></table>", unsafe_allow_html=True)
    else:
        st.caption("No decisions recorded yet.")


# --------------------------------------------------------------- entry point
def render() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
    if not session.has_case_account():
        _empty_state()
        return

    account_id = session.get_case_account()
    technical = state.is_technical()
    engine = session.get_fraud_engine()
    txns = session.load_transactions()
    cf = investigate(engine, account_id)

    page_header(f"Case · {account_id}",
                f"Score {cf.score:.0f}/100 · band {cf.band} · a citation-gated, "
                "agentic investigation assembled for your decision.")
    st.markdown(
        badge(cf.band, _BAND_KIND.get(cf.band, "info"))
        + f" &nbsp; <span class='cp-scn'>{html.escape(cf.recommendation_plain)}</span>",
        unsafe_allow_html=True)

    st.divider()
    _run_stages(cf, technical)

    st.divider()
    st.header("Case file")
    left, right = st.columns([1, 1])
    with left:
        _render_grounds(cf, technical, txns)
    with right:
        _render_ring(cf, technical)
    _render_recommendation(cf, technical)
    st.divider()
    _render_decision_gate(cf)

    with st.expander("What the words mean"):
        keys = ["mule_account", "citation_gate", "cash_out"]
        if technical:
            keys.insert(1, "typology")
        for k in keys:
            title = {"mule_account": "Rented-out account", "typology": "Typology",
                     "citation_gate": "Citation gate", "cash_out": "Cash-out point"}[k]
            st.markdown(f"**{title}** — {GLOSSARY[k]}")
