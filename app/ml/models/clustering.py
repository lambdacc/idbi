"""K-Means peer segmentation — DESCRIPTIVE only, never the credit decision.

Groups MSMEs in 5-D pillar-score space for the "who is this business like" UI
moment. k in [3,5] chosen by silhouette. Clusters are named by their centroid's
average pillar strength so the label is human-readable (implementation-plan §5.4).
"""
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

_TIER_NAMES = ["Established / Strong performers", "Growing / Stable operators",
               "Emerging businesses", "Thin-file / Watch", "High-risk / Distressed"]


class PeerSegmenter:
    def __init__(self, k_range=(3, 4, 5), seed: int = 42):
        self.k_range = k_range
        self.seed = seed
        self.scaler = StandardScaler()
        self.model: KMeans | None = None
        self._names: List[str] = []

    def fit(self, pillar_matrix: pd.DataFrame) -> "PeerSegmenter":
        X = self.scaler.fit_transform(pillar_matrix)
        best_k, best_s = self.k_range[0], -1.0
        for k in self.k_range:
            if len(X) <= k:
                continue
            km = KMeans(n_clusters=k, random_state=self.seed, n_init=10).fit(X)
            s = silhouette_score(X, km.labels_)
            if s > best_s:
                best_k, best_s = k, s
        self.model = KMeans(n_clusters=best_k, random_state=self.seed, n_init=10).fit(X)
        # Rank clusters by centroid average strength -> tiered names.
        centroid_strength = self.model.cluster_centers_.mean(axis=1)
        order = np.argsort(-centroid_strength)          # strongest first
        self._names = [""] * best_k
        for rank, cluster_id in enumerate(order):
            self._names[cluster_id] = _TIER_NAMES[min(rank, len(_TIER_NAMES) - 1)]
        return self

    def predict(self, pillar_row: pd.DataFrame) -> int:
        return int(self.model.predict(self.scaler.transform(pillar_row))[0])

    def name(self, cluster_id: int) -> str:
        return self._names[cluster_id] if 0 <= cluster_id < len(self._names) else "Unclassified"

    @property
    def k(self) -> int:
        return self.model.n_clusters if self.model else 0
