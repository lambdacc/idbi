"""Generator registry + base contract.

Each data source registers a Generator: a name, its output column schema, and a
`generate(profile)` that returns a list of row-dicts for one MSME. The single
registry is consumed by:
  * data_gen/build_dataset.py  -> writes one CSV per source
  * tests/                      -> one schema-validation test per source (auto)
  * ml/features/               -> per-source feature modules read the same rows
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from ..profiles import MSMEProfile

# name -> Generator
_REGISTRY: "Dict[str, Generator]" = {}


@dataclass
class Generator:
    name: str
    columns: List[str]
    tier: str                       # "core" | "enrichment"
    fn: Callable[[MSMEProfile], List[dict]]

    def generate(self, profile: MSMEProfile) -> List[dict]:
        rows = self.fn(profile)
        # Every generator must stamp entity_id; enforce schema keys.
        for r in rows:
            r.setdefault("entity_id", profile.entity_id)
        return rows


def register(name: str, columns: List[str], tier: str = "enrichment"):
    """Decorator registering a generator function under `name`."""
    def _wrap(fn: Callable[[MSMEProfile], List[dict]]):
        if name in _REGISTRY:
            raise ValueError(f"Duplicate generator registered: {name}")
        _REGISTRY[name] = Generator(name=name, columns=list(columns), tier=tier, fn=fn)
        return fn
    return _wrap


def get_registry() -> Dict[str, Generator]:
    # Importing this module's siblings populates the registry.
    from . import core_sources          # noqa: F401
    from . import enrichment_sources    # noqa: F401
    return dict(_REGISTRY)


def source_names() -> List[str]:
    return sorted(get_registry().keys())
