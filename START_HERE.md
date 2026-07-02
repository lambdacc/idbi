# Start here

A guided tour of this repository for anyone — reviewer, teammate, or coding
assistant — reading it for the first time. The [`README.md`](README.md) says
*what* CreditPulse is; this file says *where everything lives and why*.

## The 60-second version

CreditPulse scores an MSME's financial health from synthetic alternate data
(25 sources), through a deterministic feature layer, a cross-source synthesis
layer, an interpretable scorecard plus a monotonic GBM, and ships the result as
an explainable Financial Health Card in a Streamlit app. One container, one
deploy. Everything is reproducible from a clean checkout with four commands:

```bash
make install && make data-gen && make test && make demo
```

## Suggested reading order

1. [`README.md`](README.md) — what this is and how to run it.
2. [`docs/solution-design.md`](docs/solution-design.md) — the product spec: users,
   pillars, scoring philosophy, the Health Card.
3. [`docs/implementation-plan.md`](docs/implementation-plan.md) — how the spec became
   this codebase: module structure (§3), ML architecture (§5), the nine-stage
   demo animation spec (§6), deployment (§8). Code comments cite this document
   by section, so it doubles as the map.
4. [`docs/appendix-a-data-source-catalog.md`](docs/appendix-a-data-source-catalog.md) —
   the research backbone: which data sources made the cut, which were rejected
   and why, and the 13 composite indicators. If you read only one document about
   *why* this approach is different, read this one.
5. Then the code, in dependency order: `app/data_gen/` → `app/ml/` →
   `app/backend/` → `app/frontend/`.

## How the code is organized

```
app/
  data_gen/     synthetic cohort: generators/ (one per source), profiles.py
                (shared latent variables + fraud/health injection), scenarios.py
                (the six demo archetypes), distributions.py (India MSME stats)
  ml/           pure Python/pandas/sklearn — no UI imports, independently testable
    features/   per-source feature modules + composite_features.py (cross-source
                synthesis) + turnover_authenticity.py (the flagship cross-check)
    models/     scorecard.py (WOE/IV), gbm.py (monotonic LightGBM), clustering.py,
                confidence_score.py, pillars.py (deterministic dimension scoring)
    explainability/  reason codes, SHAP, stability checks
    eval/       metrics, leakage-resistant holdout, PSI — run via `make eval`
    engine.py   fits everything and scores an entity; prefit.py pickles a fitted
                engine at Docker build time so cold starts are instant
  backend/      pipeline_orchestrator.py (decomposes one scoring pass into the
                nine reveal stages), scoring_service.py, schemas/ (typed contracts;
                internal pillar names map to Health Card labels exactly once here)
  frontend/     Streamlit multipage app; renders only what backend/ hands it
  tests/        the suite `make test` runs; conftest.py builds a small in-memory
                cohort so tests don't depend on generated CSVs
  config/       scoring_config.yaml (weights, grade bands), feature_config.yaml
  data/         generated CSVs — never committed; rebuild with `make data-gen`
```

Three module-boundary rules keep this navigable, and are worth preserving in any
change:

1. **`frontend/` computes nothing** — it renders `Stage` and `HealthCard` objects
   produced by `backend/`.
2. **`backend/` models nothing** — it orchestrates and types what `ml/` produces.
3. **`ml/` imports no framework** — pure pandas/sklearn/LightGBM, so the entire
   scoring engine is testable and reusable without the UI.

A fourth convention: the label mapping between internal pillar names
(cash-flow health, revenue quality, …) and Health Card dimension names
(Repayment Capacity, Growth Trajectory, …) is applied in exactly one place —
`app/backend/schemas/models.py`. Don't duplicate it.

## Common tasks

| Task | How |
|---|---|
| Run the app locally | `make demo` (→ http://localhost:8080) |
| Regenerate the synthetic cohort | `make data-gen` (`N=1000 make data-gen` for a bigger one) |
| Run the tests | `make test` |
| Check model quality | `make eval` — prints AUC/Gini/KS/PSI on the holdout, with the synthetic-data caveat |
| Sanity-check the six archetypes | `make train` — prints score/grade/band per archetype and a few narrative checks |
| Skip model-fit on startup | `make prefit` — pickles a fitted engine next to the data (the Docker build does this automatically) |
| Build/run the container | `make docker-build && make docker-run` |
| Deploy | follow [`docs/deployment-runbook.md`](docs/deployment-runbook.md) |

## Things to know before changing code

- **Determinism matters.** Generators, splits, and models are seeded; re-runs must
  produce identical scores (`app/tests/test_determinism.py` enforces this). Don't
  introduce unseeded randomness into the scoring path.
- **Monotonicity is enforced.** The GBM carries per-feature monotonic constraints
  and tests assert a score never improves as a risk factor worsens. New features
  need a documented direction.
- **The holdout is leakage-resistant by design.** The six demo archetypes are
  pinned to the training side (`app/ml/eval/holdout.py`) so demo entities never
  inflate reported test metrics. Keep it that way.
- **Every composite indicator carries a rationale.** `composite_features.py`
  returns manipulation-resistance strings that surface in the UI — a new
  composite isn't done until it can explain why it's harder to fake than its
  inputs.
- **Dependencies are pinned** in `requirements.txt`; add new ones pinned, and
  only if genuinely needed.
- **Synthetic data is never committed.** `app/data/` is gitignored and rebuilt
  from code; the ground-truth labels it contains exist for evaluation and the
  demo's "reveal" moment, not for training-time peeking (the feature layer never
  reads label columns).
