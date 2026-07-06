"""Pipeline stage rendering (stage list, execution console, per-stage detail).

Consumes the `Stage.data` dicts produced by backend/services/pipeline_orchestrator
— never recomputes. Shared by the Pipeline page (staged reveal) and reused by the
Explainability / Health Card pages for the composite + reason-code widgets.
"""
from __future__ import annotations

import html
from typing import Dict, List

import streamlit as st

from app.backend.services.pipeline_orchestrator import COMPOSITE_CATALOG
from app.frontend.components import charts
from app.frontend.components.ui import badge, band_class, fmt_inr, kpi, risk_class
from app.ml.explainability.reason_codes import _LABELS

# feature/composite key -> pretty label for charts & waterfalls
_FEATURE_LABELS: Dict[str, str] = dict(_LABELS)
_FEATURE_LABELS.update({c["key"]: c["label"] for c in COMPOSITE_CATALOG})


def feature_label(fname: str) -> str:
    return _FEATURE_LABELS.get(fname, fname.replace("_", " "))


# ------------------------------------------------------------------ console
def _line_class(line: str) -> str:
    if "(−)" in line:
        return "bad"
    if any(m in line for m in ("✓", "★", "(+)")):
        return "ok"
    if "not on file" in line or line.strip().endswith("—"):
        return "dim"
    return ""


def console_html(lines: List[str], short: bool = False) -> str:
    body = "".join(
        f"<span class='ln {_line_class(ln)}'>{html.escape(ln)}</span>" for ln in lines)
    # `short` picks the compact 220px variant used when the console sits *below*
    # the live stage-output pane on the Pipeline page (WP-G).
    cls = "cp-console short" if short else "cp-console"
    # role="log" + aria-live so screen readers announce pipeline progress.
    return f"<div class='{cls}' role='log' aria-live='polite'>{body}</div>"


# ------------------------------------------------------------- stage list
def stage_list_html(stages, current_index: int) -> str:
    rows = []
    for s in stages:
        if s.index < current_index:
            state, status = "done", "Completed"
        elif s.index == current_index:
            state, status = "running", "Running"
        else:
            state, status = "waiting", "Waiting"
        rows.append(
            f"<div class='cp-stage {state}'><div class='idx'>{s.index}</div>"
            f"<div class='ttl'>{html.escape(s.title)}</div>"
            f"<div class='status'>{status}</div></div>")
    return "".join(rows)


def _dot(s) -> str:
    """Sanitise a Python string for a DOT double-quoted attribute."""
    return str(s).replace("\\", " ").replace('"', "'").replace("\n", " ").strip()


def stage_flow_dot(stages, revealed: int, current: int) -> str:
    """Graphviz DOT for the assessment pipeline as a top-down flow chart that
    *grows* one node per stage (multi-track issue #3). Only the first `revealed`
    stages are drawn, so re-rendering with an increasing `revealed` animates the
    chart building itself. `current` is the running stage (navy, highlighted);
    earlier stages are completed (green); pass current=0 once the run is done.
    Every node carries a `tooltip` (the stage's plain-language caption) so hover
    reveals what happens there — the mental-map goal."""
    shown = [s for s in stages if s.index <= revealed]
    lines = [
        "digraph pipeline {",
        '  rankdir=TB; bgcolor="transparent"; splines=true; nodesep=0.22; ranksep=0.28;',
        '  node [shape=box style="rounded,filled" fontname="Schibsted Grotesk" '
        'fontsize=10 margin="0.18,0.10" penwidth=1.2];',
        '  edge [color="#8ca3bd" arrowsize=0.6 penwidth=1.1];',
    ]
    for s in shown:
        done_boundary = current or (revealed + 1)
        if current and s.index == current:
            fill, fc, col = "#0b3d75", "#ffffff", "#0b3d75"          # running
        elif s.index < done_boundary:
            fill, fc, col = "#e7f3ec", "#14432a", "#8fc7a6"          # completed
        else:
            fill, fc, col = "#f4f6fa", "#1b2733", "#dbe2ec"          # just revealed
        tip = _dot(getattr(s, "caption", "") or getattr(s, "headline", "") or s.title)
        label = _dot(f"{s.index}. {s.title}")
        lines.append(f'  s{s.index} [label="{label}" tooltip="{tip}" '
                     f'fillcolor="{fill}" fontcolor="{fc}" color="{col}"];')
    for a_, b_ in zip(shown, shown[1:]):
        lines.append(f"  s{a_.index} -> s{b_.index};")
    lines.append("}")
    return "\n".join(lines)


