"""Deterministic pillar scoring -> composite health score -> 1-10 grade.

The interpretable-by-construction backbone (solution-design.md §5, deterministic-
first). Each feature is mapped to a 0-100 component via its percentile rank in a
FIXED training reference distribution, ORIENTED by its documented direction in
feature_config.yaml (+1 => higher is healthier, -1 => higher is riskier). Because
percentile rank is monotonic in the raw feature and the reference is frozen at
fit time, every pillar score — and the weighted composite — is provably monotonic
in each feature (Sprint-2 acceptance a).
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
import yaml

_CFG_DIR = Path(__file__).resolve().parents[2] / "config"


def load_configs():
    scoring = yaml.safe_load((_CFG_DIR / "scoring_config.yaml").read_text())
    features = yaml.safe_load((_CFG_DIR / "feature_config.yaml").read_text())
    return scoring, features


class PillarScorer:
    def __init__(self):
        self.scoring_cfg, self.feature_cfg = load_configs()
        self._refs: Dict[str, np.ndarray] = {}      # feature -> sorted reference values
        self._directions: Dict[str, int] = {}       # feature -> +1/-1
        self._pillar_feats: Dict[str, list] = {}
        # Composite calibration (z-map raw pillar-composite to a spread grade band).
        self._raw_mean, self._raw_std = 50.0, 12.0
        self._target_mean, self._target_std = 60.0, 18.0
        for pillar, feats in self.feature_cfg.items():
            self._pillar_feats[pillar] = list(feats.keys())
            for fname, spec in feats.items():
                self._directions[fname] = int(spec["direction"])

    # ------------------------------------------------------------------ fit
    def fit(self, feature_matrix: pd.DataFrame) -> "PillarScorer":
        for fname in self._directions:
            if fname in feature_matrix.columns:
                self._refs[fname] = np.sort(feature_matrix[fname].to_numpy())
        # Calibrate the composite spread from the training cohort's raw composites.
        # Iterate rows directly (robust to duplicate indices from bootstrap resamples).
        raws = np.array([self._raw_composite(self.pillar_scores(row.to_dict()))
                         for _, row in feature_matrix.iterrows()])
        self._raw_mean = float(raws.mean())
        self._raw_std = float(raws.std()) or 12.0
        return self

    # ------------------------------------------------------------- transform
    def _component(self, fname: str, value: float) -> float:
        ref = self._refs.get(fname)
        if ref is None or len(ref) == 0:
            return 50.0  # neutral if feature never seen
        pct = float(np.searchsorted(ref, value, side="right")) / len(ref)  # in (0,1], monotonic
        pct = min(max(pct, 0.0), 1.0)
        oriented = pct if self._directions[fname] > 0 else (1.0 - pct)
        return 100.0 * oriented

    def component_scores(self, feats: Dict[str, float]) -> Dict[str, float]:
        return {f: self._component(f, float(feats.get(f, 0.0))) for f in self._directions}

    def pillar_scores(self, feats: Dict[str, float]) -> Dict[str, float]:
        comps = self.component_scores(feats)
        out = {}
        for pillar, fnames in self._pillar_feats.items():
            vals = [comps[f] for f in fnames]
            out[pillar] = float(np.mean(vals)) if vals else 50.0
        return out

    # -------------------------------------------------------------- composite
    def _raw_composite(self, pillar_scores: Dict[str, float]) -> float:
        total_w, acc = 0.0, 0.0
        for pillar, spec in self.scoring_cfg["pillars"].items():
            w = float(spec["weight"])
            acc += w * pillar_scores.get(pillar, 50.0)
            total_w += w
        return float(acc / total_w) if total_w else 50.0

    def composite(self, pillar_scores: Dict[str, float]) -> float:
        """Calibrated composite: raw weighted-pillar score z-mapped to a spread
        band so grades populate the full 1-10 range. Linear in the raw score, so
        monotonicity in every feature is preserved."""
        raw = self._raw_composite(pillar_scores)
        z = (raw - self._raw_mean) / self._raw_std
        return float(np.clip(self._target_mean + z * self._target_std, 1.0, 99.0))

    def grade(self, composite_score: float) -> int:
        # Lower-bound logic (bands are contiguous by their `lo`); grade 1 = healthiest.
        for g in sorted(self.scoring_cfg["grade_bands"], key=lambda k: -self.scoring_cfg["grade_bands"][k][0]):
            lo, _ = self.scoring_cfg["grade_bands"][g]
            if composite_score >= lo:
                return int(g)
        return 10

    def onboarding_band(self, grade: int) -> str:
        for band, spec in self.scoring_cfg["onboarding_bands"].items():
            if grade in spec["grades"]:
                return band
        return "decline"

    def recommendation(self, band: str) -> str:
        return self.scoring_cfg["onboarding_bands"][band]["recommendation"]

    def indicative_limit(self, band: str, annual_turnover: float) -> float:
        frac = self.scoring_cfg["indicative_limit"]["turnover_fraction_by_band"].get(band, 0.0)
        return round(float(annual_turnover) * float(frac), 2)

    @property
    def pillar_names(self):
        return list(self.scoring_cfg["pillars"].keys())
