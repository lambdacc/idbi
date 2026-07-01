"""Shared pytest fixtures — a small in-memory synthetic cohort."""
import pytest

from app.data_gen.build_dataset import build_profiles, generate_all
from app.ml.features.base import build_feature_matrix


@pytest.fixture(scope="session")
def profiles():
    return build_profiles(n_random=60, base_seed=20260701)


@pytest.fixture(scope="session")
def tables(profiles):
    return generate_all(profiles)


@pytest.fixture(scope="session")
def feature_matrix(tables):
    return build_feature_matrix(tables)
