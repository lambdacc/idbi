"""One schema-validation test per registered source (Sprint-1 acceptance a).

Parametrized over the generator registry, so every core + enrichment source is
covered automatically as generators are added.
"""
import pandas as pd
import pytest

from app.data_gen.generators.base import get_registry

REGISTRY = get_registry()


def test_registry_has_all_sources():
    # 8 core + 17 enrichment (POS/QR folded into UPI) = 25 generators.
    assert len(REGISTRY) == 25
    core = [g for g in REGISTRY.values() if g.tier == "core"]
    assert len(core) == 8


@pytest.mark.parametrize("name", sorted(REGISTRY.keys()))
def test_generator_output_matches_schema(name, profiles):
    gen = REGISTRY[name]
    produced_any = False
    for p in profiles:
        rows = gen.generate(p)
        for r in rows:
            produced_any = True
            # No extra keys, entity_id always present.
            assert set(r.keys()) <= set(gen.columns), f"{name}: unexpected keys {set(r.keys()) - set(gen.columns)}"
            assert "entity_id" in r
    assert produced_any, f"{name}: generated zero rows across the whole cohort"


@pytest.mark.parametrize("name", sorted(REGISTRY.keys()))
def test_csv_columns_exact(name, tables):
    df = tables[name]
    gen = REGISTRY[name]
    assert list(df.columns) == gen.columns, f"{name}: CSV columns != declared schema"


def test_master_has_labels(tables):
    m = tables["msme_master"]
    assert {"label_default", "label_fraud", "entity_id"} <= set(m.columns)
    assert m["label_default"].isin([0, 1]).all()
    assert m["entity_id"].is_unique
