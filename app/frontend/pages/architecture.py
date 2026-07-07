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
  synth [label="Cross-source synthesis\\n13 composites, incl. turnover-authenticity" {_ACCENT}];
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
    "Problem Statement 3 · Financial Health Score": {
        "dot": _T03_DOT,
        "tagline": "Turns everyday business data — GST, banking, utilities and more — into a clear "
                   "financial-health score and grade for an MSME.",
        "challenge": "Financial Health Score · Problem Statement 3",
        "flow": ("25 alternate-data sources → integration (canonical entity resolution) → feature "
                 "engineering → cross-source synthesis (13 composites) → segmentation, scoring and "
                 "confidence in parallel → explainability → the Financial Health Card."),
        "kind": "t03",
    },
    "Problem Statement 4 · Early Warning": {
        "dot": _T04_DOT,
        "flow": ("A 24-month alt-data panel → leakage-guarded features → the EWS engine, compared against "
                 "a repayment-only baseline on equal footing so the lead-time gain is a fair number → the "
                 "portfolio radar and watchlist with per-borrower drivers."),
        "kind": "t04",
        "tagline": "Spots borrowers drifting toward default months before missed payments show it, "
                   "so the bank can step in early.",
        "challenge": "Default Prediction Model · Problem Statement 4",
        "stack": [
            "**Alt-data panel:** 24 monthly snapshots per borrower off the shared latent generators",
            "**No data leakage:** entity-level split; future-window features raise; labels attached separately",
            "**EWS engine:** monotonic LightGBM + isotonic calibration",
            "**Headline metric:** lead-time over a repayment-only baseline, not accuracy. Median 8-month gap.",
            "**Surfaces:** Portfolio Overview radar + Watchlist with explained drivers",
        ],
    },
    "Problem Statement 5 · Fraud Intelligence": {
        "dot": _T05_DOT,
        "flow": ("Transactions → typology + anomaly scoring → ring expansion across the transfer graph → "
                 "a citation-gated, 5-stage case file where every claim carries its transactions → the "
                 "fraud desk with human-in-the-loop review."),
        "kind": "t05",
        "tagline": "Finds suspicious patterns across transactions and accounts, and links the accounts "
                   "involved into one reviewable case.",
        "challenge": "Open Innovation · Problem Statement 5",
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
                "One platform for all three problem statements, built so every decision it makes can be traced and explained")

    st.markdown(
        "We entered **all three problem statements** on a single platform. Each has its own "
        "solution and its own diagram — **pick one below** to see how it works.")

    st.markdown("<p class='cp-arch-pick'>Choose a problem statement</p>", unsafe_allow_html=True)
    with st.container(key="cp_arch_tracks"):
        choice = st.radio("Problem statement", list(_TRACKS.keys()),
                          horizontal=True, label_visibility="collapsed")

    if not state.is_technical():
        st.caption("Under each diagram is the flow in plain language. For full engineering detail, "
                   "flip the **Technical** toggle at the top right.")
    track = _TRACKS[choice]
    st.markdown(track["tagline"])
    st.caption(f"Challenge · {track['challenge']}")

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
            st.caption("Every source here passed the Appendix-A rubric (8 core + 17 enrichment); weaker "
                       "candidates were documented separately and deliberately left out of the model.")
        with c2:
            st.subheader("Model and synthesis stack")
            st.markdown(
                "- **WOE/IV logistic scorecard:** interpretable, **probability-calibrated** PD backbone\n"
                "- **Monotonic LightGBM:** **probability-calibrated** PD lift under hard monotonic constraints, so its logic holds up to a credit review\n"
                "- **Isolation Forest:** unsupervised fraud/anomaly cross-check (label-free)\n"
                "- **Rule-based pillar → composite → grade:** a stronger input never lowers the grade\n"
                "- **K-Means:** descriptive peer segmentation (silhouette k)\n"
                "- **Confidence score:** IV × source-breadth\n"
                "- **SHAP + native reason codes:** dual explanation paths")
            st.subheader(f"Composite indicators ({len(COMPOSITE_CATALOG)})")
            st.caption(" · ".join(c["label"] for c in COMPOSITE_CATALOG))
    else:
        st.subheader("What's inside")
        st.markdown("\n".join(f"- {row}" for row in track["stack"]))
        st.caption("Built as a self-contained track under `app/tracks/` on the shared platform stack; "
                   "it imports no other track and can be removed without affecting the rest.")

    st.divider()
    st.info("All data here is synthetic. Backtesting on real defaults and connecting live GST / Account "
            "Aggregator / EPFO feeds are the next steps for a pilot, not something we're claiming to have done yet.")
