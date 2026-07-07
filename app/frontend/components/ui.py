"""Shared UI chrome + small HTML render helpers (banking-grade styling)."""
from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

_CSS = Path(__file__).resolve().parents[1] / "static" / "custom.css"
_FAVICON = Path(__file__).resolve().parents[1] / "static" / "favicon.png"

# Semantic palette (mirrors custom.css :root).
GREEN, AMBER, RED, NAVY, BLUE = "#147347", "#8f5c13", "#c0392b", "#0b3d75", "#1466b8"


def _inject_css(css: str) -> None:
    """Install the stylesheet in the TOP document's <head> so it survives page
    navigations. A per-page `st.markdown('<style>')` is torn down and re-added on
    every rerun, flashing Streamlit's default theme (light sidebar, wrong width,
    toolbar) for a frame before the custom CSS re-applies -- that flash is the
    sideways "jump" on nav clicks. Injecting into the parent <head> once (keyed by
    id, updated in place) keeps the styling continuously applied across reruns."""
    payload = json.dumps(css)
    components.html(
        "<script>"
        "const d = window.parent.document;"
        "let s = d.getElementById('cp-head-css');"
        "if (!s) { s = d.createElement('style'); s.id = 'cp-head-css'; d.head.appendChild(s); }"
        f"s.textContent = {payload};"
        "</script>",
        height=0,
    )


def brandmark() -> str:
    """The CreditPulse wordmark: 'Credit' upright + 'Pulse' italic accent.
    Same serif family, inverts to light-on-dark inside the navy sidebar."""
    return "<span class='cp-logo'><span class='a'>Credit</span><span class='b'>Pulse</span></span>"


def shell_setup() -> None:
    """Router-level chrome (multi-track D2), run once per rerun by `main.py`
    BEFORE `st.navigation`: page config (its literal first Streamlit command)
    and the stylesheet (first-paint + persistent head copy). Navigation chrome
    — the top product navbar, masthead, page pills and the view toggle — is
    rendered by `tracks.render_topnav` after `st.navigation` resolves the
    current page. There is no sidebar."""
    # A single navy monogram favicon replaces the old per-page emoji icons.
    # set_page_config MUST be the first Streamlit command of the run (wp-s Q2).
    page_icon = str(_FAVICON) if _FAVICON.exists() else None
    st.set_page_config(page_title="CreditPulse", page_icon=page_icon, layout="wide")
    if _CSS.exists():
        css = _CSS.read_text()
        # First-paint styling (immediate) + persistent head copy (survives nav).
        # Under st.navigation the router runs every rerun, so this head-injection
        # applies before any page body renders — no FOUC on nav clicks.
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        _inject_css(css)


def view_toggle() -> None:
    """The global Simple/Technical view toggle (design decision D3), rendered
    by the router in a slim row directly BELOW the top navbar. Styled (CSS) as a
    two-position slider button with the inline label "Toggle level of detail".
    Default "simple"; initialise without clobbering an existing choice, then bind
    the widget directly to the session key so the stored value is exactly
    "simple"/"technical" and persists across page switches."""
    if "cp_view_mode" not in st.session_state:
        st.session_state["cp_view_mode"] = "simple"
    st.radio(
        "Toggle level of detail",
        options=["simple", "technical"],
        format_func=lambda m: m.capitalize(),
        key="cp_view_mode",
        horizontal=True,
        label_visibility="visible",
        help="Technical view shows the model internals (SHAP, clustering, execution trace).",
    )


def page_header(title: str, caption: Optional[str] = None) -> None:
    """Page-level heading (multi-track D2). Under the top-navbar shell the
    product masthead ('CreditPulse | <product>') is the page's dominant heading,
    so this renders as a quieter serif h2 (+ optional caption) rather than an
    h1 competing with it."""
    st.markdown(f"<h2 class='cp-pagetitle'>{html.escape(title)}</h2>",
                unsafe_allow_html=True)
    if caption:
        st.caption(caption)


def page_setup(title: str, icon: str = "") -> None:  # pragma: no cover
    """Deprecated shim kept only so any stray caller does not crash. The router
    (`shell_setup`) owns chrome now and pages call `page_header`. Do NOT use in
    new code; this renders only the page title (config/CSS/brand/toggle are the
    router's job and calling set_page_config here would raise under st.navigation)."""
    page_header(title)


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


def kpi(label: str, value: str, sub: str = "", kind: str = "", tip: str = "",
        text: bool = False) -> str:
    """One KPI tile. `text=True` marks a WORD value (sector, category, risk
    band): it renders in the sans face at a size that always fits the tile —
    the big numeral mono is reserved for numbers (Ledger rule) and long words
    set in it overflow narrow tiles."""
    cls = f"cp-kpi {kind}".strip()
    vcls = "val txt" if text else "val"
    lbl = html.escape(label)
    if tip:
        safe_tip = html.escape(tip)  # escapes quotes too (aria-label safe)
        lbl += (f"<span class='cp-info' tabindex='0' role='img' aria-label='{safe_tip}'>"
                f"ⓘ<span class='cp-tipbox'>{safe_tip}</span></span>")
    return (f"<div class='{cls}'><div class='lbl'>{lbl}</div>"
            f"<div class='{vcls}'>{value}</div><div class='sub'>{html.escape(sub)}</div></div>")


def badge(text: str, kind: str = "info") -> str:
    return f"<span class='cp-badge {kind}'>{html.escape(text)}</span>"


def card(title: Optional[str], body_html: str) -> str:
    head = f"<h4>{html.escape(title)}</h4>" if title else ""
    return f"<div class='cp-card'>{head}{body_html}</div>"


def fmt_pd(p: float) -> str:
    """Display floor/ceiling for default probabilities. A real credit model never
    prints a literal 0.0% or 100.0% -- both read as bugs to a credit audience --
    so the display (not the value) is clamped to an honest open interval."""
    p = float(p or 0.0)
    if p < 0.001:
        return "<0.1%"
    if p > 0.995:
        return ">99.5%"
    return f"{p:.1%}"


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
