"""Pre-fit the platform engines and pickle them next to their data.

Run at Docker build time (after data-gen) so a Cloud Run cold start serves the
first request without paying the model-fit cost — each `get_engine()` loads its
pickle whenever it is newer than the generated data, else refits.
Run: `python -m app.ml.prefit` or `make prefit`.

Warms the core scoring engine (Track 03) plus every INSTALLED track engine.
Track engines are reached only through a folder-existence guard + lazy import
(this file is a sanctioned guarded-discovery point in the isolation linter), so
`rm -rf app/tracks/<folder>` simply drops that engine from the warm loop.
"""
from __future__ import annotations

import importlib
from pathlib import Path

from .engine import ENGINE_PICKLE, ScoringEngine, _load_prefit

_TRACKS_DIR = Path(__file__).resolve().parents[1] / "tracks"

# (folder, engine-module) pairs. Each module exposes a skip-if-fresh `prefit()`.
# Guarded by folder existence so a deleted track is silently skipped.
_TRACK_ENGINES = [
    ("t04_early_warning", "app.tracks.t04_early_warning.ml.model"),
    ("t05_fraud_intelligence", "app.tracks.t05_fraud_intelligence.ml.model"),
]


def _warm_core() -> None:
    # Cheap to re-run: skip the ~7s fit when a fresh, current-version pickle
    # already sits next to the cohort (same freshness + version guard the app
    # uses at startup).
    if _load_prefit() is not None:
        print(f"core engine.pkl already fresh: {ENGINE_PICKLE} (skipping fit)")
        return
    engine = ScoringEngine().fit().save()
    n = len(engine.feature_matrix)
    print(f"Pre-fit core engine saved: {ENGINE_PICKLE} "
          f"({n} entities, {len(engine.feature_cols)} features)")


def _warm_tracks() -> None:
    for folder, module_name in _TRACK_ENGINES:
        if not (_TRACKS_DIR / folder).exists():
            continue
        try:
            module = importlib.import_module(module_name)
            module.prefit()  # skip-if-fresh, prints its own status
        except Exception as exc:  # a track's engine failing to warm must not
            # abort the others or the build — report and continue.
            print(f"track {folder}: prefit skipped ({type(exc).__name__}: {exc})")


def main() -> None:
    _warm_core()
    _warm_tracks()


if __name__ == "__main__":
    main()
