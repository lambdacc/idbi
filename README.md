# CreditPulse — MSME Financial Health Card

An AI/ML platform that assesses the financial health of Indian MSMEs from their
**alternate-data footprint** — GST returns, bank/UPI cash flow, EPFO payroll,
e-way bills, electricity, licences, procurement records and more — so that a bank
can make an evidence-based lending decision on a business that has **no audited
financials and no credit history**.

Built for **IDBI Innovate 2026, Problem Statement 3 (Financial Health Score)**.

**Live demo:** *deploy link goes here* (see [`docs/deployment-runbook.md`](docs/deployment-runbook.md))

---

## The idea in one paragraph

Most credit-invisible MSMEs are not data-invisible. Every operating business
leaves an electronic trail across independently-governed systems — a tax
authority, a regulated bank, a state electricity utility, a labour-welfare body,
a toll network, a court registry. CreditPulse fuses 25 such sources into a
multidimensional **Financial Health Card**: five dimension scores (Repayment
Capacity, Growth Trajectory, Creditworthiness, Risk Profile, Stability &
Vintage), a composite score and 1-10 grade, a lending recommendation with an
indicative limit, plain-language reason codes for every decision — and a
**Turnover-Authenticity Score** that cross-checks declared GST turnover against
settled bank inflows and physical goods movement, because a signal spread across
three independent systems is far harder to fake than any single document.

All data in this repository is **synthetic** (generated, clearly labelled, and
calibrated to public India MSME statistics). Real-default backtesting and
recalibration is the productionization step, not a claim made here.

## Quick start

Requires Python 3.12+.

```bash
make install      # create .venv and install pinned dependencies
make data-gen     # generate the synthetic MSME cohort (25 sources)
make test         # run the test suite
make demo         # launch the app → http://localhost:8080
```

Or as a container (also how it deploys to Cloud Run):

```bash
make docker-build && make docker-run
```

In the app: pick one of six business archetypes (or a random MSME), click
**Run Assessment**, and watch the nine-stage pipeline execute — data ingestion
across all 25 sources, integration, feature engineering, cross-source synthesis,
peer segmentation, scoring, explainability, and the final Health Card.
A guided walkthrough with expected output at every step is in
[`docs/demo-script.md`](docs/demo-script.md).

## What's under the hood

| Layer | What it does |
|---|---|
| `app/data_gen/` | Synthetic-data generators — one per data source, driven by shared latent variables (true scale, health, honesty) so cross-source signals are internally consistent, with ground-truth labels for evaluation |
| `app/ml/features/` | Deterministic per-source feature engineering + a **cross-source synthesis layer** producing 13 composite indicators (energy intensity, premises authenticity, supply-chain consistency, …) |
| `app/ml/models/` | WOE/IV logistic scorecard (interpretable backbone), monotonic-constrained LightGBM (lift), K-Means peer segmentation (descriptive only), and a data-completeness confidence score |
| `app/ml/explainability/` | Native reason codes, SHAP for the GBM path, and reason-code stability checks |
| `app/ml/eval/` | Evaluation harness: AUC/Gini/KS, calibration, PSI stability, leakage-resistant holdout (`make eval`) |
| `app/backend/` | Pipeline orchestration and the typed Health Card contract |
| `app/frontend/` | Streamlit dashboard — the staged-reveal pipeline, Health Card, and explainability views |

Design stance throughout: **deterministic-first, ML-second** — every score
carries its reasons, every feature is auditable, and the model never improves a
score as a risk factor worsens (monotonicity is enforced and tested).

## Documentation

Start with [`START_HERE.md`](START_HERE.md) for a guided tour of the repo, then:

- [`docs/solution-design.md`](docs/solution-design.md) — the product and scoring specification
- [`docs/implementation-plan.md`](docs/implementation-plan.md) — architecture, ML design, sprint plan
- [`docs/appendix-a-data-source-catalog.md`](docs/appendix-a-data-source-catalog.md) — 34 data sources evaluated on a fixed rubric, with rejections reasoned and 13 composite indicators
- [`docs/appendix-b-synthetic-data-plan.md`](docs/appendix-b-synthetic-data-plan.md) — the India MSME distribution profile (every figure tagged sourced/assumed) and per-source generator specs
- [`docs/cag-gst-feature-analysis.md`](docs/cag-gst-feature-analysis.md) — borrower-health signals mined from CAG GST audit reports
- [`docs/business-impact-model.md`](docs/business-impact-model.md) — the quantified business case
- [`docs/deployment-runbook.md`](docs/deployment-runbook.md) — Cloud Run deployment, step by step

## Tests & CI

```bash
make test    # unit + integration suite
make eval    # evaluation-harness scorecard on the synthetic holdout
make train   # fit models and print the six-archetype demo scorecard
```

CI (GitHub Actions) regenerates the cohort, runs the full suite, runs the eval
harness, and builds the Docker image on every push.

## Team

Built by **Lambdac** for IDBI Innovate 2026.
