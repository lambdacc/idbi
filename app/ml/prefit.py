"""Pre-fit the scoring engine and pickle it next to the cohort.

Run at Docker build time (after data-gen) so a Cloud Run cold start serves the
first request without paying the model-fit cost — `get_engine()` loads this
pickle whenever it is newer than the generated cohort, else refits.
Run: `python -m app.ml.prefit` or `make prefit`.
"""
from __future__ import annotations

from .engine import ENGINE_PICKLE, ScoringEngine, _load_prefit


def main() -> None:
    # Cheap to re-run: skip the ~7s fit when a fresh, current-version pickle
    # already sits next to the cohort (same freshness + version guard the app
    # uses at startup).
    if _load_prefit() is not None:
        print(f"engine.pkl already fresh: {ENGINE_PICKLE} (skipping fit)")
        return
    engine = ScoringEngine().fit().save()
    n = len(engine.feature_matrix)
    print(f"Pre-fit engine saved: {ENGINE_PICKLE} "
          f"({n} entities, {len(engine.feature_cols)} features)")


if __name__ == "__main__":
    main()
