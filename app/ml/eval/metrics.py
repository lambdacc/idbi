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


def brier(y_true, y_prob) -> float:
    """Mean squared error of the probability forecast — lower is better-calibrated."""
    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.asarray(y_prob, dtype=float)
    return float(np.mean((y_prob - y_true) ** 2))


def ece(y_true, y_prob, bins: int = 10) -> float:
    """Expected Calibration Error: average |confidence - accuracy| over prob bins,
    weighted by bin population. 0 = predicted probabilities match observed rates."""
    y_true = np.asarray(y_true, dtype=float)
    y_prob = np.clip(np.asarray(y_prob, dtype=float), 0.0, 1.0)
    edges = np.linspace(0.0, 1.0, bins + 1)
    idx = np.clip(np.digitize(y_prob, edges[1:-1], right=False), 0, bins - 1)
    n = len(y_prob)
    total = 0.0
    for b in range(bins):
        mask = idx == b
        if not np.any(mask):
            continue
        conf = float(np.mean(y_prob[mask]))
        acc = float(np.mean(y_true[mask]))
        total += (np.sum(mask) / n) * abs(conf - acc)
    return float(total)


def calibration(y_true, y_prob) -> Dict[str, float]:
    return {"brier": brier(y_true, y_prob), "ece": ece(y_true, y_prob)}
