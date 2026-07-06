"""Architecture — concise solution overview for judges (implementation-plan §3, §5, §8).

Reference page (core, not track-owned): a platform-level diagram of the three
tracks over the shared foundation, followed by the Track-03 assessment pipeline
in detail. This page is technical by design (jargon-exempt in the Simple-mode
sweep) but hides the deep engineering narrative behind the Technical toggle.
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


def render() -> None:
    page_header("Solution architecture",
                "Single Cloud-Run container · Python-first · deterministic-first, explainable by construction")

    st.caption("One platform, three problem statements: Track 03 (financial health), Track 04 (early "
               "warning) and Track 05 (fraud intelligence) all run on the shared stack below.")

    if not state.is_technical():
        st.info("This page shows the system's internal architecture; use the **Technical** toggle at "
                "the top right for full engineering detail.")

    # --- Platform view: three tracks over one shared foundation --------------
    _PLATFORM_DOT = """
    digraph Platform {
      rankdir=TB; bgcolor="transparent"; splines=ortho;
      node [shape=box style="rounded,filled" fontname="Schibsted Grotesk" fontsize=11
            color="#dbe2ec" fillcolor="#f4f6fa" fontcolor="#1b2733" margin="0.18,0.10"];
      edge [color="#8ca3bd" arrowsize=0.7];

      subgraph cluster_foundation {
        label="Shared foundation (one codebase, one deploy)";
        fontname="Schibsted Grotesk"; fontsize=11; color="#c3d0e0"; style="rounded";
        data  [label="Synthetic data-gen\\nlatent-consistent generators + ground-truth labels" fillcolor="#eef2f8"];
        mlc   [label="ML core\\nfeatures · scorecard + monotonic LightGBM · explainability · eval" fillcolor="#eef2f8"];
        back  [label="Backend\\npipeline orchestration + typed contracts" fillcolor="#eef2f8"];
        shell [label="Frontend router (main.py)\\nst.navigation · Overview · registry auto-detects installed tracks"
               fillcolor="#e9f0fb" color="#1466b8"];
        data -> mlc -> back -> shell;
      }

      t03 [label="Track 03 · Financial Health (PS3)\\nshared scorecard → Financial Health Card\\nunderwrite the new-to-bank MSME"
           fillcolor="#0b3d75" fontcolor="#ffffff" color="#0b3d75"];
      t04 [label="Track 04 · Early Warning (PS4)\\nEWSEngine → portfolio radar + watchlist\\nmonitor the book for deterioration"
           fillcolor="#0b3d75" fontcolor="#ffffff" color="#0b3d75"];
      t05 [label="Track 05 · Fraud Intelligence (PS5)\\nFraudEngine + citation-gated case file\\nprotect the payment rails"
           fillcolor="#0b3d75" fontcolor="#ffffff" color="#0b3d75"];

      shell -> t03; shell -> t04; shell -> t05;
    }
    """
    st.graphviz_chart(_PLATFORM_DOT, use_container_width=True)
    st.caption("Every track builds on the same synthetic data-gen, ML core, backend contract and "
               "Streamlit shell. Tracks never import each other; the registry auto-detects installed "
               "tracks by folder, so removing a track folder cleanly drops its group (Track 03 is the "
               "shared core itself). Track 03's assessment pipeline is detailed below.")

    st.divider()
    st.subheader("Track 03 — assessment pipeline (detail)")

    _DOT = """
    digraph CreditPulse {
      rankdir=TB; bgcolor="transparent"; splines=ortho;
      node [shape=box style="rounded,filled" fontname="Schibsted Grotesk" fontsize=11
            color="#dbe2ec" fillcolor="#f4f6fa" fontcolor="#1b2733" margin="0.18,0.10"];
      edge [color="#8ca3bd" arrowsize=0.7];

      src [label="Alternate data sources (25)\\nGST · Bank/AA · UPI · EPFO · Bureau · Udyam\\nE-way · Electricity · MCA · GeM · Courts · …"
           fillcolor="#eef2f8"];
      integ [label="Data integration\\ncanonical entity resolution (GSTIN↔PAN↔Udyam↔MCA)"];
      feat  [label="Feature engineering\\n5 pillars · per-source modules"];
      synth [label="Cross-source synthesis\\n12 composites + turnover-authenticity (flagship)"
             fillcolor="#e9f0fb" color="#1466b8"];
      clust [label="K-Means segmentation\\n(descriptive peer group only)"];
      score [label="Scoring models\\nWOE/IV scorecard + monotonic LightGBM\\n+ deterministic pillar→composite→grade"];
      conf  [label="Confidence score\\ndata-completeness (IV × breadth)"];
      expl  [label="Explainability\\nnative reason codes + SHAP"];
      card  [label="Financial health card\\n5 dimensions · grade · recommendation"
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

    st.divider()
    st.info("All data is synthetic. Real-default backtesting and live GST/AA/EPFO integration are "
            "explicit post-hackathon productionization steps, stated honestly, not claimed here.")
