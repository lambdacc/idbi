"""Regenerate the Track-04 early-warning panel CSVs.

Callable API (used by tests / the Wave-2 ML agent):
    build_panel(n_random=..., base_seed=...) -> dict[str, DataFrame]
    write_panel(tables, data_dir=...) -> None
    ensure_panel() -> None            # build only if the CSVs are missing

CLI (WP-V wires this into the Makefile `data-gen` target later):
    python -m app.tracks.t04_early_warning.data_gen.build [--n N] [--seed S] [--out DIR]

Deterministic: identical (--n, --seed) → byte-identical CSVs (thesis encoded in
data). Reuses the platform cohort (`app.data_gen.build_dataset.build_profiles`)
read-only, so entity_ids / archetypes / latents match Track 03.
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

import pandas as pd

from app.data_gen.build_dataset import build_profiles

from . import panel
from . import paths


def build_panel(n_random: int = panel.N_RANDOM,
                base_seed: int = panel.BASE_SEED) -> Dict[str, pd.DataFrame]:
    """Build all panel tables as DataFrames with the declared column order."""
    profiles = build_profiles(n_random=n_random, base_seed=base_seed)
    raw = panel.generate_tables(profiles)
    return {
        name: pd.DataFrame(rows, columns=panel.SCHEMAS[name])
        for name, rows in raw.items()
    }


def write_panel(tables: Dict[str, pd.DataFrame], data_dir: Path = paths.DATA_DIR) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_csv(data_dir / f"{name}.csv", index=False)


def ensure_panel(data_dir: Path = paths.DATA_DIR) -> None:
    """Build the panel only if any output CSV is missing (test/demo convenience)."""
    if all((data_dir / f"{name}.csv").exists() for name in panel.SCHEMAS):
        return
    write_panel(build_panel(), data_dir)


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate the Track-04 early-warning panel")
    ap.add_argument("--n", type=int, default=panel.N_RANDOM, help="randomised cohort size")
    ap.add_argument("--seed", type=int, default=panel.BASE_SEED)
    ap.add_argument("--out", type=str, default=str(paths.DATA_DIR))
    args = ap.parse_args()

    tables = build_panel(n_random=args.n, base_seed=args.seed)
    write_panel(tables, Path(args.out))

    loans = tables["loan_book"]
    labels = tables["default_labels"]
    n_loans = len(loans)
    n_def = int(labels["is_defaulter"].sum())
    n_obs = int(labels["default_observed"].sum())
    print(f"Track-04 panel written to {args.out}")
    for name in panel.SCHEMAS:
        df = tables[name]
        print(f"  {name:20s} {len(df):6d} rows  ({len(df.columns)} cols)")
    print(f"  book: {n_loans} loans | defaulters: {n_def} "
          f"({n_def / n_loans:.1%}) | observed-in-panel: {n_obs} "
          f"| live watchlist: {n_def - n_obs}")


if __name__ == "__main__":
    main()
