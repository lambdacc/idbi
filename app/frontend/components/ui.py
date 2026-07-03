"""Shared UI chrome + small HTML render helpers (banking-grade styling)."""
from __future__ import annotations

import html
from pathlib import Path
from typing import Optional

import streamlit as st

_CSS = Path(__file__).resolve().parents[1] / "static" / "custom.css"
_FAVICON = Path(__file__).resolve().parents[1] / "static" / "favicon.png"

# Semantic palette (mirrors custom.css :root). Pine doubles as accent + positive.
GREEN, AMBER, RED, NAVY, BLUE = "#1f5a45", "#8a5a12", "#a2331f", "#1f5a45", "#1f5a45"


def page_setup(title: str, icon: str = "") -> None:
    # A single pine monogram favicon replaces the old per-page emoji icons.
    page_icon = str(_FAVICON) if _FAVICON.exists() else None
    st.set_page_config(page_title=f"CreditPulse · {title}", page_icon=page_icon, layout="wide")
    if _CSS.exists():
        st.markdown(f"<style>{_CSS.read_text()}</style>", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown(
            "<div class='cp-brand'>CreditPulse</div>"
            "<div class='cp-brand-sub'>MSME Financial Health Card · IDBI Innovate 2026</div><br>",
            unsafe_allow_html=True)

    # Global Simple/Technical view toggle (design decision D3). Default
    # "simple"; initialise without clobbering an existing choice, then bind the
    # widget directly to the session key so the stored value is exactly
    # "simple"/"technical" and persists across page switches. The toggle lives
    # top-right on every page (page_setup runs at the top of Home + pages 1-5),
    # rendered above each page's title; the [5, 1.4] column pushes it right and
    # the .cp-viewtoggle-anchor marker lets CSS compact it into a pill.
    if "cp_view_mode" not in st.session_state:
        st.session_state["cp_view_mode"] = "simple"
    st.markdown("<div class='cp-viewtoggle-anchor'></div>", unsafe_allow_html=True)
    _spacer, ctrl = st.columns([5, 1.4])
    with ctrl:
        st.radio(
            "View",
            options=["simple", "technical"],
            format_func=lambda m: m.capitalize(),
            key="cp_view_mode",
            horizontal=True,
            label_visibility="collapsed",
            help="Technical view shows the model internals (SHAP, clustering, execution trace).",
        )


def band_class(band: str) -> str:
    return {"fast_track": "good", "review": "warn", "decline": "risk"}.get(band, "info")


def risk_class(category: str) -> str:
    return {"Low": "good", "Medium": "warn", "High": "risk", "Very High": "risk"}.get(category, "info")


def confidence_class(band: str) -> str:
    return {"High": "good", "Medium": "warn", "Low": "risk"}.get(band, "info")


def auth_class(score: float) -> str:
    return "good" if score >= 80 else ("warn" if score >= 55 else "risk")


def score_class(score: float) -> str:
    return "good" if score >= 74 else ("warn" if score >= 58 else "risk")


def kpi(label: str, value: str, sub: str = "", kind: str = "", tip: str = "") -> str:
    cls = f"cp-kpi {kind}".strip()
    lbl = html.escape(label)
    if tip:
        safe_tip = html.escape(tip)  # escapes quotes too (aria-label safe)
        lbl += (f"<span class='cp-info' tabindex='0' role='img' aria-label='{safe_tip}'>"
                f"ⓘ<span class='cp-tipbox'>{safe_tip}</span></span>")
    return (f"<div class='{cls}'><div class='lbl'>{lbl}</div>"
            f"<div class='val'>{value}</div><div class='sub'>{html.escape(sub)}</div></div>")


def badge(text: str, kind: str = "info") -> str:
    return f"<span class='cp-badge {kind}'>{html.escape(text)}</span>"


def card(title: Optional[str], body_html: str) -> str:
    head = f"<h4>{html.escape(title)}</h4>" if title else ""
    return f"<div class='cp-card'>{head}{body_html}</div>"


def fmt_inr(x: Optional[float]) -> str:
    x = float(x or 0.0)
    if x >= 1e7:
        return f"₹{x / 1e7:.2f} Cr"
    if x >= 1e5:
        return f"₹{x / 1e5:.1f} L"
    return f"₹{x:,.0f}"


def dimension_bars(pillars, show_eng: bool = False) -> str:
    """Render the five dimension scores as horizontal bullet bars (the Ledger
    replacement for the radar). Each `pillar` is either a pydantic Pillar or a
    dict carrying `label`, `score`, and optionally `engineering_name`."""
    rows = []
    for p in pillars:
        label = getattr(p, "label", None) or p["label"]
        score = getattr(p, "score", None)
        if score is None:
            score = p["score"]
        eng_name = getattr(p, "engineering_name", None)
        if eng_name is None and isinstance(p, dict):
            eng_name = p.get("engineering_name")
        cls = score_class(float(score))
        pct = max(0.0, min(100.0, float(score)))
        eng = (f" <span class='eng'>({html.escape(str(eng_name))})</span>"
               if show_eng and eng_name else "")
        rows.append(
            f"<div class='cp-dimbar {cls}'>"
            f"<div class='row'><span class='k'>{html.escape(str(label))}{eng}</span>"
            f"<span class='v'>{float(score):.0f}<small>/100</small></span></div>"
            f"<div class='track'><div class='fill' style='width:{pct:.0f}%'></div></div>"
            f"</div>")
    return "".join(rows)
