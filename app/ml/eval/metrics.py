"""Discrimination metrics — AUC / Gini / KS (solution-design.md §9)."""
from __future__ import annotations

from typing import Dict

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve


def auc(y_true, y_score) -> float:
    y_true = np.asarray(y_true)
    if len(np.unique(y_true)) < 2:
        return float("nan")
    return float(roc_auc_score(y_true, y_score))


def gini(y_true, y_score) -> float:
    a = auc(y_true, y_score)
    return float(2 * a - 1) if a == a else float("nan")  # nan-safe


def ks(y_true, y_score) -> float:
    """Kolmogorov-Smirnov: max gap between TPR and FPR cumulative curves."""
    y_true = np.asarray(y_true)
    if len(np.unique(y_true)) < 2:
        return float("nan")
    fpr, tpr, _ = roc_curve(y_true, y_score)
    return float(np.max(tpr - fpr))


def summary(y_true, y_score) -> Dict[str, float]:
    return {"auc": auc(y_true, y_score), "gini": gini(y_true, y_score),
            "ks": ks(y_true, y_score), "n": int(len(y_true)),
            "positives": int(np.sum(np.asarray(y_true)))}
