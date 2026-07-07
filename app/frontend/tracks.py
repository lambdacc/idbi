"""Track registry — the single declarative source of truth for the platform's
grouped navigation (multi-track README §1a / D1 / D10 / D11).

Consumed by:
  * `main.py`     — builds `st.navigation({group_label: [st.Page, ...]})`;
  * `pages/overview.py` — renders one card per INSTALLED track;
  * in-app links  — every `st.page_link`/`st.switch_page` targets the
                    `StreamlitPage` OBJECT from `get_page(key)` (path strings do
                    not resolve against callable-registered pages — wp-s Q4).

Isolation (D10): a track's pages live under `app/tracks/<folder>/pages/`. The
registry auto-detects installed tracks by folder existence, and imports a track's
page modules ONLY when its folder is present — so `rm -rf app/tracks/<folder>`
silently drops the group, its Overview card and its deep links with no code edits.
Platform + Reference groups have no folder and are always present.

Pages are registered as CALLABLES (each page module exposes `render()`), never as
bare file paths: under st.navigation (MPA v2) AppTest renders file-path pages
BLANK with no exception, so callables are the only way the smoke sweep tests
anything (wp-s Q5). Every page carries an explicit, unique, flat `url_path`
(D11); the four submission deep links are `track03/04/05` + the Overview root.
"""
from __future__ import annotations

import html
import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

import streamlit as st

_ROOT = Path(__file__).resolve().parents[2]          # repo root (…/idbi)
_TRACKS_DIR = _ROOT / "app" / "tracks"


@dataclass(frozen=True)
class PageSpec:
    """One navigable page. `module`/`attr` name the render callable to import
    lazily; `key` is the stable registry handle used by in-app links."""
    key: str
    title: str
    module: str
    url_path: str
    attr: str = "render"
    default: bool = False


@dataclass(frozen=True)
class TrackSpec:
    """A navigation group. `folder` (under app/tracks/) drives auto-detection;
    `folder=None` marks always-present platform/reference groups."""
    id: str
    label: str
    pages: List[PageSpec]
    badge: Optional[str] = None
    folder: Optional[str] = None
    blurb: str = ""
    capabilities: List[str] = field(default_factory=list)

    @property
    def installed(self) -> bool:
        return self.folder is None or (_TRACKS_DIR / self.folder).exists()

    @property
    def start_key(self) -> str:
        """Registry key of the group's entry page (the D11 deep-link target)."""
        return self.pages[0].key


