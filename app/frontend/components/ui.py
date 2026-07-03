"""Shared UI chrome + small HTML render helpers (banking-grade styling)."""
from __future__ import annotations

import html
from pathlib import Path
from typing import Optional

import streamlit as st

_CSS = Path(__file__).resolve().parents[1] / "static" / "custom.css"

# Semantic palette (mirrors custom.css :root)
GREEN, AMBER, RED, NAVY, BLUE = "#147347", "#8f5c13", "#c0392b", "#0b3d75", "#1466b8"


def page_setup(title: str, icon: str = "📊") -> None:
    st.set_page_config(page_title=f"CreditPulse · {title}", page_icon=icon, layout="wide")
    if _CSS.exists():
        st.markdown(f"<style>{_CSS.read_text()}</style>", unsafe_allow_html=True)
    with st.sidebar:
        st.markdown(
            "<div class='cp-brand'>CreditPulse</div>"
            "<div class='cp-brand-sub'>MSME Financial Health Card · IDBI Innovate 2026</div><br>",
            unsafe_allow_html=True)
        # Global Simple/Technical view toggle (design decision D3). Default
        # "simple"; initialise without clobbering an existing choice, then bind
        # the widget directly to the session key so the stored value is exactly
        # "simple"/"technical" and persists across page switches.
        if "cp_view_mode" not in st.session_state:
            st.session_state["cp_view_mode"] = "simple"
        st.radio(
            "View",
            options=["simple", "technical"],
            format_func=lambda m: m.capitalize(),
            key="cp_view_mode",
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
