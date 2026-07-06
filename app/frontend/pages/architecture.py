"""Architecture — concise solution overview for judges (implementation-plan §3, §5, §8).

Reference page (core, not track-owned). One platform, three problem statements:
a radio selects Track 03 / 04 / 05 and renders that track's OWN architecture
diagram over the shared foundation (multi-track issue #0). This page is technical
by design (jargon-exempt in the Simple-mode sweep) but hides the deep engineering
narrative behind the Technical toggle.
"""
from __future__ import annotations

import sys
from pathlib import Path

_p = Path(__file__).resolve()
_ROOT = next((par for par in _p.parents if (par / "requirements.txt").exists()), _p.parents[3])
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from collections import defaultdict

import streamlit as st

from app.backend.services.pipeline_orchestrator import COMPOSITE_CATALOG, SOURCE_CATALOG
from app.frontend.components import state
from app.frontend.components.ui import page_header

# Shared graphviz preamble — same node/edge styling across all three diagrams.
_HEAD = ('  rankdir=TB; bgcolor="transparent"; splines=ortho; nodesep=0.24; ranksep=0.3;\n'
         '  node [shape=box style="rounded,filled" fontname="Schibsted Grotesk" fontsize=11\n'
         '        color="#dbe2ec" fillcolor="#f4f6fa" fontcolor="#1b2733" margin="0.18,0.10"];\n'
         '  edge [color="#8ca3bd" arrowsize=0.7];')
_NAVY = 'fillcolor="#0b3d75" fontcolor="#ffffff" color="#0b3d75"'
_ACCENT = 'fillcolor="#e9f0fb" color="#1466b8"'

# --- Track 03 · Financial Health (the shared core itself) --------------------
_T03_DOT = f"""
digraph T03 {{
{_HEAD}
  src   [label="Alternate data sources (25)\\nGST · Bank/AA · UPI · EPFO · Bureau · Udyam\\nE-way · Electricity · MCA · GeM · Courts · …" fillcolor="#eef2f8"];
  integ [label="Data integration\\ncanonical entity resolution (GSTIN↔PAN↔Udyam↔MCA)"];
  feat  [label="Feature engineering\\n5 pillars · per-source modules"];
  synth [label="Cross-source synthesis\\n13 composites + turnover-authenticity (flagship)" {_ACCENT}];
  clust [label="Peer segmentation\\n(descriptive group only)"];
  score [label="Scoring\\nWOE/IV scorecard + monotonic LightGBM\\n+ deterministic pillar→composite→grade"];
  conf  [label="Confidence score\\ndata-completeness (IV × breadth)"];
  expl  [label="Explainability\\nnative reason codes + SHAP"];
  card  [label="Financial Health Card\\n5 dimensions · grade · recommendation" {_NAVY}];
  src -> integ -> feat -> synth;
  synth -> clust; synth -> score; synth -> conf;
  clust -> expl; score -> expl; conf -> expl;
  expl -> card;
}}
"""

# --- Track 04 · Early Warning ------------------------------------------------
_T04_DOT = f"""
digraph T04 {{
{_HEAD}
  panel [label="Alt-data panel (24 months)\\nGST · UPI · EPFO · e-way · electricity\\n+ repayment history" fillcolor="#eef2f8"];
  feat  [label="Leakage-guarded features\\nentity-level split · future-window blocked\\nlabels attached in a separate step"];
  ews   [label="EWS engine\\nmonotonic LightGBM + isotonic calibration" {_NAVY}];
  base  [label="Repayment-only baseline\\n(SAJAG-style stand-in)"];
  eval  [label="Lead-time evaluation\\nmedian 8-month gap (11.5 vs 2.0 mo)\\ncapture@decile 0.926 vs 0.519" {_ACCENT}];
  out   [label="Portfolio radar + watchlist\\nexplained drivers per borrower" {_NAVY}];
  panel -> feat -> ews;
  ews -> eval; base -> eval;
  ews -> out;
}}
"""

# --- Track 05 · Fraud Intelligence -------------------------------------------
_T05_DOT = f"""
digraph T05 {{
{_HEAD}
  txn   [label="Transactions + accounts\\n(data the bank already holds)" fillcolor="#eef2f8"];
  score [label="Scoring\\ntypology detectors + Isolation-Forest anomaly"];
  ring  [label="Ring expansion\\nbounded BFS over the transfer graph\\n(no graph DB, no new dependency)"];
  gate  [label="Citation gate\\nevery claim carries transaction IDs — or raises" {_ACCENT}];
  case  [label="Agentic case file (5 stages)\\ngrounds · ring diagram · recommendation" {_NAVY}];
  eval  [label="Evaluation (ground-truth = eval-only)\\n6/6 rings recovered · 0/10 hard-negative FP" {_ACCENT}];
  desk  [label="Fraud desk\\nscored accounts · human-in-the-loop review" {_NAVY}];
  txn -> score -> ring -> gate -> case;
  score -> eval; ring -> eval; score -> desk;
}}
"""

