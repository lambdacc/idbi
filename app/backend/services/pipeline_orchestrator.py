"""Pipeline orchestrator — drives the staged-reveal state machine (implementation-plan §6).

The frontend (`frontend/pages/2_Pipeline.py`) NEVER computes anything: it renders
the `Stage` objects this module produces. The full assessment is computed ONCE
(one `ScoringEngine.score_entity` pass) and then DECOMPOSED into the nine reveal
stages of §6.2, each carrying (a) the execution-console log lines to print and
(b) the structured `data` that stage's visualization needs.

This is the Sprint-3 testable core: `run_assessment()` and the scenario helpers
are exercised end-to-end by `tests/test_pipeline_orchestrator.py` with no
Streamlit import (acceptance criterion b — "callable pipeline-orchestrator
functions, not the UI itself").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import pandas as pd

from ...ml.engine import ScoringEngine, get_engine
from ...ml.features.base import compute_entity_features
from ...ml.features.composite_features import composite_rationales
from ...ml.models.pillars import load_configs
from ..schemas.models import HealthCard, pillar_label_map
from .scoring_service import build_health_card

# --------------------------------------------------------------------------- #
# Display catalogs (presentation metadata; the numbers themselves come from ml/)
# --------------------------------------------------------------------------- #

# table stem -> (display label, group). Order defines the ingestion-reveal order:
# the eight Retain-CORE sources light up first (the credit-officer's staples),
# then the enrichment breadth — the deliberate "footprint" moment (§6.2 stage 2).
SOURCE_CATALOG: List[tuple] = [
    # Retain-core (8)
    ("gst", "GST Returns", "Tax / Statutory"),
    ("bank", "Bank / AA", "Banking & Payments"),
    ("upi", "UPI / QR", "Banking & Payments"),
    ("epfo", "EPFO", "Labour / Statutory"),
    ("bureau", "Credit Bureau", "Credit"),
    ("udyam", "Udyam Registry", "Identity / Statutory"),
    ("pan_gstin", "PAN ↔ GSTIN", "Identity / Statutory"),
    ("ewaybill", "E-Way Bills", "Trade & Logistics"),
    # Retain-enrichment (17)
    ("electricity", "Electricity (DISCOM)", "Utilities & Premises"),
    ("itr", "Income Tax (ITR)", "Tax / Statutory"),
    ("mca21", "MCA21", "Identity / Statutory"),
    ("fastag", "FASTag", "Trade & Logistics"),
    ("vahan", "Vahan (Fleet)", "Trade & Logistics"),
    ("factory_licence", "Factory Licence", "Utilities & Premises"),
    ("fssai", "FSSAI Licence", "Licensing"),
    ("pollution", "Pollution Consent", "Utilities & Premises"),
    ("shops_establishment", "Shops & Estab.", "Licensing"),
    ("property_tax", "Property Tax", "Utilities & Premises"),
    ("gem", "GeM Seller", "Commerce / B2G"),
    ("procurement", "e-Procurement", "Commerce / B2G"),
    ("dgft", "DGFT / IEC", "Trade & Logistics"),
    ("ecommerce", "E-commerce", "Commerce / B2G"),
    ("insurance", "Insurance", "Risk / Legal"),
    ("courts", "Court Records", "Risk / Legal"),
    ("insolvency", "IBC / DIN Screen", "Risk / Legal"),
]

# composite feature key -> (label, constituent source stems, static "fused signal"
# description). The dynamic manipulation-resistance string from composite_rationales()
# is preferred when present; this static line is the always-available fallback.
COMPOSITE_CATALOG: List[dict] = [
    dict(key="turnover_authenticity_score", label="Turnover Authenticity",
         sources=["gst", "bank", "ewaybill"], flagship=True, kind="score",
         desc="Declared GST turnover reconciled against settled bank inflows and e-way-bill goods movement."),
    dict(key="energy_intensity_flag", label="Energy Intensity", kind="flag_bad",
         sources=["gst", "electricity"],
         desc="Declared turnover checked against metered DISCOM electricity consumption."),
    dict(key="production_capacity_consistency", label="Production Capacity", kind="index",
         sources=["electricity", "epfo", "factory_licence"],
         desc="Sanctioned load, EPFO headcount and factory licence agree on real production scale."),
    dict(key="logistics_activity_index", label="Logistics Activity", kind="index",
         sources=["ewaybill", "vahan", "fastag"],
         desc="E-way-bill volume, registered fleet and FASTag toll crossings corroborate goods movement."),
    dict(key="premises_authenticity", label="Premises Authenticity", kind="index",
         sources=["property_tax", "shops_establishment", "gst"],
         desc="GST premises corroborated by independent municipal property-tax and Shops-&-Estab. records."),
    dict(key="business_continuity", label="Business Continuity", kind="index",
         sources=["bank", "upi", "gst"],
         desc="Bank, UPI and GST filing all continuously active — a going-concern signal."),
    dict(key="operational_stability", label="Operational Stability", kind="index",
         sources=["electricity", "epfo"],
         desc="Utility bills and EPFO contributions paid on time — obligations met, no arrears."),
    dict(key="b2g_credibility", label="B2G Credibility", kind="index",
         sources=["gem", "procurement"],
         desc="Government-counterparty-verified revenue (GeM POs / awarded tenders)."),
    dict(key="legal_risk_overlay", label="Legal-Risk Overlay", kind="flag_bad",
         sources=["courts", "insolvency", "mca21"],
         desc="Court, insolvency and director-disqualification screens — independent judicial signal."),
    dict(key="supply_chain_consistency", label="Supply-Chain Consistency", kind="index",
         sources=["dgft", "gst", "ewaybill"],
         desc="Customs trade flows, the GST return and e-way-bill movement tell one consistent story."),
    dict(key="export_orientation", label="Export Orientation", kind="index",
         sources=["dgft", "gst"],
         desc="DGFT export value cross-checked against IGST-heavy GST export markers."),
    dict(key="formal_identity_integrity", label="Formal-Identity Integrity", kind="index",
         sources=["udyam", "pan_gstin", "mca21"],
         desc="Udyam, PAN/GSTIN and MCA all resolve to one consistent legal entity."),
    dict(key="credit_exposure_mismatch", label="Credit-Exposure Cross-Check", kind="flag_bad",
         sources=["bank", "bureau"],
         desc="Bank EMI debits reconciled against bureau-declared obligations to surface undisclosed borrowing."),
]

# Observable master attributes shown on the scenario / entity card (never the
# true_* latents in the main flow — those live in a clearly-labelled synthetic
# ground-truth reveal on the Health Card).
_OBSERVABLE_ATTRS = ["name", "sector", "category", "state", "urban_rural", "age_years",
                     "employees", "incorporated", "gst_registered", "digital_adoption",
                     "exports", "sells_to_govt", "declared_turnover"]


# --------------------------------------------------------------------------- #
# Data model
# --------------------------------------------------------------------------- #
@dataclass
class Stage:
    index: int                    # 1..9
    key: str
    title: str
    caption: str
    duration: float               # suggested seconds for the staged reveal
    log: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Assessment:
    entity_id: str
    entity: Dict[str, Any]
    health_card: HealthCard
    engine_output: Dict[str, Any]
    stages: List[Stage]

    def stage(self, key: str) -> Optional[Stage]:
        return next((s for s in self.stages if s.key == key), None)


# --------------------------------------------------------------------------- #
# Scenario helpers
# --------------------------------------------------------------------------- #
_ARCHETYPE_BLURB = {
    "TEXTILE_MANUFACTURER": "Established exporter — clean books, the easy approve",
    "RETAIL_KIRANA": "Micro thin-file trader — the cautious-review case",
    "RESTAURANT": "Stressed young F&B business — repayment pressure",
    "IT_SERVICES": "Asset-light services firm — strong digital footprint",
    "AUTO_COMPONENTS": "Inflated-turnover showcase — benign PD, caught by authenticity",
    "LOGISTICS": "Fleet-based operator — heavy e-way-bill / FASTag trail",
}


def list_scenarios(engine: Optional[ScoringEngine] = None) -> List[dict]:
    """The named demo archetypes present in the cohort, in a stable demo order."""
    engine = engine or get_engine()
    master = engine.tables["msme_master"].set_index("entity_id")
    scenarios = []
    for eid in _ARCHETYPE_BLURB:
        if eid not in master.index:
            continue
        row = master.loc[eid]
        scenarios.append({
            "entity_id": eid,
            "name": row.get("name", eid),
            "sector": row.get("sector", ""),
            "category": row.get("category", ""),
            "turnover": float(row.get("declared_turnover", 0.0)),
            "blurb": _ARCHETYPE_BLURB[eid],
        })
    return scenarios


def random_entity_id(engine: Optional[ScoringEngine] = None, seed: Optional[int] = None) -> str:
    """Pick a randomised (non-archetype) cohort entity so repeat demos vary."""
    engine = engine or get_engine()
    master = engine.tables["msme_master"]
    pool = master[~master["entity_id"].isin(_ARCHETYPE_BLURB)]["entity_id"].tolist()
    if not pool:
        pool = master["entity_id"].tolist()
    import numpy as np
    rng = np.random.default_rng(seed)
    return str(pool[int(rng.integers(0, len(pool)))])


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _fmt_inr(x: float) -> str:
    """Indian-style short currency for logs/cards (₹1.2 Cr / ₹45.0 L)."""
    x = float(x or 0.0)
    if x >= 1e7:
        return f"₹{x / 1e7:.2f} Cr"
    if x >= 1e5:
        return f"₹{x / 1e5:.1f} L"
    return f"₹{x:,.0f}"


def _record_counts(engine: ScoringEngine, entity_id: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for stem, _label, _grp in SOURCE_CATALOG:
        df = engine.tables.get(stem)
        if df is None or df.empty or "entity_id" not in df.columns:
            counts[stem] = 0
        else:
            counts[stem] = int((df["entity_id"] == entity_id).sum())
    return counts


def _pillar_feature_counts() -> Dict[str, List[str]]:
    """pillar engineering-name -> list of its configured feature names."""
    _, feature_cfg = load_configs()
    return {pillar: list(feats.keys()) for pillar, feats in feature_cfg.items()}


# --------------------------------------------------------------------------- #
# Stage builders
# --------------------------------------------------------------------------- #
def _stage_scenario(entity: Dict[str, Any]) -> Stage:
    log = [
        f"Loading entity: {entity['name']} …",
        f"Sector: {entity.get('sector', '?')}  ·  Udyam category: {entity.get('category', '?')}",
        f"Vintage: {entity.get('age_years', '?')}y  ·  Headcount: {entity.get('employees', '?')}"
        f"  ·  Declared turnover: {_fmt_inr(entity.get('declared_turnover', 0))}",
        "Entity locked. Ready to assemble the digital footprint.",
    ]
    return Stage(1, "scenario_lock_in", "Scenario Lock-in",
                 "The selected MSME and its self-declared profile.", 1.5, log,
                 {"entity": entity})


def _stage_ingestion(engine: ScoringEngine, entity_id: str, feats: Dict[str, float]) -> Stage:
    counts = _record_counts(engine, entity_id)
    present = engine._present_sources(feats)  # presence predicates (real signal, not placeholder rows)
    sources, log = [], []
    connected = 0
    for stem, label, group in SOURCE_CATALOG:
        n = counts.get(stem, 0)
        # "Connected" = carries a real signal. Row-presence is the fallback for any
        # source without an explicit presence predicate.
        is_on = present.get(stem, n > 0)
        if is_on:
            connected += 1
        sources.append({"stem": stem, "label": label, "group": group,
                        "records": n, "connected": bool(is_on)})
        if is_on:
            log.append(f"  {label:<22} ✓  loaded {n} record(s)")
        else:
            log.append(f"  {label:<22} —  not on file")
    log.insert(0, f"Querying {len(SOURCE_CATALOG)} alternate-data sources …")
    log.append(f"Footprint assembled: {connected} of {len(SOURCE_CATALOG)} sources carry a live signal.")
    return Stage(2, "ingestion", "Data Ingestion — Breadth Reveal",
                 "Every alternate-data source queried; the ones that carry signal light up.",
                 5.0, log, {"sources": sources, "connected": connected,
                            "total": len(SOURCE_CATALOG)})


def _stage_integration(engine: ScoringEngine, entity_id: str, feats: Dict[str, float]) -> Stage:
    counts = _record_counts(engine, entity_id)
    present = engine._present_sources(feats)
    connected = sum(1 for stem, *_ in SOURCE_CATALOG if present.get(stem, counts.get(stem, 0) > 0))
    total_records = sum(counts.values())
    log = [
        "Resolving records to a canonical entity schema …",
        "Matching identity across GSTIN ↔ PAN ↔ Udyam ↔ MCA …",
        f"Identity integrity: {feats.get('formal_identity_integrity', 0.0):.2f} (1.0 = all registries agree)",
        f"Reconciled {total_records:,} raw records from {connected} sources into 1 entity node.",
    ]
    return Stage(3, "integration", "Data Integration",
                 "Fragmented records resolved into one canonical MSME.", 2.0, log,
                 {"connected": connected, "total_records": total_records,
                  "identity_integrity": round(feats.get("formal_identity_integrity", 0.0), 3)})


def _stage_features(feats: Dict[str, float]) -> Stage:
    labels = pillar_label_map()
    pillar_feats = _pillar_feature_counts()
    counters, log, total = [], [], 0
    for pillar, fnames in pillar_feats.items():
        n = len(fnames)
        total += n
        counters.append({"pillar": pillar, "label": labels.get(pillar, pillar), "count": n})
        log.append(f"  {labels.get(pillar, pillar):<22} 0 → {n} features")
    n_comp = len(COMPOSITE_CATALOG)
    log.insert(0, "Engineering per-source features …")
    log.append(f"  {'Cross-source composites':<22} 0 → {n_comp} indicators")
    log.append(f"Feature engineering complete: {total + n_comp} signals across 5 pillars.")
    return Stage(4, "features", "Feature Engineering",
                 "Raw records turned into pillar features and cross-source composites.",
                 2.5, log, {"counters": counters, "composite_count": n_comp,
                            "total_features": total + n_comp})


def _stage_synthesis(feats: Dict[str, float]) -> Stage:
    rationales = composite_rationales(feats)
    composites, log = [], ["Fusing independently-governed sources into composite signals …"]
    for spec in COMPOSITE_CATALOG:
        key = spec["key"]
        val = float(feats.get(key, 0.0))
        # Present the flagship as its 0-100 score; the rest as their native 0-1
        # index / flag. "flag_bad" composites are risk-when-high.
        if spec["kind"] == "score":
            display = f"{val:.0f}/100"
        else:
            display = f"{val:.2f}"
        rationale = rationales.get(key) or spec["desc"]
        composites.append({
            "key": key, "label": spec["label"], "value": round(val, 3),
            "display": display, "kind": spec["kind"], "sources": spec["sources"],
            "flagship": bool(spec.get("flagship")), "rationale": rationale,
        })
        mark = "★" if spec.get("flagship") else "✓"
        log.append(f"  {mark} {spec['label']:<26} {display}")
    log.append("Composite layer complete — signals harder to fake than any single source.")
    return Stage(5, "synthesis", "Cross-Source Synthesis",
                 "The differentiator: sources combined into manipulation-resistant composites.",
                 4.0, log, {"composites": composites})


def _stage_clustering(engine: ScoringEngine, out: Dict[str, Any]) -> Stage:
    scatter = engine.cohort_scatter()
    coord = out.get("peer_coord", (0.0, 0.0))
    seg = out.get("peer_segment", "Unclassified")
    log = [
        f"Standardising pillar-score space and running K-Means (k={engine.segmenter.k}) …",
        "Assigning peer group by nearest centroid …",
        f"Peer group: {seg}",
        "Note: segmentation is descriptive only — never part of the credit decision.",
    ]
    return Stage(6, "clustering", "Peer Segmentation",
                 "Who is this business like? A descriptive peer group (not the decision).",
                 2.5, log, {"scatter": scatter, "entity_point": {"x": coord[0], "y": coord[1]},
                            "segment": seg, "segment_id": out.get("peer_segment_id"),
                            "k": engine.segmenter.k})


def _stage_scoring(out: Dict[str, Any]) -> Stage:
    labels = pillar_label_map()
    pillars = [{"pillar": p, "label": labels.get(p, p), "score": round(s, 1)}
               for p, s in out["pillar_scores"].items()]
    log = [f"  {labels.get(p, p):<22} {round(s, 1):>5.1f} / 100"
           for p, s in out["pillar_scores"].items()]
    log.insert(0, "Scoring pillars from the frozen reference distribution …")
    log.append(f"Composite Financial Health Score: {out['composite_score']} / 100")
    log.append(f"CMR-style grade: {out['grade']} / 10  ·  Band: {out['onboarding_band']}")
    log.append(f"Model PD: {out['pd']:.3f}  ·  Risk category: {out['risk_category']}")
    return Stage(7, "scoring", "Scoring",
                 "Five dimension scores aggregate into the composite health score and grade.",
                 3.0, log, {
                     "pillars": pillars,
                     "composite_score": out["composite_score"],
                     "grade": out["grade"],
                     "onboarding_band": out["onboarding_band"],
                     "recommendation": out["recommendation"],
                     "pd": out["pd"], "pd_detail": out["pd_detail"],
                     "risk_category": out["risk_category"],
                     "credit_score_300_900": out["credit_score_300_900"],
                     "confidence": out["confidence"], "confidence_band": out["confidence_band"],
                     "sources_connected": out["sources_connected"],
                     "indicative_limit": out["indicative_limit"],
                 })


def _stage_explainability(engine: ScoringEngine, feats: Dict[str, float], out: Dict[str, Any]) -> Stage:
    shap_top: List[dict] = []
    if engine.shap is not None:
        try:
            for fname, val in engine.shap.top_features(feats, k=6):
                shap_top.append({"feature": fname, "shap": round(float(val), 4),
                                "direction": -1 if val > 0 else 1})  # +SHAP => toward default (risk)
        except Exception:
            shap_top = []
    log = ["Generating native reason codes from pillar component scores …"]
    for r in out["reasons_positive"]:
        log.append(f"  (+) {r['text']}")
    for r in out["reasons_negative"]:
        log.append(f"  (−) {r['text']}")
    log.append("Cross-checking with SHAP over the monotonic GBM PD path …")
    return Stage(8, "explainability", "Explainability",
                 "Top strengths and risks in plain language, with a SHAP cross-check.",
                 3.0, log, {"reasons_positive": out["reasons_positive"],
                            "reasons_negative": out["reasons_negative"],
                            "shap_top": shap_top})


def _stage_health_card(card: HealthCard) -> Stage:
    log = [
        "Assembling the Financial Health Card …",
        f"Recommendation: {card.recommendation}  ·  Indicative limit: {_fmt_inr(card.indicative_limit or 0)}",
        f"Confidence: {card.confidence}",
        "Assessment complete.",
    ]
    return Stage(9, "health_card", "Financial Health Card",
                 "The executive credit assessment, ready for the officer.", 2.5, log,
                 {"health_card": card.model_dump(),
                  "turnover_authenticity_score": card.turnover_authenticity_score})


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def run_assessment(entity_id: str, engine: Optional[ScoringEngine] = None) -> Assessment:
    """Compute one MSME assessment and decompose it into the 9 reveal stages."""
    engine = engine or get_engine()
    out = engine.score_entity(entity_id)
    feats = compute_entity_features(entity_id, engine.tables)
    card = build_health_card(out)

    master = engine.tables["msme_master"].set_index("entity_id")
    row = master.loc[entity_id].to_dict() if entity_id in master.index else {}
    entity = {k: row.get(k) for k in _OBSERVABLE_ATTRS}
    entity["entity_id"] = entity_id
    # Synthetic ground truth — surfaced only in a clearly-labelled reveal so judges
    # can verify the model actually caught what it should (honest about synthetic).
    entity["_true_health"] = row.get("true_health")
    entity["_true_honesty"] = row.get("true_honesty")

    stages = [
        _stage_scenario(entity),
        _stage_ingestion(engine, entity_id, feats),
        _stage_integration(engine, entity_id, feats),
        _stage_features(feats),
        _stage_synthesis(feats),
        _stage_clustering(engine, out),
        _stage_scoring(out),
        _stage_explainability(engine, feats, out),
        _stage_health_card(card),
    ]
    return Assessment(entity_id=entity_id, entity=entity, health_card=card,
                      engine_output=out, stages=stages)
