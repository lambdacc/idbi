"""SHAP explanations for the LightGBM PD path (solution-design.md §6).

TreeExplainer over the monotonic GBM; returns per-feature SHAP contributions to
P(default) for one entity (positive => pushes toward default). Feeds the
Explainability page's waterfall in Sprint 3.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd
import shap


class ShapExplainer:
    def __init__(self, gbm_model, features: List[str]):
        self.features = features
        self.explainer = shap.TreeExplainer(gbm_model)

    def explain(self, feats: Dict[str, float]) -> Dict[str, float]:
        X = pd.DataFrame([{f: feats.get(f, 0.0) for f in self.features}])
        vals = self.explainer.shap_values(X)
        if isinstance(vals, list):          # [class0, class1] -> positive class
            arr = np.asarray(vals[1])
        else:
            arr = np.asarray(vals)
            if arr.ndim == 3:               # (n, features, classes) -> positive class
                arr = arr[:, :, 1]
        row = arr[0]                        # single entity
        return {f: float(v) for f, v in zip(self.features, np.ravel(row))}

    def top_features(self, feats: Dict[str, float], k: int = 6) -> List[tuple]:
        contribs = self.explain(feats)
        return sorted(contribs.items(), key=lambda kv: -abs(kv[1]))[:k]
