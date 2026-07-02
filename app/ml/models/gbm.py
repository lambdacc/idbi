"""Monotonic-constrained LightGBM — optional PD lift model (implementation-plan §5.4).

Monotone constraints keep it bank-defensible: for a feature whose health direction
is +1 (higher = healthier), the constraint on P(default) is -1 (higher => lower
PD, never higher). Features absent from feature_config are left unconstrained (0).
This hard constraint is what the Sprint-2 monotonicity test relies on.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier

from .pillars import load_configs


def health_direction_map() -> Dict[str, int]:
    _, feature_cfg = load_configs()
    dirs: Dict[str, int] = {}
    for feats in feature_cfg.values():
        for fname, spec in feats.items():
            dirs[fname] = int(spec["direction"])
    return dirs


class MonotonicGBM:
    def __init__(self, **params):
        self.features_: List[str] = []
        self.health_dirs = health_direction_map()
        self.params = dict(
            n_estimators=200, num_leaves=15, learning_rate=0.05,
            min_child_samples=10, subsample=0.9, colsample_bytree=0.9,
            verbose=-1, **params)
        self.model: LGBMClassifier | None = None

    def _constraints(self, features: List[str]) -> List[int]:
        # PD constraint = negative of health direction (health +1 => PD -1).
        return [-self.health_dirs.get(f, 0) for f in features]

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "MonotonicGBM":
        self.features_ = list(X.columns)
        self.model = LGBMClassifier(
            monotone_constraints=self._constraints(self.features_),
            monotone_constraints_method="advanced", **self.params)
        self.model.fit(X[self.features_], y)
        return self

    def predict_pd(self, X: pd.DataFrame) -> np.ndarray:
        return self.model.predict_proba(X[self.features_])[:, 1]
