"""Sprint-3 acceptance (b): exercise the callable pipeline-orchestrator functions
end-to-end for >=2 archetypes without exceptions — NOT the Streamlit UI itself.

Asserts the 9-stage state machine is well-formed and every stage carries the
structured `data` its visualization needs, so the frontend (a pure renderer) has
a stable contract to consume.
"""
import re

import pytest

from app.backend.schemas.models import HealthCard
from app.backend.services.pipeline_orchestrator import (COMPOSITE_CATALOG, SOURCE_CATALOG,
                                                         list_scenarios, random_entity_id,
                                                         run_assessment, verdict)

ARCHETYPES = ["TEXTILE_MANUFACTURER", "AUTO_COMPONENTS"]

# UI-humanization plan §5 G4 — banned in Simple mode / any technical=False copy.
# `Model PD` may appear in Technical only; bare "PD" is banned. Matched with word
# boundaries so words like "five" (contains "iv") or "drive" don't false-positive.
_BANNED_JARGON = ["SHAP", "WOE", "IV", "K-Means", "PCA", "centroid", "GBM",
                  "LightGBM", "monotonic", "percentile", "z-score",
                  "scorecard bins", "latent", "feature", "PD"]

# The flagship divergence sentence (CB-9 s3) — a stable substring to assert on.
_DIVERGENCE_MARKER = "A conventional scorecard would likely have approved"


def _jargon_hits(text: str) -> list:
    low = text.lower()
    hits = []
    for term in _BANNED_JARGON:
        if re.search(r"\b" + re.escape(term.lower()) + r"\b", low):
            hits.append(term)
    return hits

# stage key -> keys its .data dict must expose for the frontend
_STAGE_DATA_KEYS = {
    "scenario_lock_in": ["entity"],
    "ingestion": ["sources", "connected", "total"],
    "integration": ["connected", "total_records", "identity_integrity"],
    "features": ["counters", "composite_count", "total_features"],
    "synthesis": ["composites", "fraud"],
    "clustering": ["scatter", "entity_point", "segment", "k"],
    "scoring": ["pillars", "composite_score", "grade", "onboarding_band", "recommendation",
                "pd", "risk_category", "confidence_band"],
    "explainability": ["reasons_positive", "reasons_negative", "shap_top"],
    "health_card": ["health_card"],
}


def test_list_scenarios_present(engine):
    scenarios = list_scenarios(engine)
    ids = {s["entity_id"] for s in scenarios}
    assert len(scenarios) >= 2
    for eid in ARCHETYPES:
        assert eid in ids
    for s in scenarios:
        assert s["name"] and s["sector"] and s["blurb"]


@pytest.mark.parametrize("entity_id", ARCHETYPES)
def test_run_assessment_nine_stages(engine, entity_id):
    a = run_assessment(entity_id, engine)

    # exactly the 9 stages, in order, each with log + the expected data keys
    assert [s.index for s in a.stages] == list(range(1, 10))
    assert [s.key for s in a.stages] == list(_STAGE_DATA_KEYS.keys())
    for s in a.stages:
        assert s.log, f"stage {s.key} has no log lines"
        assert s.title and s.caption
        for key in _STAGE_DATA_KEYS[s.key]:
            assert key in s.data, f"stage {s.key} missing data['{key}']"

    # terminal health card is a valid typed payload with the full contract
    assert isinstance(a.health_card, HealthCard)
    assert 0 <= a.health_card.composite_score <= 100
    assert 1 <= a.health_card.grade <= 10
    assert len(a.health_card.pillars) == 5

    # ingestion breadth + clustering scatter are populated
    ing = a.stage("ingestion").data
    assert 0 < ing["connected"] <= ing["total"] == len(SOURCE_CATALOG)
    clu = a.stage("clustering").data
    assert len(clu["scatter"]) > 0
    assert set(clu["entity_point"]) == {"x", "y"}

    # every composite in the catalog is surfaced in the synthesis stage
    syn_keys = {c["key"] for c in a.stage("synthesis").data["composites"]}
    assert syn_keys == {c["key"] for c in COMPOSITE_CATALOG}


@pytest.mark.parametrize("entity_id", ARCHETYPES)
def test_every_stage_has_headline_and_findings(engine, entity_id):
    """UI-humanization WP-A: every stage carries a plain-language layer."""
    a = run_assessment(entity_id, engine)
    for s in a.stages:
        assert s.headline.strip(), f"stage {s.key} has an empty headline"
        assert len(s.findings) >= 1, f"stage {s.key} has no findings"
        for f in s.findings:
            assert set(f) >= {"text", "tone", "technical"}, f"malformed finding in {s.key}"
            assert f["tone"] in {"good", "warn", "risk", "neutral"}
            assert isinstance(f["technical"], bool)
            assert f["text"].strip()


