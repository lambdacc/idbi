"""End-to-end eval harness (Sprint-1 gate).

Loads the synthetic cohort, builds features, does a leakage-resistant split,
fits a baseline logistic model, and reports AUC/Gini/KS on the holdout plus PSI
train-vs-holdout. The Sprint-1 acceptance bar is that this RUNS and reports
numbers — tuning is Sprint 2. Prints a ReconWise-style release-gate scorecard.
"""
from __future__ import annotations

from typing import Dict, List

import pandas as pd

from ..features.base import load_tables, build_feature_matrix
from ..models.pillars import PillarScorer
from ..models.scorecard import WOEScorecard
from ..models.gbm import MonotonicGBM
from . import metrics
from .holdout import split
from .psi import psi_report

LABEL_COLS = ["label_default", "label_fraud"]


def _feature_cols(fm: pd.DataFrame) -> List[str]:
    return [c for c in fm.columns if c not in LABEL_COLS]


def run_eval(n_report_features: int = 12, seed: int = 42) -> Dict:
    tables = load_tables()
    fm = build_feature_matrix(tables)
    train, test = split(fm, label_col="label_default", seed=seed)
    feats = _feature_cols(fm)
    Xtr, ytr = train[feats], train["label_default"].to_numpy()
    Xte, yte = test[feats], test["label_default"]

    # The actual Sprint-2 models, fit on train, scored on the holdout.
    scorecard = WOEScorecard().fit(Xtr, ytr)
    gbm = MonotonicGBM().fit(Xtr, ytr)
    pillars = PillarScorer().fit(train)

    sc_metrics = metrics.summary(yte, scorecard.predict_pd(Xte))
    gbm_metrics = metrics.summary(yte, gbm.predict_pd(Xte))
    # Deterministic composite as a protective score: risk = 100 - health.
    composite = pd.Series(
        [100.0 - pillars.composite(pillars.pillar_scores(row.to_dict())) for _, row in Xte.iterrows()],
        index=Xte.index)
    comp_metrics = metrics.summary(yte, composite)

    # Fraud discrimination: flagship authenticity score alone (lower = more fraud).
    fraud_metrics = metrics.summary(test["label_fraud"], 100.0 - test["turnover_authenticity_score"])

    top = list(scorecard.top_iv(n_report_features).keys())
    psi = psi_report(train, test, top)

    return {
        "n_entities": int(len(fm)), "n_features": len(feats),
        "n_train": int(len(train)), "n_test": int(len(test)),
        "scorecard": sc_metrics, "gbm": gbm_metrics, "composite": comp_metrics,
        "fraud_authenticity": fraud_metrics,
        "psi_top_features": psi, "psi_max": max(psi.values()) if psi else 0.0,
    }


def print_scorecard(report: Dict) -> None:
    print("=" * 62)
    print(" CreditPulse — Eval Harness Scorecard (synthetic holdout)")
    print("=" * 62)
    print(f" entities={report['n_entities']}  features={report['n_features']}  "
          f"train={report['n_train']}  test={report['n_test']}")
    print(f"\n Default discrimination (synthetic holdout):")
    for name, key in [("WOE/IV scorecard", "scorecard"), ("Monotonic LightGBM", "gbm"),
                      ("Deterministic composite", "composite")]:
        m = report[key]
        print(f"   {name:24s} AUC={m['auc']:.3f}  Gini={m['gini']:.3f}  KS={m['ks']:.3f}")
    f = report["fraud_authenticity"]
    print(f" Fraud detection (Turnover-Authenticity alone):")
    print(f"   {'':24s} AUC={f['auc']:.3f}  Gini={f['gini']:.3f}  KS={f['ks']:.3f}  "
          f"(positives={f['positives']})")
    psi = report["psi_max"]
    psi_band = "stable" if psi < 0.1 else ("moderate" if psi < 0.25 else "significant shift")
    print(f"\n Stability: max PSI (train vs holdout) = {psi:.4f} ({psi_band})")
    print("\n Honesty note: metrics are on SYNTHETIC data calibrated to the")
    print(" generator. Real-default backtesting + recalibration is the")
    print(" productionization step, not a stage-1 claim.")
    print("=" * 62)


def main() -> None:
    print_scorecard(run_eval())


if __name__ == "__main__":
    main()
