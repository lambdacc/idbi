"""Build the synthetic MSME cohort and write one CSV per source to app/data/.

`make data-gen` runs this. It writes:
  * msme_master.csv  — one row per entity (attributes + ground-truth labels)
  * <source>.csv     — one file per registered generator (core + enrichment)

The 6 named archetypes are always emitted first (stable entity_ids for the
demo), followed by `--n` randomised entities for the eval-harness cohort.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

import pandas as pd

from .generators.base import get_registry
from .profiles import MSMEProfile
from .scenarios import ARCHETYPE_KEYS, build_archetype, build_random

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Master columns exclude nothing — labels included for the eval harness.
_MASTER_DROP = set()


def build_profiles(n_random: int, base_seed: int = 20260701) -> List[MSMEProfile]:
    profiles = [build_archetype(k, seed=base_seed + i) for i, k in enumerate(ARCHETYPE_KEYS)]
    profiles += [build_random(seed=base_seed + 1000 + i) for i in range(n_random)]
    return profiles


def generate_all(profiles: List[MSMEProfile]) -> dict:
    """Return {source_name: DataFrame} plus 'msme_master'."""
    registry = get_registry()
    frames: dict = {name: [] for name in registry}
    for p in profiles:
        for name, gen in registry.items():
            frames[name].extend(gen.generate(p))

    out = {}
    for name, gen in registry.items():
        df = pd.DataFrame(frames[name], columns=gen.columns) if frames[name] else pd.DataFrame(columns=gen.columns)
        out[name] = df

    master = pd.DataFrame([p.as_dict() for p in profiles])
    out["msme_master"] = master
    return out


def write_csvs(tables: dict, data_dir: Path = DATA_DIR) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_csv(data_dir / f"{name}.csv", index=False)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate CreditPulse synthetic cohort")
    ap.add_argument("--n", type=int, default=400, help="number of randomised entities")
    ap.add_argument("--seed", type=int, default=20260701)
    ap.add_argument("--out", type=str, default=str(DATA_DIR))
    args = ap.parse_args()

    profiles = build_profiles(args.n, base_seed=args.seed)
    tables = generate_all(profiles)
    write_csvs(tables, Path(args.out))

    print(f"Generated {len(profiles)} entities ({len(ARCHETYPE_KEYS)} archetypes + {args.n} random)")
    for name, df in sorted(tables.items()):
        print(f"  {name:22s} {len(df):6d} rows  ({len(df.columns)} cols)")
    labels = tables["msme_master"]
    print(f"  default rate: {labels['label_default'].mean():.3f} | "
          f"fraud rate: {labels['label_fraud'].mean():.3f}")


if __name__ == "__main__":
    main()