# ------------------------------------------------------- per-stage detail
def render_source_grid(sources: List[dict], per_row: int = 6, limit: int | None = None) -> None:
    items = sources if limit is None else sources[:limit]
    for start in range(0, len(items), per_row):
        cols = st.columns(per_row)
        for col, src in zip(cols, items[start:start + per_row]):
            on = "on" if src["connected"] else ""
            rc = f"{src['records']} rec" if src["connected"] else "not on file"
            col.markdown(
                f"<div class='cp-src {on}'><div class='nm'>{html.escape(src['label'])}</div>"
                f"<div class='rc'>{rc}</div></div>",
                unsafe_allow_html=True)


def render_composites(composites: List[dict]) -> None:
    for c in composites:
        flag = "flagship" if c.get("flagship") else ""
        srcs = " · ".join(c["sources"])
        tag = ("<span class='cp-badge good' style='margin-right:.4rem'>flagship</span>"
               if c.get("flagship") else "")
        st.markdown(
            f"<div class='cp-comp {flag}'><div class='hd'>"
            f"<span class='nm'>{tag}{html.escape(c['label'])}</span>"
            f"<span class='vl'>{html.escape(c['display'])}</span></div>"
            f"<div class='rt'>{html.escape(c['rationale'])}</div>"
            f"<div class='sr'>sources: {html.escape(srcs)}</div></div>",
            unsafe_allow_html=True)


def render_reasons(positives: List[dict], negatives: List[dict]) -> None:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Key strengths**")
        if not positives:
            st.caption("No material strengths above threshold.")
        for r in positives:
            st.markdown(
                f"<div class='cp-reason pos'><span class='mk'>+</span>"
                f"<span class='tx'>{html.escape(r['text'])}</span></div>", unsafe_allow_html=True)
    with col_b:
        st.markdown("**Key risks**")
        if not negatives:
            st.caption("No material risks above threshold.")
        for r in negatives:
            st.markdown(
                f"<div class='cp-reason neg'><span class='mk'>−</span>"
                f"<span class='tx'>{html.escape(r['text'])}</span></div>", unsafe_allow_html=True)


def render_feature_counters(counters: List[dict], composite_count: int) -> None:
    cols = st.columns(len(counters) + 1)
    for col, c in zip(cols, counters):
        col.markdown(kpi_mini(c["label"], c["count"]), unsafe_allow_html=True)
    cols[-1].markdown(kpi_mini("Composites", composite_count), unsafe_allow_html=True)


def kpi_mini(label: str, value) -> str:
    return (f"<div class='cp-kpi'><div class='lbl'>{html.escape(str(label))}</div>"
            f"<div class='val'>{value}</div></div>")


# ------------------------------------------------- plain-language findings
def render_findings(findings: List[dict], technical: bool) -> None:
    """Render each finding as a tone-coded `.cp-finding` callout (plan §4 WP-C).

    In simple view, `technical=True` findings are skipped so non-technical users
    never see model-internal notes. Every interpolated string is html-escaped (G3).
    """
    for f in findings:
        if f.get("technical") and not technical:
            continue
        tone = f.get("tone", "neutral")
        if tone not in ("good", "warn", "risk", "neutral"):
            tone = "neutral"
        st.markdown(
            f"<div class='cp-finding {tone}'>{html.escape(str(f.get('text', '')))}</div>",
            unsafe_allow_html=True)


