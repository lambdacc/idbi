"""Determinism: identical seed => identical data + features (ReconWise discipline)."""
import pandas as pd

from app.data_gen.build_dataset import build_profiles, generate_all
from app.ml.features.base import build_feature_matrix


def test_profiles_reproducible():
    p1 = build_profiles(n_random=20, base_seed=123)
    p2 = build_profiles(n_random=20, base_seed=123)
    assert [x.as_dict() for x in p1] == [x.as_dict() for x in p2]


def test_generated_tables_reproducible():
    t1 = generate_all(build_profiles(10, base_seed=99))
    t2 = generate_all(build_profiles(10, base_seed=99))
    for name in t1:
        pd.testing.assert_frame_equal(t1[name], t2[name])


def test_feature_matrix_reproducible():
    fm1 = build_feature_matrix(generate_all(build_profiles(10, base_seed=55)))
    fm2 = build_feature_matrix(generate_all(build_profiles(10, base_seed=55)))
    pd.testing.assert_frame_equal(fm1, fm2)
