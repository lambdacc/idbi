"""ScoringEngine — fits every model and assembles the Health Card payload.

Wiring (implementation-plan.md §5.1):
  features -> deterministic pillars -> composite -> 1-10 grade -> bands   (backbone)
           -> WOE scorecard + monotonic GBM -> PD / risk category         (ML lift)
           -> K-Means -> peer segment (descriptive)
           -> confidence (source-coverage x IV)
           -> reason codes (native) + SHAP (GBM path)

Models are fit in-memory from the synthetic cohort (fast on ~400 rows,
deterministic). `ml/` stays framework-free; label mapping happens in backend.
"""
from __future__ import annotations

import pickle
from typing import Dict, List

import numpy as np
import pandas as pd

from .features.base import (DATA_DIR, build_feature_matrix, compute_entity_features,
                            load_tables, _ensure_modules_loaded, _FEATURE_FUNCS)
from .features.composite_features import compute_composites, composite_rationales
from .models.pillars import PillarScorer
from .models.scorecard import WOEScorecard
from .models.gbm import MonotonicGBM
from .models.clustering import PeerSegmenter
from .models.confidence_score import ConfidenceScorer
from .explainability.reason_codes import generate_reason_codes
from .explainability.shap_explainer import ShapExplainer

LABEL_COLS = ["label_default", "label_fraud"]

# Source -> (feature, is-meaningfully-present predicate). Placeholder rows
# (has_*=0) must NOT count as "connected" — completeness means real signal.
PRESENCE_FLAGS = {
    "gst": lambda f: f.get("gst_present", 0) > 0,
    "bank": lambda f: f.get("bank_present", 0) > 0,
    "upi": lambda f: f.get("upi_present", 0) > 0,
    "epfo": lambda f: f.get("epfo_present", 0) > 0,
    "bureau": lambda f: f.get("bureau_has_record", 0) > 0,
    "ewaybill": lambda f: f.get("ewb_present", 0) > 0,
    "electricity": lambda f: f.get("electricity_present", 0) > 0,
    "udyam": lambda f: f.get("udyam_registered", 0) > 0,
    "pan_gstin": lambda f: f.get("gstin_active", 0) > 0,
    "property_tax": lambda f: f.get("ptax_has_record", 0) > 0,
    "vahan": lambda f: f.get("vahan_num_vehicles", 0) > 0,
    "fastag": lambda f: f.get("fastag_toll_crossings_total", 0) > 0,
    "factory_licence": lambda f: f.get("factory_has_licence", 0) > 0,
    "gem": lambda f: f.get("gem_is_seller", 0) > 0,
    "procurement": lambda f: f.get("proc_tenders_won", 0) > 0,
    "mca21": lambda f: f.get("mca_has_record", 0) > 0,
    "itr": lambda f: f.get("itr_reported_income", 0) > 0,
    "dgft": lambda f: f.get("dgft_has_iec", 0) > 0,
    "fssai": lambda f: f.get("fssai_has_licence", 0) > 0,
    "pollution": lambda f: f.get("pollution_has_consent", 0) > 0,
    "shops_establishment": lambda f: f.get("shops_registered", 0) > 0,
    "insurance": lambda f: f.get("insurance_sum_insured", 0) > 0,
    "ecommerce": lambda f: f.get("ecom_gmv", 0) > 0,
    # Public negative-screens are always queryable, so always "connected".
    "courts": lambda f: True,
    "insolvency": lambda f: True,
}


def build_feature_source_map() -> Dict[str, str]:
    """feature name -> originating source (via each fn's keys on empty input)."""
    _ensure_modules_loaded()
    dummy = {"sector": "Services", "age_years": 5.0, "incorporated": False}
    fmap: Dict[str, str] = {}
    for source, fn in _FEATURE_FUNCS.items():
        for key in (fn(pd.DataFrame(), dummy) or {}):
            fmap[key] = source
    for key in compute_composites({}, dummy):
        fmap[key] = "composite"
    return fmap


