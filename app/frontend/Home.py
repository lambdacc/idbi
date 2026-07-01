"""CreditPulse — Streamlit entry point (Sprint-1 placeholder).

Serves on $PORT for Cloud Run. The full staged-reveal demo (implementation-plan
§6) lands in Sprint 3; this page proves the container builds and serves, and
shows the Sprint-1 foundation is live (data cohort + eval harness).
"""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="CreditPulse", page_icon="📊", layout="wide")

st.title("CreditPulse — MSME Financial Health Card")
st.caption("IDBI Innovate 2026 · PS3 — Financial Health Score · deterministic-first, explainable-by-construction")

st.info("Sprint 1 foundation is live. Scoring UI and the staged-reveal pipeline arrive in Sprint 3.")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Demo archetypes")
    st.markdown(
        "- Textile Manufacturer\n- Retail Kirana Store\n- Restaurant\n"
        "- IT Services Company\n- Auto Components Supplier *(inflated-turnover showcase)*\n- Logistics Business")
with col2:
    st.subheader("Foundation status")
    data_dir = Path(__file__).resolve().parents[1] / "data"
    n_sources = len(list(data_dir.glob("*.csv"))) if data_dir.exists() else 0
    st.metric("Synthetic data sources", f"{n_sources} CSVs")
    st.markdown("5 scoring pillars · 12 composite indicators · Turnover-Authenticity flagship")

st.divider()
st.caption("Run `make data-gen` then `make eval` for the offline scorecard. `make demo` launches this app.")
