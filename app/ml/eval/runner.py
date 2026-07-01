"""End-to-end eval harness (Sprint-1 gate).

Loads the synthetic cohort, builds features, does a leakage-resistant split,
fits a baseline logistic model, and reports AUC/Gini/KS on the holdout plus PSI
train-vs-holdout. The Sprint-1 acceptance bar is that this RUNS and reports
numbers — tuning is Sprint 2. Prints a ReconWise-style release-gate scorecard.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from ..features.base import load_tables, build_feature_matrix
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
    scaler = StandardScaler().fit(train[feats])
    Xtr, Xte = scaler.transform(train[feats]), scaler.transform(test[feats])

    model = LogisticRegression(max_iter=1000, class_weight="balanced")
    model.fit(Xtr, train["label_default"])
    proba = model.predict_proba(Xte)[:, 1]

    default_metrics = metrics.summary(test["label_default"], proba)

    # Fraud discrimination: the flagship authenticity score alone (lower = worse),
    # so a higher predicted fraud risk = (100 - authenticity).
    fraud_score = 100.0 - test["turnover_authenticity_score"]
    fraud_metrics = metrics.summary(test["label_fraud"], fraud_score)

    # PSI on the highest-|coef| features.
    top = list(pd.Series(np.abs(model.coef_[0]), index=feats).sort_values(ascending=False).head(n_report_features).index)
    psi = psi_report(train, test, top)

    report = {
        "n_entities": int(len(fm)), "n_features": len(feats),
        "n_train": int(len(train)), "n_test": int(len(test)),
        "default_model": default_metrics,
        "fraud_authenticity": fraud_metrics,
        "psi_top_features": psi,
        "psi_max": max(psi.values()) if psi else 0.0,
    }
    return report


def print_scorecard(report: Dict) -> None:
    print("=" * 62)
    print(" CreditPulse — Eval Harness Scorecard (synthetic holdout)")
    print("=" * 62)
    print(f" entities={report['n_entities']}  features={report['n_features']}  "
          f"train={report['n_train']}  test={report['n_test']}")
    d = report["default_model"]
    print(f"\n Default model (baseline logistic):")
    print(f"   AUC={d['auc']:.3f}  Gini={d['gini']:.3f}  KS={d['ks']:.3f}  "
          f"(n={d['n']}, positives={d['positives']})")
    f = report["fraud_authenticity"]
    print(f" Fraud detection (Turnover-Authenticity score alone):")
    print(f"   AUC={f['auc']:.3f}  Gini={f['gini']:.3f}  KS={f['ks']:.3f}  "
          f"(n={f['n']}, positives={f['positives']})")
    print(f"\n Stability: max PSI (train vs holdout) = {report['psi_max']:.4f} "
          f"({'stable' if report['psi_max'] < 0.1 else 'shift'})")
    print("\n Honesty note: metrics are on SYNTHETIC data calibrated to the")
    print(" generator. Real-default backtesting + recalibration is the")
    print(" productionization step, not a stage-1 claim.")
    print("=" * 62)


def main() -> None:
    print_scorecard(run_eval())


if __name__ == "__main__":
    main()
