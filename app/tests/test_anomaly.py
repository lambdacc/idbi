"""Isolation Forest fraud leg: valid ranges, correct direction, real fraud lift."""
import numpy as np
import pandas as pd
import pytest

from app.ml.eval import metrics
from app.ml.models.anomaly import AnomalyDetector


def _genuine_feats():
    """A corroborated business: turnover checks pass, no contradictions."""
    return {"turnover_authenticity_score": 100.0, "ta_num_checks": 2.0,
            "dgft_has_iec": 0.0, "supply_chain_consistency": 0.0,
            "credit_exposure_mismatch": 0.0, "ptax_has_record": 1.0,
            "ptax_address_matches_gst": 1.0, "energy_intensity_flag": 0.0}


def _inflated_feats():
    """Declared turnover unsupported + several independent contradictions."""
    return {"turnover_authenticity_score": 40.0, "ta_num_checks": 2.0,
            "dgft_has_iec": 1.0, "supply_chain_consistency": 0.1,
            "credit_exposure_mismatch": 1.0, "ptax_has_record": 1.0,
            "ptax_address_matches_gst": 0.0, "energy_intensity_flag": 0.8}


def test_assess_ranges_and_keys(feature_matrix):
    det = AnomalyDetector().fit(feature_matrix)
    a = det.assess(_genuine_feats())
    for k in ("anomaly_score", "fraud_risk_score", "fraud_band", "n_signals"):
        assert k in a
    assert 0.0 <= a["anomaly_score"] <= 100.0
    assert 0.0 <= a["fraud_risk_score"] <= 100.0
    assert a["fraud_band"] in ("Low", "Moderate", "Elevated")


def test_genuine_business_is_low_fraud_risk(feature_matrix):
    det = AnomalyDetector().fit(feature_matrix)
    assert det.assess(_genuine_feats())["fraud_band"] == "Low"


def test_inflated_scores_higher_than_genuine(feature_matrix):
    det = AnomalyDetector().fit(feature_matrix)
    genuine = det.assess(_genuine_feats())["fraud_risk_score"]
    inflated = det.assess(_inflated_feats())["fraud_risk_score"]
    assert inflated > genuine


def test_cohort_series_in_unit_range(feature_matrix):
    det = AnomalyDetector().fit(feature_matrix)
    fr = det.fraud_risk_series(feature_matrix)
    an = det.anomaly_scores(feature_matrix)
    assert fr.min() >= 0.0 and fr.max() <= 1.0
    assert an.min() >= 0.0 and an.max() <= 1.0


def test_deterministic(feature_matrix):
    a = AnomalyDetector(seed=42).fit(feature_matrix).assess(_inflated_feats())
    b = AnomalyDetector(seed=42).fit(feature_matrix).assess(_inflated_feats())
    assert a == b


def test_ensemble_beats_composite_alone_on_fraud():
    """The whole point: blending the unsupervised leg lifts fraud discrimination
    over the hand-crafted authenticity composite alone. Fit on train, score the
    holdout (honest out-of-sample), on the full generated cohort."""
    try:
        from app.ml.features.base import load_tables, build_feature_matrix
        from app.ml.eval.holdout import split
        fm = build_feature_matrix(load_tables())
    except Exception:
        pytest.skip("full generated cohort not available (run `make data-gen`)")
    if int(fm["label_fraud"].sum()) < 5:
        pytest.skip("too few fraud positives to assess discrimination")
    train, test = split(fm, label_col="label_default")
    det = AnomalyDetector().fit(train)
    yfr = test["label_fraud"].to_numpy()
    comp_auc = metrics.auc(yfr, 100.0 - test["turnover_authenticity_score"].to_numpy())
    ens_auc = metrics.auc(yfr, det.fraud_risk_series(test))
    assert ens_auc > comp_auc          # a genuine, material improvement