# ------------------------------------------------ per-stage ML technique
def render_technique(technique: dict | None, technical: bool) -> None:
    """Disclose WHICH ML technique runs at this stage and WHY it helps.

    `plain` (jargon-free name) + `benefit` sentence are ALWAYS shown, in both view
    modes. The `algorithm` string (the technical model name — contains banned terms
    like Isolation Forest / WOE / SHAP) is appended in TECHNICAL mode only (G4).
    Renders nothing when the stage carries no technique. Every interpolated string
    is html-escaped (G3)."""
    if not technique:
        return
    plain = html.escape(str(technique.get("plain", "")))
    benefit = html.escape(str(technique.get("benefit", "")))
    method = ""
    if technical and technique.get("algorithm"):
        method = (f"<div class='method'>Method: "
                  f"{html.escape(str(technique['algorithm']))}</div>")
    st.markdown(
        f"<div class='cp-technique'><span class='chip'>Technique</span>"
        f"<span class='nm'>{plain}</span>"
        f"<div class='bn'>{benefit}</div>{method}</div>",
        unsafe_allow_html=True)


# ------------------------------------------------------- per-stage detail
def render_detail(container, stage, entity_name: str, technical: bool,
                  upto: int | None = None, show_header: bool = True,
                  key_prefix: str = "") -> None:
    """Render a stage's visualization panel — shared by the live playback loop and
    the persistent notebook cells (plan §4 WP-C; relocated here from the page so
    both paths use one dispatch, no duplication).

    `upto` (ingestion only) shows just the first k source cards — the §6.2
    breadth-reveal lights them up one by one. `show_header` prints the
    `#### Stage N · Title` heading + caption (the live area wants it; the notebook
    cell already has that in its expander label, so it passes False). Model-internal
    bits (SHAP, the clustering algorithm name, Model PD) render only when
    `technical` (design decision D3 / guardrail G4).

    `key_prefix` disambiguates the plotly charts: the live playback area and a
    completed stage's notebook cell can both hold the same stage's chart at once,
    which would otherwise collide on Streamlit's auto-generated element id."""
    d = stage.data

    def _ck(name: str):
        return f"{key_prefix}{stage.key}_{name}" if key_prefix else None
    with container.container():
        if show_header:
            st.markdown(f"#### Stage {stage.index} · {stage.title}")
            st.caption(stage.caption)

        if stage.key == "scenario_lock_in":
            e = d["entity"]
            cols = st.columns(5)
            cols[0].markdown(kpi("Sector", e.get("sector", "-")), unsafe_allow_html=True)
            cols[1].markdown(kpi("Udyam category", e.get("category", "-")), unsafe_allow_html=True)
            cols[2].markdown(kpi("Vintage", f"{e.get('age_years', '-')} y"), unsafe_allow_html=True)
            cols[3].markdown(kpi("Employees", str(e.get("employees", "-"))), unsafe_allow_html=True)
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
            # Fraud/anomaly cross-check panel (unsupervised second opinion). The
            # headline is the blended fraud-risk score + band; the raw anomaly
            # score and label-free signal count are model-internal (technical-only).
            fraud = d.get("fraud") or {}
            band = fraud.get("fraud_band") or "Low"
            ftone = {"Elevated": "risk", "Moderate": "warn", "Low": "good"}.get(band, "neutral")
            frisk = fraud.get("fraud_risk_score")
            auth = fraud.get("authenticity_score")
            frisk_txt = f"{frisk:.0f}/100" if isinstance(frisk, (int, float)) else "-"
            auth_txt = f"{auth:.0f}/100" if isinstance(auth, (int, float)) else "-"
            st.markdown(
                f"<div class='cp-finding {ftone}'><b>Fraud risk: {html.escape(band)}</b> "
                f"&nbsp;·&nbsp; blended score {html.escape(frisk_txt)} "
                f"&nbsp;·&nbsp; turnover authenticity {html.escape(auth_txt)}</div>",
                unsafe_allow_html=True)
            if technical:
                anom = fraud.get("anomaly_score")
                sig = fraud.get("signals")
                anom_txt = f"{anom:.0f}/100" if isinstance(anom, (int, float)) else "-"
                fc = st.columns(2)
                fc[0].markdown(kpi("Profile anomaly", anom_txt,
                               "raw unsupervised score"), unsafe_allow_html=True)
                fc[1].markdown(kpi("Label-free signals", str(sig if sig is not None else "-"),
                               "consistency features cross-checked"), unsafe_allow_html=True)

        elif stage.key == "clustering":
            algo = (f"K-Means, k={d['k']} · descriptive only" if technical
                    else "Compared with similar businesses · descriptive only")
            st.markdown(badge(f"Peer group: {d['segment']}", "info") +
                        f" &nbsp; <span class='cp-scn'>{algo}</span>",
                        unsafe_allow_html=True)
            st.plotly_chart(charts.cluster_scatter(d["scatter"], d["entity_point"],
                            entity_name), use_container_width=True, key=_ck("scatter"))

        elif stage.key == "scoring":
            labels = [p["label"] for p in d["pillars"]]
            vals = [p["score"] for p in d["pillars"]]
            c1, c2 = st.columns([1.3, 1])
            with c1:
                st.plotly_chart(charts.pillar_bars(labels, vals),
                                use_container_width=True, key=_ck("pillars"))
            with c2:
                st.markdown(kpi("Composite score", f"{d['composite_score']:.0f}<small>/100</small>",
                            f"Grade {d['grade']}/10", band_class(d["onboarding_band"])),
                            unsafe_allow_html=True)
                if technical:
                    st.markdown(kpi("Model PD", f"{d['pd']:.1%}", d["risk_category"] + " risk",
                                risk_class(d["risk_category"])), unsafe_allow_html=True)
                else:
                    st.markdown(kpi("Estimated default risk", d["risk_category"],
                                "chance of repayment difficulty",
                                risk_class(d["risk_category"])), unsafe_allow_html=True)

        elif stage.key == "explainability":
            render_reasons(d["reasons_positive"], d["reasons_negative"])
            if technical and d["shap_top"]:
                st.markdown("**SHAP cross-check**, monotonic GBM PD path")
                st.plotly_chart(charts.shap_waterfall(d["shap_top"], feature_label),
                                use_container_width=True, key=_ck("shap"))

        elif stage.key == "health_card":
            hc = d["health_card"]
            st.markdown(
                f"<div class='cp-hero'><div class='score'>{hc['composite_score']:.0f}"
                f"<small>/100</small></div><div class='meta'>"
                f"<div class='name'>{html.escape(str(hc['name']))}</div>"
                f"<div class='subtle'>Grade {hc['grade']}/10 · {hc['recommendation']} · "
                f"confidence {hc['confidence']}</div></div></div>", unsafe_allow_html=True)
            from app.frontend import tracks
            st.page_link(tracks.get_page("t03.health_card"),
                         label="Open the full health card", use_container_width=True)


# ------------------------------------------------- persistent notebook cell
def render_stage_cell(stage, technical: bool, expanded: bool, detail_fn) -> None:
    """One persistent, notebook-style record for a completed stage (plan §4 WP-C /
    D2): an expander titled `Stage N · Title` whose summary line surfaces the
    stage headline, body = plain-language findings + the stage visualization via
    `detail_fn(container, stage)`. `detail_fn` is the page's `render_detail`
    binding (entity name + view mode pre-applied), so there is no duplicated
    dispatch."""
    label = f"Stage {stage.index} · {stage.title}"
    if stage.headline:
        label += f" — {stage.headline}"
    with st.expander(label, expanded=expanded):
        render_technique(stage.technique, technical)
        render_findings(stage.findings, technical)
        detail_fn(st.container(), stage)
