"""Architecture — concise solution overview for judges (implementation-plan §3, §5, §8)."""
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
from app.frontend.components.ui import page_setup

page_setup("Architecture", icon="🏗️")

st.title("Solution Architecture")
st.caption("Single Cloud-Run container · Python-first · deterministic-first, explainable-by-construction")

if not state.is_technical():
    st.info("This page shows the system's internal architecture — use the **Technical** toggle at "
            "the top right for full engineering detail.")

_DOT = """
digraph CreditPulse {
  rankdir=TB; bgcolor="transparent"; splines=ortho;
  node [shape=box style="rounded,filled" fontname="Inter" fontsize=11
        color="#dbe2ec" fillcolor="#f4f6fa" fontcolor="#1b2733" margin="0.18,0.10"];
  edge [color="#8ca3bd" arrowsize=0.7];

  src [label="Alternate data sources (25)\\nGST · Bank/AA · UPI · EPFO · Bureau · Udyam\\nE-way · Electricity · MCA · GeM · Courts · …"
       fillcolor="#eef2f8"];
  integ [label="Data Integration\\ncanonical entity resolution (GSTIN↔PAN↔Udyam↔MCA)"];
  feat  [label="Feature Engineering\\n5 pillars · per-source modules"];
  synth [label="Cross-Source Synthesis\\n12 composites + Turnover-Authenticity (flagship)"
         fillcolor="#e9f0fb" color="#1466b8"];
  clust [label="K-Means Segmentation\\n(descriptive peer group only)"];
  score [label="Scoring Models\\nWOE/IV scorecard + monotonic LightGBM\\n+ deterministic pillar→composite→grade"];
  conf  [label="Confidence Score\\ndata-completeness (IV × breadth)"];
  expl  [label="Explainability\\nnative reason codes + SHAP"];
  card  [label="Financial Health Card\\n5 dimensions · grade · recommendation"
         fillcolor="#0b3d75" fontcolor="#ffffff" color="#0b3d75"];

  src -> integ -> feat -> synth;
  synth -> clust; synth -> score; synth -> conf;
  clust -> expl; score -> expl; conf -> expl;
  expl -> card;
}
"""
st.graphviz_chart(_DOT, use_container_width=True)
st.caption("Flow: 25 alternate-data sources → data integration (canonical entity resolution) → "
           "feature engineering → cross-source synthesis (13 composites) → segmentation, scoring "
           "and confidence in parallel → explainability → the Financial Health Card.")

st.divider()
c1, c2 = st.columns([1.1, 1])
with c1:
    st.subheader(f"Data Sources ({len(SOURCE_CATALOG)})")
    groups = defaultdict(list)
    for _stem, label, group in SOURCE_CATALOG:
        groups[group].append(label)
    for group, labels in groups.items():
        st.markdown(f"**{group}** — " + ", ".join(labels))
    st.caption("Every source is Retain-tier from the Appendix-A rubric sweep (8 core + 17 enrichment); "
               "Reject-tier candidates are documented, not silently modelled.")
with c2:
    st.subheader("Model & Synthesis Stack")
    st.markdown(
        "- **WOE/IV logistic scorecard** — interpretable, **probability-calibrated** PD backbone\n"
        "- **Monotonic LightGBM** — bank-defensible, **probability-calibrated** PD lift (hard constraints)\n"
        "- **Isolation Forest** — unsupervised fraud/anomaly cross-check (label-free)\n"
        "- **Deterministic pillar→composite→grade** — provably monotonic\n"
        "- **K-Means** — descriptive peer segmentation (silhouette k)\n"
        "- **Confidence score** — IV × source-breadth\n"
        "- **SHAP + native reason codes** — dual explanation paths")
    st.subheader(f"Composite Indicators ({len(COMPOSITE_CATALOG)})")
    st.caption(" · ".join(c["label"] for c in COMPOSITE_CATALOG))

st.divider()
st.info("All data is synthetic. Real-default backtesting and live GST/AA/EPFO integration are "
        "explicit post-hackathon productionization steps — stated honestly, not claimed here.")
