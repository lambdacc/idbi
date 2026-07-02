"""Feature-module coverage: keys present, numeric, empty-input safe."""
import math

import pandas as pd
import pytest

from app.ml.features import base as fbase


def test_feature_matrix_numeric_no_nan(feature_matrix):
    assert feature_matrix.shape[0] > 0
    assert int(feature_matrix.isna().sum().sum()) == 0
    # Every column numeric.
    assert all(pd.api.types.is_numeric_dtype(t) for t in feature_matrix.dtypes)


def test_every_source_has_feature_fn():
    # All 24 feature sources register (POS/QR + insurance-only sources collapsed).
    assert len(fbase.registered_sources()) == 24


@pytest.mark.parametrize("source", fbase.registered_sources())
def test_feature_fn_handles_empty_input(source):
    """Each per-source fn must degrade gracefully on an empty DataFrame."""
    fbase._ensure_modules_loaded()
    fn = fbase._FEATURE_FUNCS[source]
    master_row = {"sector": "Services", "age_years": 5.0, "incorporated": False}
    out = fn(pd.DataFrame(), master_row)
    assert isinstance(out, dict)
    for k, v in out.items():
        assert isinstance(v, (int, float)) and not math.isnan(float(v)), f"{source}.{k} not clean numeric"


def test_gst_features_values(tables):
    """Sanity: a GST-registered entity has positive turnover + regularity in [0,1]."""
    from app.ml.features.gst_features import gst_features
    gst = tables["gst"]
    eid = gst["entity_id"].iloc[0]
    row = tables["msme_master"].set_index("entity_id").loc[eid].to_dict()
    f = gst_features(gst[gst["entity_id"] == eid], row)
    assert f["gst_present"] == 1.0
    assert f["gst_total_turnover"] > 0
    assert 0.0 <= f["gst_filing_regularity"] <= 1.0
