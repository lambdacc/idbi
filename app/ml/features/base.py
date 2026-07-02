"""Feature-engineering registry + orchestration.

Each per-source feature module registers a function via @feature_source("gst").
The function receives (entity_source_df, master_row) and returns a flat dict of
named features. `compute_entity_features` runs all of them for one entity, then
layers the composite features (composite_features.py) on top of the merged
per-source dict — the composite layer never re-reads raw source data, keeping it
testable in isolation (implementation-plan.md §5.2).

`ml/` has no Streamlit/FastAPI import — pure pandas/numpy (module-boundary rule).
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# source_name -> feature function
_FEATURE_FUNCS: "Dict[str, Callable]" = {}


def feature_source(name: str):
    def _wrap(fn: Callable):
        _FEATURE_FUNCS[name] = fn
        return fn
    return _wrap


def _ensure_modules_loaded():
    # Importing populates the registry (per-source modules + composites).
    from . import (  # noqa: F401
        gst_features, bank_features, upi_features, epfo_features,
        bureau_features, ewaybill_features, electricity_features, misc_features,
    )


def load_tables(data_dir: Path = DATA_DIR) -> Dict[str, pd.DataFrame]:
    """Load every CSV in data_dir into {stem: DataFrame}."""
    tables = {}
    for csv in sorted(Path(data_dir).glob("*.csv")):
        tables[csv.stem] = pd.read_csv(csv)
    if "msme_master" not in tables:
        raise FileNotFoundError(f"msme_master.csv not found in {data_dir} — run `make data-gen`")
    return tables


def _entity_slice(df: pd.DataFrame, entity_id: str) -> pd.DataFrame:
    if df is None or df.empty or "entity_id" not in df.columns:
        return pd.DataFrame()
    return df[df["entity_id"] == entity_id]


def compute_entity_features(entity_id: str, tables: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    """Compute the full per-source + composite feature vector for one entity."""
    _ensure_modules_loaded()
    from .composite_features import compute_composites

    master = tables["msme_master"]
    row = master[master["entity_id"] == entity_id]
    if row.empty:
        raise KeyError(f"entity_id {entity_id} not in msme_master")
    master_row = row.iloc[0].to_dict()

    feats: Dict[str, float] = {}
    for source, fn in _FEATURE_FUNCS.items():
        sub = _entity_slice(tables.get(source, pd.DataFrame()), entity_id)
        result = fn(sub, master_row) or {}
        feats.update(result)

    feats.update(compute_composites(feats, master_row))
    return feats


def build_feature_matrix(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Feature matrix (one row per entity) + ground-truth labels, indexed by entity_id."""
    master = tables["msme_master"]
    records = []
    for eid in master["entity_id"]:
        feats = compute_entity_features(eid, tables)
        feats["entity_id"] = eid
        records.append(feats)
    fm = pd.DataFrame(records).set_index("entity_id")
    labels = master.set_index("entity_id")[["label_default", "label_fraud"]]
    fm = fm.join(labels)
    return fm.fillna(0.0)


def registered_sources():
    _ensure_modules_loaded()
    return sorted(_FEATURE_FUNCS.keys())
