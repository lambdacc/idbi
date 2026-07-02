"""K-Means peer segmentation — DESCRIPTIVE only, never the credit decision.

Groups MSMEs in 5-D pillar-score space for the "who is this business like" UI
moment. k in [3,5] chosen by silhouette. Clusters are named by their centroid's
average pillar strength so the label is human-readable (implementation-plan §5.4).
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
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
        # Cohort 2-D projection kept for the descriptive UI scatter (Sprint-3
        # clustering stage). PCA on the SAME scaled pillar space the KMeans uses,
        # so the plotted separation matches the actual segmentation.
        self.pca: Optional[PCA] = None
        self.coords_: Optional[np.ndarray] = None       # (n, 2) cohort coords
        self.labels_: Optional[np.ndarray] = None       # cohort cluster ids
        self.index_: List[str] = []                     # cohort entity ids

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
        # Descriptive-only 2-D projection of the cohort for the UI scatter.
        n_comp = 2 if X.shape[1] >= 2 and len(X) > 2 else 1
        self.pca = PCA(n_components=n_comp, random_state=self.seed)
        self.coords_ = self.pca.fit_transform(X)
        self.labels_ = self.model.labels_
        self.index_ = list(pillar_matrix.index)
        return self

    def predict(self, pillar_row: pd.DataFrame) -> int:
        return int(self.model.predict(self.scaler.transform(pillar_row))[0])

    def project(self, pillar_row: pd.DataFrame) -> Tuple[float, float]:
        """2-D coord of one entity in the same PCA space as the cohort scatter."""
        if self.pca is None:
            return (0.0, 0.0)
        xy = self.pca.transform(self.scaler.transform(pillar_row))[0]
        return (float(xy[0]), float(xy[1]) if len(xy) > 1 else 0.0)

    def cohort_scatter(self, names: Optional[Dict[str, str]] = None) -> List[dict]:
        """Cohort points for the peer-group scatter (x, y, cluster id, tier name)."""
        names = names or {}
        out: List[dict] = []
        if self.coords_ is None:
            return out
        two_d = self.coords_.shape[1] > 1
        for i, eid in enumerate(self.index_):
            cid = int(self.labels_[i])
            out.append({
                "entity_id": eid,
                "name": names.get(eid, eid),
                "x": float(self.coords_[i, 0]),
                "y": float(self.coords_[i, 1]) if two_d else 0.0,
                "cluster": cid,
                "tier": self.name(cid),
            })
        return out

    def name(self, cluster_id: int) -> str:
        return self._names[cluster_id] if 0 <= cluster_id < len(self._names) else "Unclassified"

    @property
    def k(self) -> int:
        return self.model.n_clusters if self.model else 0
