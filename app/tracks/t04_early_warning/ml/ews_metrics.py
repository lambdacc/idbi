"""Track-04 early-warning evaluation (WP-4M spec §Build.4).

Headline is NOT accuracy — it is **lead time**: how many months earlier the
alt-data EWS turns Red versus the repayment-only baseline (the internal
SAJAG-style stand-in), and capture@top-decile. AUC is reported but not headlined.

All numbers are computed on the ENTITY-LEVEL holdout so nothing the model trained
on inflates them. Import of `app.ml.eval.metrics` is read-only reuse of the
platform kit.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from app.ml.eval.metrics import auc


# --------------------------------------------------------------------------- #
# Primitive metrics.
# --------------------------------------------------------------------------- #
def capture_at_decile(y_true, score, frac: float = 0.10) -> float:
    """Fraction of all positives that fall in the top-`frac` highest-scored rows."""
    y = np.asarray(y_true, dtype=int)
    s = np.asarray(score, dtype=float)
    total_pos = int(y.sum())
    if total_pos == 0 or len(y) == 0:
        return float("nan")
    k = max(1, int(round(len(y) * frac)))
    top = np.argsort(-s)[:k]
    return float(y[top].sum() / total_pos)


def precision_recall_at_band(y_true, band, positive_band: str = "Red") -> Dict[str, float]:
    y = np.asarray(y_true, dtype=int)
    flag = np.asarray([b == positive_band for b in band], dtype=int)
    tp = int(((flag == 1) & (y == 1)).sum())
    fp = int(((flag == 1) & (y == 0)).sum())
    fn = int(((flag == 0) & (y == 1)).sum())
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    return {"precision": precision, "recall": recall, "alerts": int(flag.sum())}


def _pctiles(vals: List[int]) -> Dict[str, float]:
    if not vals:
        return {"median": float("nan"), "p25": float("nan"), "p75": float("nan"), "n": 0}
    a = np.asarray(vals, dtype=float)
    return {"median": float(np.median(a)), "p25": float(np.percentile(a, 25)),
            "p75": float(np.percentile(a, 75)), "n": int(len(a))}


# --------------------------------------------------------------------------- #
# Lead-time distribution (the differentiator).
# --------------------------------------------------------------------------- #
def lead_times(engine, entities: List[str]) -> Dict[str, object]:
    """Per-entity months-before-default that each model first went Red, for the
    given defaulter entities. `paired` restricts to entities BOTH models alerted
    on (the conservative gap the thesis test uses)."""
    ews, base, paired_ews, paired_base = [], [], [], []
    for eid in entities:
        d = engine._default_month.get(eid)
        if d is None or engine._is_defaulter.get(eid, 0) != 1:
            continue
        fa = engine._first_alerts.get(eid, {})
        fe, fb = fa.get("ews"), fa.get("baseline")
        le = (d - fe) if fe is not None else None
        lb = (d - fb) if fb is not None else None
        if le is not None and le > 0:
            ews.append(le)
        if lb is not None and lb > 0:
            base.append(lb)
        if le is not None and le > 0 and lb is not None and lb > 0:
            paired_ews.append(le); paired_base.append(lb)
    gap = (float(np.median(paired_ews) - np.median(paired_base))
           if paired_ews else float("nan"))
    return {
        "ews": _pctiles(ews),
        "baseline": _pctiles(base),
        "paired_ews": _pctiles(paired_ews),
        "paired_baseline": _pctiles(paired_base),
        "median_gap": gap,
        "n_paired": len(paired_ews),
    }


# --------------------------------------------------------------------------- #
# Scorecard.
# --------------------------------------------------------------------------- #
def compute_scorecard(engine, snaps: pd.DataFrame) -> Dict[str, object]:
    ho = snaps[snaps["entity_id"].isin(engine._holdout_entities)]
    y12 = ho["default_within_12m"].to_numpy()

    ews_auc = auc(y12, ho["ews_pd"].to_numpy())
    base_auc = auc(ho["default_within_3m"].to_numpy(), ho["baseline_pd"].to_numpy())

    cap_ews = capture_at_decile(y12, ho["ews_pd"].to_numpy())
    cap_base = capture_at_decile(y12, ho["baseline_pd"].to_numpy())

    pr_ews = precision_recall_at_band(y12, ho["ews_band"].tolist())

    holdout_defaulters = [e for e in engine._holdout_entities
                          if engine._is_defaulter.get(e, 0) == 1]
    lt = lead_times(engine, holdout_defaulters)

    non_def = [e for e in engine._holdout_entities
               if engine._is_defaulter.get(e, 0) == 0]
    false_alert = float(np.mean([
        engine._first_alerts.get(e, {}).get("ews") is not None for e in non_def
    ])) if non_def else float("nan")

    return {
        "holdout_auc_ews": ews_auc,
        "holdout_auc_baseline": base_auc,
        "capture_decile_ews": cap_ews,
        "capture_decile_baseline": cap_base,
        "alert_precision_red": pr_ews["precision"],
        "alert_recall_red": pr_ews["recall"],
        "lead_time": lt,
        "median_lead_ews": lt["ews"]["median"],
        "median_lead_baseline": lt["baseline"]["median"],
        "median_lead_gap": lt["median_gap"],
        "false_alert_rate": false_alert,
        "n_holdout_defaulters": len(holdout_defaulters),
    }


def format_scorecard(ev: Dict[str, object]) -> str:
    lt = ev["lead_time"]

    def _f(x, d=3):
        try:
            return f"{float(x):.{d}f}"
        except (TypeError, ValueError):
            return "  n/a"

    lines = [
        "=" * 62,
        "  TRACK-04 EARLY-WARNING SCORECARD  (entity-level holdout)",
        "=" * 62,
        f"  Holdout AUC        EWS {_f(ev['holdout_auc_ews'])}   "
        f"baseline {_f(ev['holdout_auc_baseline'])}",
        f"  Capture@decile     EWS {_f(ev['capture_decile_ews'])}   "
        f"baseline {_f(ev['capture_decile_baseline'])}",
        f"  Red alert P / R    {_f(ev['alert_precision_red'])} / "
        f"{_f(ev['alert_recall_red'])}",
        f"  False-alert rate   {_f(ev['false_alert_rate'])} (non-defaulters)",
        "-" * 62,
        "  LEAD TIME (months of warning before default)",
        f"    EWS        median {_f(lt['ews']['median'],1)}  "
        f"[p25 {_f(lt['ews']['p25'],1)} .. p75 {_f(lt['ews']['p75'],1)}]  "
        f"n={lt['ews']['n']}",
        f"    baseline   median {_f(lt['baseline']['median'],1)}  "
        f"[p25 {_f(lt['baseline']['p25'],1)} .. p75 {_f(lt['baseline']['p75'],1)}]  "
        f"n={lt['baseline']['n']}",
        f"    >>> median lead-time gap (EWS - baseline): "
        f"{_f(ev['median_lead_gap'],1)} months  (paired n={lt['n_paired']})",
        "=" * 62,
    ]
    return "\n".join(lines)