# --- The registry ----------------------------------------------------------
# Section order == dict insertion order in main.py: Platform, T03, T04, T05,
# Reference (wp-s Q1). Every url_path is flat and unique (wp-s Q7).
TRACKS: List[TrackSpec] = [
    TrackSpec(
        id="platform", label="Platform",
        pages=[
            PageSpec("platform.overview", "Overview",
                     "app.frontend.pages.overview", url_path="", default=True),
        ],
    ),
    TrackSpec(
        id="t03", label="Problem Statement 3 · Financial Health Score", badge="Problem Statement 3",
        folder="t03_financial_health",
        blurb="Many new-to-credit and new-to-bank MSMEs lack the financial documents banks underwrite "
              "on. CreditPulse aggregates their alternate data — GST, UPI, Account Aggregator, EPFO and "
              "more — into a Financial Health Card: a multidimensional score of each business's strengths "
              "and risks, so viable but credit-invisible borrowers stop being turned away by default.",
        capabilities=["Explainable financial health card",
                      "Turnover-authenticity cross-check",
                      "Deterministic scorecard + calibrated PD"],
        pages=[
            # Consolidated 5→3 (multi-track issue #5): Run+Pipeline merged into
            # one Assessment page; Dashboard folded into the Financial Health Card.
            PageSpec("t03.run", "Assessment",
                     "app.tracks.t03_financial_health.pages.assessment",
                     url_path="track03"),
            PageSpec("t03.health_card", "Financial Health Card",
                     "app.tracks.t03_financial_health.pages.health_card",
                     url_path="health_card"),
            PageSpec("t03.explainability", "Explainability",
                     "app.tracks.t03_financial_health.pages.explainability",
                     url_path="explainability"),
        ],
    ),
    TrackSpec(
        id="t04", label="Problem Statement 4 · Early Warning", badge="Problem Statement 4",
        folder="t04_early_warning",
        blurb="Default prediction today is held back by structured-data-only models and fragmented methods "
              "across loan types. This monitors the whole book with structured and alternate signals "
              "together, flagging borrowers likely to slip months before repayment does — every warning "
              "explained the same way, so the risk read stays consistent and actionable. "
              "(Official brief: Default Prediction Model.)",
        capabilities=["Portfolio deterioration radar",
                      "Lead-time vs a repayment-only baseline",
                      "Watchlist with explained drivers"],
        pages=[
            PageSpec("t04.portfolio", "Portfolio Overview",
                     "app.tracks.t04_early_warning.pages.portfolio_overview",
                     url_path="track04"),
            PageSpec("t04.watchlist", "Watchlist & Cases",
                     "app.tracks.t04_early_warning.pages.watchlist",
                     url_path="watchlist"),
        ],
    ),
    TrackSpec(
        id="t05", label="Problem Statement 5 · Fraud Intelligence", badge="Problem Statement 5",
        folder="t05_fraud_intelligence",
        blurb="Entered under Problem Statement 5 · Open Innovation — a shield for the payment rails. It "
              "detects mule accounts and the rings they route money through, then builds a case file where "
              "every claim is backed by its exact transactions, so a fraud analyst gets evidence-grounded "
              "cases to act on — not just an opaque score.",
        capabilities=["Typology + anomaly detection",
                      "Ring expansion over the transaction graph",
                      "Agentic, citation-gated case file"],
        pages=[
            PageSpec("t05.desk", "Fraud Desk",
                     "app.tracks.t05_fraud_intelligence.pages.fraud_desk",
                     url_path="track05"),
            PageSpec("t05.case", "Case Investigation",
                     "app.tracks.t05_fraud_intelligence.pages.case_investigation",
                     url_path="case_investigation"),
        ],
    ),
    TrackSpec(
        id="ref", label="Reference",
        pages=[
            PageSpec("ref.architecture", "Architecture",
                     "app.frontend.pages.architecture", url_path="architecture"),
        ],
    ),
]

# Populated by build_navigation() each rerun; read by get_page() for links.
_PAGE_OBJECTS: Dict[str, "st.navigation.StreamlitPage"] = {}


def installed_tracks() -> List[TrackSpec]:
    return [t for t in TRACKS if t.installed]


def _resolve_render(spec: PageSpec) -> Callable[[], None]:
    """Import the page module lazily and return its render callable, tagged with
    a unique __name__ so st.Page never collides on function identity."""
    module = importlib.import_module(spec.module)
    fn = getattr(module, spec.attr)
    fn.__name__ = spec.key.replace(".", "_")
    return fn


def build_navigation() -> Dict[str, list]:
    """Build `{group_label: [st.Page, ...]}` for INSTALLED tracks only, and
    (re)populate the page-object registry used by in-app links. Called by the
    router on every rerun, before `st.navigation(...).run()`."""
    _PAGE_OBJECTS.clear()
    nav: Dict[str, list] = {}
    for track in TRACKS:
        if not track.installed:
            continue
        pages = []
        for spec in track.pages:
            render = _resolve_render(spec)
            kwargs: dict = {"title": spec.title}
            if spec.default:
                kwargs["default"] = True
            else:
                kwargs["url_path"] = spec.url_path
            page = st.Page(render, **kwargs)
            _PAGE_OBJECTS[spec.key] = page
            pages.append(page)
        nav[track.label] = pages
    return nav


def get_page(key: str):
    """The `StreamlitPage` object for a registry key, for object-form links
    (`st.page_link(get_page("t03.explainability"))`). Requires build_navigation() to
    have run this rerun (the router guarantees this before any page renders)."""
    return _PAGE_OBJECTS[key]


def _key_of_page(page) -> Optional[str]:
    """Registry key of a StreamlitPage returned by `st.navigation` this rerun
    (identity lookup — build_navigation constructs fresh page objects on every
    rerun, so `is` is the reliable comparison)."""
    return next((k for k, p in _PAGE_OBJECTS.items() if p is page), None)


def track_of_page(page) -> Optional[TrackSpec]:
    """The TrackSpec owning a StreamlitPage returned by `st.navigation`."""
    key = _key_of_page(page)
    if key is None:
        return None
    return next((t for t in TRACKS if any(sp.key == key for sp in t.pages)), None)


