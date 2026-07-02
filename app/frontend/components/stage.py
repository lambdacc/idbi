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


def console_html(lines: List[str]) -> str:
    body = "".join(
        f"<span class='ln {_line_class(ln)}'>{html.escape(ln)}</span>" for ln in lines)
    # role="log" + aria-live so screen readers announce pipeline progress.
    return f"<div class='cp-console' role='log' aria-live='polite'>{body}</div>"


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
                f"<div class='rc'>{'✓ ' if src['connected'] else ''}{rc}</div></div>",
                unsafe_allow_html=True)


def render_composites(composites: List[dict]) -> None:
    for c in composites:
        flag = "flagship" if c.get("flagship") else ""
        srcs = " · ".join(c["sources"])
        star = "★ " if c.get("flagship") else ""
        st.markdown(
            f"<div class='cp-comp {flag}'><div class='hd'>"
            f"<span class='nm'>{star}{html.escape(c['label'])}</span>"
            f"<span class='vl'>{html.escape(c['display'])}</span></div>"
            f"<div class='rt'>{html.escape(c['rationale'])}</div>"
            f"<div class='sr'>sources: {html.escape(srcs)}</div></div>",
            unsafe_allow_html=True)


def render_reasons(positives: List[dict], negatives: List[dict]) -> None:
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("**Key Strengths**")
        if not positives:
            st.caption("No material strengths above threshold.")
        for r in positives:
            st.markdown(
                f"<div class='cp-reason pos'><span class='mk'>+</span>"
                f"<span class='tx'>{html.escape(r['text'])}</span></div>", unsafe_allow_html=True)
    with col_b:
        st.markdown("**Key Risks**")
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
