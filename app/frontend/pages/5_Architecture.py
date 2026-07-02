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
from app.frontend.components.ui import page_setup

page_setup("Architecture", icon="🏗️")

st.title("Solution Architecture")
st.caption("Single Cloud-Run container · Python-first · deterministic-first, explainable-by-construction")

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

st.divider()
c1, c2 = st.columns([1.1, 1])
with c1:
    st.subheader(f"Data sources ({len(SOURCE_CATALOG)})")
    groups = defaultdict(list)
    for _stem, label, group in SOURCE_CATALOG:
        groups[group].append(label)
    for group, labels in groups.items():
        st.markdown(f"**{group}** — " + ", ".join(labels))
    st.caption("Every source is Retain-tier from the Appendix-A rubric sweep (8 core + 17 enrichment); "
               "Reject-tier candidates are documented, not silently modelled.")
with c2:
    st.subheader("Model & synthesis stack")
    st.markdown(
        "- **WOE/IV logistic scorecard** — interpretable PD backbone\n"
        "- **Monotonic LightGBM** — bank-defensible PD lift (hard constraints)\n"
        "- **Deterministic pillar→composite→grade** — provably monotonic\n"
        "- **K-Means** — descriptive peer segmentation (silhouette k)\n"
        "- **Confidence score** — IV × source-breadth\n"
        "- **SHAP + native reason codes** — dual explanation paths")
    st.subheader(f"Composite indicators ({len(COMPOSITE_CATALOG)})")
    st.caption(" · ".join(c["label"] for c in COMPOSITE_CATALOG))

st.divider()
b1, b2 = st.columns(2)
with b1:
    st.markdown(
        "<div class='cp-card'><h4>Module boundaries</h4>"
        "<b>frontend/</b> renders state only · <b>backend/</b> orchestrates + applies "
        "brief-facing labels · <b>ml/</b> is framework-free (pure pandas/sklearn/LightGBM), "
        "independently testable and reusable behind a future FastAPI adapter.</div>",
        unsafe_allow_html=True)
with b2:
    st.markdown(
        "<div class='cp-card'><h4>Deployment</h4>"
        "Single Docker image on Google Cloud Run · Streamlit binds <code>$PORT</code> · "
        "synthetic cohort generated at build time · scale-to-zero between demos, "
        "min-instances=1 for the judging window. No PII, no external secrets.</div>",
        unsafe_allow_html=True)

st.info("All data is synthetic. Real-default backtesting and live GST/AA/EPFO integration are "
        "explicit post-hackathon productionization steps — stated honestly, not claimed here.")