@pytest.mark.parametrize("entity_id", ARCHETYPES)
def test_no_banned_jargon_in_simple_copy(engine, entity_id):
    """G4: headlines and any technical=False finding must be jargon-free."""
    a = run_assessment(entity_id, engine)
    for s in a.stages:
        hits = _jargon_hits(s.headline)
        assert not hits, f"stage {s.key} headline uses banned jargon {hits}: {s.headline!r}"
        for f in s.findings:
            if not f["technical"]:
                hits = _jargon_hits(f["text"])
                assert not hits, f"stage {s.key} simple finding uses {hits}: {f['text']!r}"
    # the verdict is Simple-mode copy too
    for line in a.verdict:
        hits = _jargon_hits(line)
        assert not hits, f"verdict line uses banned jargon {hits}: {line!r}"
    # technique plain-name + benefit are shown in Simple mode (only `algorithm` is
    # Technical-only), so they must also be jargon-free.
    for s in a.stages:
        if s.technique:
            for k in ("plain", "benefit"):
                hits = _jargon_hits(s.technique[k])
                assert not hits, f"stage {s.key} technique[{k}] uses {hits}: {s.technique[k]!r}"


def test_model_stages_disclose_technique(engine):
    """Every stage that runs an ML technique exposes it (name + plain benefit) so
    the UI can tell the user which model ran and why."""
    a = run_assessment("AUTO_COMPONENTS", engine)
    for key in ("features", "synthesis", "clustering", "scoring", "explainability"):
        tech = a.stage(key).technique
        assert tech and tech.get("plain") and tech.get("benefit") and tech.get("algorithm"), key
    # the fraud block is fully populated on the synthesis stage
    fraud = a.stage("synthesis").data["fraud"]
    assert set(fraud) >= {"authenticity_score", "anomaly_score", "fraud_risk_score", "fraud_band"}
    assert fraud["fraud_band"] in ("Low", "Moderate", "Elevated")


def test_verdict_divergence_fires_only_for_inflated_archetype(engine):
    """CB-9 s3: the turnover-authenticity divergence note appears for the inflated
    showcase (benign default risk + weak authenticity) but not the clean genuine
    manufacturer."""
    auto = run_assessment("AUTO_COMPONENTS", engine)
    textile = run_assessment("TEXTILE_MANUFACTURER", engine)

    assert any(_DIVERGENCE_MARKER in ln for ln in auto.verdict), auto.verdict
    assert not any(_DIVERGENCE_MARKER in ln for ln in textile.verdict), textile.verdict

    # verdict is 2–3 sentences and function output matches assessment attribute
    for a in (auto, textile):
        assert 2 <= len(a.verdict) <= 3
        assert a.verdict == verdict(a.engine_output, a.health_card)
        # stage 9 headline is the first verdict sentence
        assert a.stage("health_card").headline == a.verdict[0]


def test_inflated_archetype_authenticity_lower(engine):
    """The differentiator: the inflated showcase scores materially lower on the
    flagship Turnover-Authenticity check than the clean genuine manufacturer."""
    genuine = run_assessment("TEXTILE_MANUFACTURER", engine).health_card.turnover_authenticity_score
    inflated = run_assessment("AUTO_COMPONENTS", engine).health_card.turnover_authenticity_score
    assert inflated < genuine


def test_random_entity_id_valid(engine):
    eid = random_entity_id(engine, seed=7)
    assert eid in set(engine.tables["msme_master"]["entity_id"])


def test_glossary_entries_concise_and_jargon_free():
    """CB-10 / G4: every tooltip is <=25 words and free of banned jargon —
    tooltips are Simple-mode copy shown to non-technical bank users."""
    from app.frontend.components.glossary import GLOSSARY

    assert GLOSSARY, "glossary must not be empty"
    for key, text in GLOSSARY.items():
        assert text.strip(), f"glossary['{key}'] is empty"
        n_words = len(text.split())
        assert n_words <= 25, f"glossary['{key}'] is {n_words} words (>25): {text!r}"
        hits = _jargon_hits(text)
        assert not hits, f"glossary['{key}'] uses banned jargon {hits}: {text!r}"
