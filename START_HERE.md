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

## Now a platform: three tracks, one codebase

CreditPulse started as a single answer to PS3 (Financial Health). It is now a
multi-track **platform** answering three IDBI Innovate 2026 problem statements
from one checkout, one container, one deploy:

- **PS3 · Financial Health** — underwrite the credit-invisible MSME from its
  digital exhaust (the original app; its engine is the shared `app/ml/` core).
- **PS4 · Early Warning** — watch the book: alt-data stress signals a median
  **8 months earlier** than a repayment-only baseline (median lead-time 11.5
  vs 2.0 months; capture@top-decile 0.926 vs 0.519).
- **PS5 · Fraud Intelligence** — protect the rails: explainable mule-account
  detection that recovered **6/6 fraud rings** (recall@alert 1.0) with **0/10
  hard-negative false positives** — the gig-worker who looks suspicious is
  explainably cleared.

All three metrics are on synthetic data, and stay that way — see the honesty
note at the foot of this file.

The three tracks are wired together by a small **router**, not a monolith:

```
app/frontend/
  main.py               the st.navigation router entrypoint (NOT app.py — a
                        file named app.py here shadows the `app` package and
                        breaks `import app.backend …`; see the docstring)
  tracks.py             the track REGISTRY — single source of truth for grouped
                        nav; auto-detects installed tracks by folder existence,
                        so `rm -rf app/tracks/<folder>` silently drops a track's
                        group, its Overview card and its deep links, no edits
  pages/overview.py     the common landing page (one card per installed track)
  pages/architecture.py the cross-track architecture reference page
```

`main.py` calls `tracks.build_navigation()` each rerun to assemble
`{group_label: [st.Page, …]}` for installed tracks only, then `nav.run()`.
Each track's own pages live under `app/tracks/<track>/pages/` (see the repo map).

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
6. Then tour the platform track by track, following the nav itself:
   **Overview** (`app/frontend/pages/overview.py`) → **Track 03**
   (`app/tracks/t03_financial_health/`, whose engine is the `app/ml/` core you
   just read) → **Track 04** (`app/tracks/t04_early_warning/`) → **Track 05**
   (`app/tracks/t05_fraud_intelligence/`). Each track folder is self-contained
   (its own data, ML and pages), so you can read one end-to-end before the next.

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
                engine at Docker build time so cold starts are instant — and now
                also warms every INSTALLED track engine (guarded by folder
                existence + lazy import, so a deleted track is silently skipped)
  backend/      pipeline_orchestrator.py (decomposes one scoring pass into the
                nine reveal stages), scoring_service.py, schemas/ (typed contracts;
                internal pillar names map to Health Card labels exactly once here)
  frontend/     the st.navigation router (main.py) + track registry (tracks.py)
                + common pages/ (overview, architecture); renders only what
                backend/ or a track hands it — see "Now a platform" above
  tracks/       one self-contained package per problem statement (below); the
                registry auto-detects them by folder existence
  tests/        the suite `make test` runs; conftest.py builds a small in-memory
                cohort so tests don't depend on generated CSVs. test_isolation.py
                enforces the boundary: no cross-track imports, and core never
                hard-imports a track (only the guarded discovery points may)
  config/       scoring_config.yaml (weights, grade bands), feature_config.yaml
  data/         generated CSVs — never committed; rebuild with `make data-gen`
```

The tracks themselves, under `app/tracks/`:

```
tracks/
  t03_financial_health/  NOT self-contained — it IS the core. Only pages/ live
    pages/               here (run_assessment, dashboard, pipeline, health_card,
                         explainability); the engine is the shared app/ml/ above
  t04_early_warning/     self-contained: its own data + ML + pages
    data_gen/            build.py, panel.py, paths.py — the 24-month alt-data panel
    data/                generated CSVs + ews_engine.pkl (gitignored, rebuilt)
    ml/                  features.py, model.py (EWSEngine), ews_metrics.py
    pages/               portfolio_overview.py, watchlist.py
    service.py, charts.py, ui_state.py, glossary.py   track helpers
    tests/               ews data / engine / orchestrator / pages
  t05_fraud_intelligence/ self-contained: its own data + ML + pages
    data_gen/            build.py, fraud_profiles.py, typologies.py, legit.py
    data/                accounts/transactions CSVs + fraud_engine.pkl (rebuilt);
                         fraud_ground_truth.csv is EVAL-ONLY, never read at score time
    ml/                  features.py, typologies.py, model.py (FraudEngine),
                         eval/fraud_metrics.py
    case_orchestrator.py the agentic, citation-gated case file (CaseFile / Ground)
    pages/               fraud_desk.py, case_investigation.py
    charts.py, session.py, glossary.py                track helpers
    tests/               case orchestrator / pages / fraud data / fraud engine
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
