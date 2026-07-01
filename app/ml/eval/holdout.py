"""Leakage-resistant holdout split (solution-design.md §9, agentic-execution-plan §non-negotiable-2).

Design choices that resist the ways agents overfit weak evals:
  * split is done ONCE, up front, before any feature scaling/fitting;
  * stratified on the default label so both sides carry positives;
  * fixed seed => deterministic re-runs (ReconWise determinism);
  * the 6 named demo archetypes are forced into TRAIN so the demo entities are
    never silently used to report test metrics (a subtle leakage path).
"""
from __future__ import annotations

from typing import Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

ARCHETYPE_IDS = {
    "TEXTILE_MANUFACTURER", "RETAIL_KIRANA", "RESTAURANT",
    "IT_SERVICES", "AUTO_COMPONENTS", "LOGISTICS",
}


def split(feature_matrix: pd.DataFrame, label_col: str = "label_default",
          test_size: float = 0.3, seed: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    fm = feature_matrix
    demo = fm[fm.index.isin(ARCHETYPE_IDS)]
    pool = fm[~fm.index.isin(ARCHETYPE_IDS)]

    stratify = pool[label_col] if pool[label_col].nunique() > 1 else None
    train, test = train_test_split(
        pool, test_size=test_size, random_state=seed, stratify=stratify)
    # Demo archetypes always live in train, never in the reported test set.
    train = pd.concat([train, demo])
    return train, test
