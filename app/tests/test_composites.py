"""Composite-indicator coverage + the flagship Turnover-Authenticity behaviour."""
from app.ml.features.composite_features import compute_composites, composite_rationales
from app.ml.features.turnover_authenticity import compute_turnover_authenticity


GENUINE = {  # declared turnover matches every evidence trail
    "gst_total_turnover": 1_000_000.0, "gst_present": 1.0,
    "bank_present": 1.0, "bank_total_inflow": 980_000.0,
    "ewb_present": 1.0, "ewb_total_value": 1_020_000.0,
    "itr_reported_income": 100_000.0,
}
INFLATED = {  # declared turnover far above real evidence
    "gst_total_turnover": 3_000_000.0, "gst_present": 1.0,
    "bank_present": 1.0, "bank_total_inflow": 900_000.0,
    "ewb_present": 1.0, "ewb_total_value": 950_000.0,
    "itr_reported_income": 90_000.0,
}
ROW = {"sector": "Manufacturing", "incorporated": True}


def test_authenticity_separates_genuine_from_inflated():
    g = compute_turnover_authenticity(GENUINE, ROW)["turnover_authenticity_score"]
    b = compute_turnover_authenticity(INFLATED, ROW)["turnover_authenticity_score"]
    assert g >= 85, f"genuine should score high, got {g}"
    assert b <= 60, f"inflated should score low, got {b}"
    assert g - b >= 25


def test_authenticity_neutral_when_no_gst():
    out = compute_turnover_authenticity({"gst_total_turnover": 0.0}, ROW)
    assert out["ta_num_checks"] == 0.0
    assert out["turnover_authenticity_score"] == 60.0  # neutral, never penalised


def test_composites_all_present_and_bounded(feature_matrix):
    expected = {"turnover_authenticity_score", "energy_intensity_flag",
                "production_capacity_consistency", "logistics_activity_index",
                "premises_authenticity", "business_continuity", "operational_stability",
                "b2g_credibility", "legal_risk_overlay", "export_orientation",
                "formal_identity_integrity", "credit_exposure_mismatch"}
    assert expected <= set(feature_matrix.columns)
    # bounded composites in [0,1]; authenticity in [0,100]
    for c in expected - {"turnover_authenticity_score"}:
        assert feature_matrix[c].between(0.0, 1.0).all(), f"{c} out of [0,1]"
    assert feature_matrix["turnover_authenticity_score"].between(0, 100).all()


def test_rationales_are_strings():
    r = composite_rationales(compute_composites(GENUINE, ROW))
    assert "turnover_authenticity_score" in r
    assert all(isinstance(v, str) and v for v in r.values())