_TRACKS = {
    "Track 03 · Financial Health (PS3)": {
        "dot": _T03_DOT,
        "flow": ("25 alternate-data sources → integration (canonical entity resolution) → feature "
                 "engineering → cross-source synthesis (13 composites) → segmentation, scoring and "
                 "confidence in parallel → explainability → the Financial Health Card."),
        "kind": "t03",
    },
    "Track 04 · Early Warning (PS4)": {
        "dot": _T04_DOT,
        "flow": ("A 24-month alt-data panel → leakage-guarded features → the EWS engine, scored against "
                 "a repayment-only baseline so the lead-time gap is apples-to-apples → the portfolio "
                 "radar and watchlist with per-borrower drivers."),
        "kind": "t04",
        "stack": [
            "**Alt-data panel:** 24 monthly snapshots per borrower off the shared latent generators",
            "**Anti-leakage by construction:** entity-level split; future-window features raise; labels attached separately",
            "**EWS engine:** monotonic LightGBM + isotonic calibration",
            "**Headline metric:** lead-time vs a repayment-only baseline (not accuracy) — median 8-month gap",
            "**Surfaces:** Portfolio Overview radar + Watchlist with explained drivers",
        ],
    },
    "Track 05 · Fraud Intelligence (PS5)": {
        "dot": _T05_DOT,
        "flow": ("Transactions → typology + anomaly scoring → ring expansion across the transfer graph → "
                 "a citation-gated, 5-stage case file where every claim carries its transactions → the "
                 "fraud desk with human-in-the-loop review."),
        "kind": "t05",
        "stack": [
            "**Scoring:** typology detectors blended with an Isolation-Forest anomaly signal",
            "**Ring expansion:** bounded pure-Python BFS over the transfer graph — no graph DB, no new dependency",
            "**Citation gate:** a finding cannot be constructed without its transaction IDs (it raises)",
            "**Ground truth is eval-only:** the fraud label file is never read at score time",
            "**Results:** 6/6 rings recovered; 0/10 hard-negative false positives",
        ],
    },
}


def render() -> None:
    page_header("Solution architecture",
                "Single Cloud-Run container · Python-first · deterministic-first, explainable by construction")

    st.caption("One platform, three problem statements over a shared foundation (synthetic data-gen · "
               "ML core · backend contract · Streamlit shell). Pick a track to see its architecture.")

    if not state.is_technical():
        st.info("This page shows the system's internal architecture; use the **Technical** toggle at "
                "the top right for full engineering detail.")

    choice = st.radio("Track", list(_TRACKS.keys()), horizontal=True, label_visibility="collapsed")
    track = _TRACKS[choice]

    st.graphviz_chart(track["dot"], use_container_width=True)
    st.caption(f"Flow: {track['flow']}")

    st.divider()
    if track["kind"] == "t03":
        c1, c2 = st.columns([1.1, 1])
        with c1:
            st.subheader(f"Data sources ({len(SOURCE_CATALOG)})")
            groups = defaultdict(list)
            for _stem, label, group in SOURCE_CATALOG:
                groups[group].append(label)
            for group, labels in groups.items():
                st.markdown(f"**{group}:** " + ", ".join(labels))
            st.caption("Every source is Retain-tier from the Appendix-A rubric sweep (8 core + 17 enrichment); "
                       "Reject-tier candidates are documented, not silently modelled.")
        with c2:
            st.subheader("Model and synthesis stack")
            st.markdown(
                "- **WOE/IV logistic scorecard:** interpretable, **probability-calibrated** PD backbone\n"
                "- **Monotonic LightGBM:** bank-defensible, **probability-calibrated** PD lift (hard constraints)\n"
                "- **Isolation Forest:** unsupervised fraud/anomaly cross-check (label-free)\n"
                "- **Deterministic pillar to composite to grade:** provably monotonic\n"
                "- **K-Means:** descriptive peer segmentation (silhouette k)\n"
                "- **Confidence score:** IV × source-breadth\n"
                "- **SHAP + native reason codes:** dual explanation paths")
            st.subheader(f"Composite indicators ({len(COMPOSITE_CATALOG)})")
            st.caption(" · ".join(c["label"] for c in COMPOSITE_CATALOG))
    else:
        st.subheader("Under the hood")
        st.markdown("\n".join(f"- {row}" for row in track["stack"]))
        st.caption("Built as a self-contained track under `app/tracks/` on the shared platform stack; "
                   "it imports no other track and can be removed without affecting the rest.")

    st.divider()
    st.info("All data is synthetic. Real-default backtesting and live GST/AA/EPFO integration are "
            "explicit post-hackathon productionization steps, stated honestly, not claimed here.")
