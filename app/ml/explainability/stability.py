"""Reason-code stability across recalibration (solution-design.md §6).

Research flagged SHAP instability; we test that the top reason codes for a fixed
entity stay consistent when the models are refit on bootstrap resamples. Reported
as mean pairwise Jaccard overlap of the top-reason feature sets across refits.
"""
from __future__ import annotations

from itertools import combinations
from typing import Callable, List, Set


def jaccard(a: Set, b: Set) -> float:
    if not a and not b:
        return 1.0
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def stability_across_refits(refit_reason_features: Callable[[int], Set], seeds: List[int]) -> float:
    """`refit_reason_features(seed)` refits models on a resample and returns the
    set of top reason-code features for the reference entity. Returns mean pairwise
    Jaccard across the given seeds (1.0 = perfectly stable)."""
    sets = [refit_reason_features(s) for s in seeds]
    pairs = list(combinations(sets, 2))
    if not pairs:
        return 1.0
    return sum(jaccard(a, b) for a, b in pairs) / len(pairs)