def _short(label: str) -> str:
    """Product short name from a group label ('Problem Statement 3 · Financial
    Health Score' -> 'Financial Health Score')."""
    return label.split("·")[-1].strip()


def _ps_code(track: TrackSpec) -> str:
    """Compact PS prefix for a navbar tab ('Problem Statement 3' -> 'PS3').
    Reads the badge so it always tracks the real problem-statement number."""
    return f"PS{track.badge.split()[-1]}" if track.badge else ""


def _nav_link(key: str, label: str, active: bool) -> None:
    """One navbar/pill link. The active one carries a zero-height `.cp-here`
    marker so CSS can style its column's page_link via `:has(.cp-here)` —
    st.page_link exposes no active state of its own under the hidden router."""
    if active:
        st.markdown("<div class='cp-here'></div>", unsafe_allow_html=True)
    st.page_link(_PAGE_OBJECTS[key], label=label)


def render_topnav(current_page) -> None:
    """Registry-driven top product navbar for the hidden-position router
    (replaces the sidebar rail — team-lead + UX review, 06 Jul).

    Three layers, kept visually separate so each reads unambiguously:

      * a slim utility row above everything, right-aligned: the global
        Simple/Technical view toggle;
      * the navy bar = WHICH PRODUCT: brand wordmark (left); then the nav group
        — Overview + one PS-prefixed tab per installed track — floated to the
        centre; and Architecture pinned to the right edge;
      * below it, on product pages only: a masthead heading the product
        (product name + its PS badge) and one pill per page of the ACTIVE
        track.

    Columns are content-sized via CSS (flex max-content); two stretch spacers
    (brand→group and group→Architecture) centre the nav group between the brand
    on the left and Architecture on the right."""
    from app.frontend.components import ui

    active = track_of_page(current_page)
    current_key = _key_of_page(current_page)
    products = [t for t in installed_tracks() if t.badge]

    with st.container(key="cp_topnav"):
        cols = iter(st.columns(len(products) + 5, vertical_alignment="center"))
        with next(cols):
            # The wordmark doubles as a home link. A transparent st.page_link
            # overlays the two-tone markup (CSS) so clicking the logo navigates
            # to Overview client-side — a full-reload <a> would drop the demo's
            # session_state. The visible wordmark is aria-hidden; the link
            # carries the accessible name.
            with st.container(key="cp_brand"):
                st.markdown(
                    "<div class='cp-nav-brand' aria-hidden='true'><span class='a'>Credit</span>"
                    "<span class='b'>Pulse</span></div>", unsafe_allow_html=True)
                st.page_link(_PAGE_OBJECTS["platform.overview"], label="CreditPulse — home")
        with next(cols):
            st.markdown("<div class='cp-nav-spacer'></div>", unsafe_allow_html=True)
        with next(cols):
            _nav_link("platform.overview", "Overview",
                      active is not None and active.id == "platform")
        for track in products:
            with next(cols):
                _nav_link(track.start_key, f"{_ps_code(track)}: {_short(track.label)}",
                          track is active)
        with next(cols):
            st.markdown("<div class='cp-nav-spacer'></div>", unsafe_allow_html=True)
        with next(cols):
            _nav_link("ref.architecture", "Architecture",
                      active is not None and active.id == "ref")

    # The global level-of-detail slider sits in a slim row just below the navbar.
    with st.container(key="cp_utilbar"):
        ui.view_toggle()

    # Product masthead + page pills — product pages only; Overview is the brand
    # landing and Reference pages carry a masthead without a badge. The navbar
    # already carries the wordmark, so the masthead is the product name alone.
    if active is None or active.id == "platform":
        return
    badge = (f"<span class='cp-track-badge'>{html.escape(active.badge)}</span>"
             if active.badge else "")
    st.markdown(
        f"<div class='cp-masthead'>"
        f"<span class='prod'>{html.escape(_short(active.label))}</span>{badge}</div>",
        unsafe_allow_html=True)
    if len(active.pages) > 1:
        with st.container(key="cp_pills"):
            for col, sp in zip(st.columns(len(active.pages), vertical_alignment="center"),
                               active.pages):
                with col:
                    _nav_link(sp.key, sp.title, sp.key == current_key)