class ScoringEngine:
    def __init__(self):
        self.tables = None
        self.feature_matrix: pd.DataFrame | None = None
        self.feature_cols: List[str] = []
        self.pillars = PillarScorer()
        self.scorecard = WOEScorecard()
        self.gbm = MonotonicGBM()
        self.segmenter = PeerSegmenter()
        self.confidence = ConfidenceScorer()
        self.shap: ShapExplainer | None = None
        self._present_by_source: Dict[str, set] = {}
        self._data_sources: List[str] = []

    # ------------------------------------------------------------------ fit
    def fit(self, tables=None) -> "ScoringEngine":
        self.tables = tables or load_tables()
        fm = build_feature_matrix(self.tables)
        self.feature_matrix = fm
        self.feature_cols = [c for c in fm.columns if c not in LABEL_COLS]
        X, y = fm[self.feature_cols], fm["label_default"].to_numpy()

        self.pillars.fit(fm)
        self.scorecard.fit(X, y)
        self.gbm.fit(X, y)
        self.shap = ShapExplainer(self.gbm.model, self.gbm.features_)

        # Peer segmentation in pillar-score space.
        pillar_mat = pd.DataFrame(
            {eid: self.pillars.pillar_scores(fm.loc[eid].to_dict()) for eid in fm.index}).T
        self._pillar_cols = list(pillar_mat.columns)
        self._pillar_mat = pillar_mat
        self.segmenter.fit(pillar_mat)

        # Confidence weights from IV per source. Exclude derived composites — they
        # aren't an independent data source for the completeness measure.
        fmap = {f: s for f, s in build_feature_source_map().items() if s != "composite"}
        self.confidence.fit(self.scorecard.binner.iv_, fmap)

        return self

    # --------------------------------------------------------------- scoring
    def cohort_scatter(self) -> List[dict]:
        """Cohort peer-group scatter (descriptive only) for the clustering stage."""
        master = self.tables["msme_master"].set_index("entity_id")
        names = {eid: (master.loc[eid].get("name", eid) if eid in master.index else eid)
                 for eid in self.segmenter.index_}
        return self.segmenter.cohort_scatter(names)

    def _present_sources(self, feats: Dict[str, float]) -> Dict[str, bool]:
        return {s: bool(pred(feats)) for s, pred in PRESENCE_FLAGS.items()}

    def _pd(self, X: pd.DataFrame) -> Dict[str, float]:
        pd_card = float(self.scorecard.predict_pd(X)[0])
        pd_gbm = float(self.gbm.predict_pd(X)[0])
        return {"pd_scorecard": pd_card, "pd_gbm": pd_gbm, "pd_blended": (pd_card + pd_gbm) / 2}

    @staticmethod
    def _risk_category(pd_val: float) -> str:
        if pd_val < 0.05:
            return "Low"
        if pd_val < 0.15:
            return "Medium"
        if pd_val < 0.35:
            return "High"
        return "Very High"

    def score_entity(self, entity_id: str) -> Dict:
        feats = compute_entity_features(entity_id, self.tables)
        X = pd.DataFrame([{c: feats.get(c, 0.0) for c in self.feature_cols}])

        pillar_scores = self.pillars.pillar_scores(feats)
        composite = self.pillars.composite(pillar_scores)
        grade = self.pillars.grade(composite)
        band = self.pillars.onboarding_band(grade)
        recommendation = self.pillars.recommendation(band)

        annual_turnover = feats.get("gst_total_turnover", 0.0) or feats.get("bank_total_inflow", 0.0)
        pds = self._pd(X)

        present = self._present_sources(feats)
        conf = self.confidence.score(present)

        comp_scores = self.pillars.component_scores(feats)
        pos, neg = generate_reason_codes(comp_scores, self.pillars.feature_cfg, composite_rationales(feats))

        pillar_row = pd.DataFrame([pillar_scores])[self._pillar_cols]
        seg_id = self.segmenter.predict(pillar_row)

        return {
            "entity_id": entity_id,
            "name": self.tables["msme_master"].set_index("entity_id").loc[entity_id].get("name", entity_id),
            "pillar_scores": pillar_scores,
            "peer_segment_id": seg_id,
            "peer_coord": self.segmenter.project(pillar_row),
            "composite_score": round(composite, 1),
            "grade": grade,
            "onboarding_band": band,
            "recommendation": recommendation,
            "pd": round(pds["pd_blended"], 4),
            "pd_detail": {k: round(v, 4) for k, v in pds.items()},
            "risk_category": self._risk_category(pds["pd_blended"]),
            "credit_score_300_900": int(self.scorecard.credit_score_300_900(X)[0]),
            "confidence": round(conf, 3),
            "confidence_band": self.confidence.band(conf),
            "sources_connected": self.confidence.sources_connected(present),
            "turnover_authenticity_score": feats.get("turnover_authenticity_score", 0.0),
            "peer_segment": self.segmenter.name(seg_id),
            "indicative_limit": self.pillars.indicative_limit(band, annual_turnover),
            "reasons_positive": pos,
            "reasons_negative": neg,
        }


    # ------------------------------------------------------------- persistence
    # The SHAP TreeExplainer holds C-extension state — dropped on pickle and
    # rebuilt from the fitted GBM on load (cheap, deterministic).
    def __getstate__(self):
        state = self.__dict__.copy()
        state["shap"] = None
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        if self.gbm is not None and getattr(self.gbm, "model", None) is not None:
            self.shap = ShapExplainer(self.gbm.model, self.gbm.features_)

    def save(self, path=None) -> "ScoringEngine":
        path = path or ENGINE_PICKLE
        with open(path, "wb") as fh:
            pickle.dump(self, fh)
        return self


ENGINE_PICKLE = DATA_DIR / "engine.pkl"

_ENGINE: ScoringEngine | None = None


def _load_prefit() -> ScoringEngine | None:
    """Load the build-time pre-fit engine iff it isn't stale vs the cohort."""
    master = DATA_DIR / "msme_master.csv"
    try:
        if not (ENGINE_PICKLE.exists() and master.exists()):
            return None
        if ENGINE_PICKLE.stat().st_mtime < master.stat().st_mtime:
            return None  # cohort regenerated after the pickle — refit
        with open(ENGINE_PICKLE, "rb") as fh:
            return pickle.load(fh)
    except Exception:
        return None  # any load problem -> fall back to a fresh fit


def get_engine() -> ScoringEngine:
    """Cached singleton: pre-fit pickle when fresh (Cloud Run cold-start), else fit."""
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = _load_prefit() or ScoringEngine().fit()
    return _ENGINE
