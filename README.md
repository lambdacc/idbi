# CreditPulse — MSME Credit Intelligence Platform

An AI/ML platform that reads an Indian MSME's **alternate-data footprint** — GST
returns, bank/UPI cash flow, EPFO payroll, e-way bills, electricity, licences,
procurement, FASTag and more — and turns it into three things a bank actually
needs: an underwriting decision on a business with no audited financials, an
early warning when a loan already on the book starts to sour, and a fraud call
on the accounts moving the money.

Built for **IDBI Innovate 2026**, answering **three problem statements from one
codebase and one deployment**.

**Live demo:** *deploy link goes here* (see [`docs/deployment-runbook.md`](docs/deployment-runbook.md))

---

## Three problem statements, one codebase

IDBI Innovate 2026 permits one team to submit against multiple problem
statements. CreditPulse is a **single deployable app** with a common Overview
landing page and three self-contained tracks in the sidebar. Each track is an
isolated folder under `app/tracks/`, with its own deep link — so the *same*
repository URL and the *same* deploy URL back all three submission entries, and
a reviewer arriving for any one PS lands directly on that track's page.

| Problem statement | Track | Codebase | Deep link | The one proof |
|---|---|---|---|---|
| **Problem Statement 3 · Financial Health Score** | Financial Health | shared core (`app/data_gen/`, `app/ml/`, `app/backend/`) + [`app/tracks/t03_financial_health/`](app/tracks/t03_financial_health/) | `/track03` | Explainable health card + turnover-authenticity cross-check |
| **Problem Statement 4 · Default Prediction Model** | Early Warning | [`app/tracks/t04_early_warning/`](app/tracks/t04_early_warning/) (self-contained) | `/track04` | Flags stress a **median 8 months** before a repayment-only baseline |
| **Problem Statement 5 · Open Innovation** | Fraud Intelligence | [`app/tracks/t05_fraud_intelligence/`](app/tracks/t05_fraud_intelligence/) (self-contained) | `/track05` | **6/6 mule rings** recovered; **0** false positives on hard-negative gig workers |

> **Reviewers:** open the deep link for your problem statement to land directly
> on that track. **Problem Statement 3** is the platform foundation — its scoring engine *is* the
> shared `app/ml/` core, with only its pages under `t03_financial_health/`.
> **Problem Statement 4 and Problem Statement 5** are self-contained satellite tracks that build on that
> foundation: each carries its own data-gen, ML engine, orchestration and pages,
> and `rm -rf app/tracks/t04_early_warning` (or `t05_…`) leaves the rest of the
> platform fully working — enforced by `app/tests/test_isolation.py`.

The three tracks share one synthetic-data foundation, one ML layer, one backend
contract and one Streamlit shell; no track imports another.

## The idea in one paragraph

Most credit-invisible MSMEs are not data-invisible. Every operating business
leaves an electronic trail across independently-governed systems — a tax
authority, a regulated bank, a state electricity utility, a labour-welfare body,
a toll network, a court registry. CreditPulse fuses these sources into signals no
single document can fake, and applies them across the full credit lifecycle:
**underwrite** the new-to-bank MSME (Problem Statement 3), **monitor** the loan already on the
book for early deterioration (Problem Statement 4), and **protect** the payment rails from mule
accounts and fraud rings (Problem Statement 5).

All data in this repository is **synthetic** (generated, clearly labelled, and
calibrated to public India MSME statistics). Real-default backtesting and
recalibration is the productionization step, not a claim made here. Every metric
quoted below is measured on that synthetic holdout by the in-repo eval harnesses.

## Quick start

Requires Python 3.12+.

```bash
make install      # create .venv and install pinned dependencies
make data-gen     # generate the synthetic cohort for the platform + all tracks
make test         # run the full suite (platform + every installed track)
make demo         # launch the app → http://localhost:8080 (Overview landing page)
```

Or as a container (also how it deploys to Cloud Run):

```bash
make docker-build && make docker-run
```

In the app you land on **Overview** — one card per installed track. From there:

- **Problem Statement 3 · Financial Health** — pick a business archetype, **Run Assessment**,
  and watch the nine-stage pipeline build a Health Card with a lending
  recommendation and plain-language reason codes.
- **Problem Statement 4 · Early Warning** — a portfolio deterioration radar and a watchlist
  showing which live borrowers are rolling over, and how many months of lead time
  the alt-data signal buys over a repayment-only view.
- **Problem Statement 5 · Fraud Intelligence** — a fraud desk that scores accounts, expands
  a suspicious account into its ring across the transaction graph, and builds a
  **citation-gated** case file where every claim carries the transaction IDs
  behind it.

A guided five-minute walkthrough covering all three is in
[`docs/demo-script.md`](docs/demo-script.md).

## What's under the hood

**Shared foundation** (used by every track; core = Problem Statement 3 lives here too):

| Layer | What it does |
|---|---|
| `app/data_gen/` | Synthetic-data generators — one per data source, driven by shared latent variables (true scale, health, honesty) so cross-source signals are internally consistent, with ground-truth labels for evaluation |
| `app/ml/` | Deterministic per-source feature engineering, a cross-source synthesis layer of composite indicators, the interpretable scorecard + monotonic-constrained lift model, explainability, and the eval harness (`make eval`) |
| `app/backend/` | Pipeline orchestration and the typed Health Card contract |
| `app/frontend/` | Streamlit **router** (`main.py`) + Overview + the track registry that builds the grouped navigation and auto-detects installed tracks by folder |

**Per track** (t04/t05 self-contain their data-gen, ML engine, orchestration and
pages; t03 is the shared core plus its pages):

| Track | Under the hood | Headline (synthetic holdout) |
|---|---|---|
| `t03_financial_health` (+ shared `app/ml/`) | WOE/IV logistic scorecard + monotonic LightGBM lift + K-Means peer segmentation; 13 composite cross-source indicators; native reason codes + SHAP; the **Turnover-Authenticity** cross-check | Explainable 1–10 grade with an indicative limit; every score carries its reasons |
| `t04_early_warning` | 24-month alt-data panel; entity-level split with future-window leakage guards; monotonic LightGBM + isotonic calibration; lead-time vs a repayment-only baseline | Median lead-time **11.5 mo vs 2.0 mo** baseline (**8-month gap**); capture@decile **0.926 vs 0.519** |
| `t05_fraud_intelligence` | Typology detectors + anomaly scoring; ring expansion over the transaction graph; a 5-stage **agentic, citation-gated** case orchestrator (an uncited claim raises rather than renders) | **6/6 rings** recovered; recall@alert **1.0**; **0/10** hard-negative false positives |

Design stance throughout: **deterministic-first, ML-second** — every score
carries its reasons, every feature is auditable, the model never improves a score
as a risk factor worsens (monotonicity enforced and tested), and no fraud finding
is shown without the transactions that justify it.

## Documentation

Start with [`START_HERE.md`](START_HERE.md) for a guided tour of the repo, then:

- [`docs/solution-design.md`](docs/solution-design.md) — the product and scoring specification (all three tracks)
- [`docs/implementation-plan.md`](docs/implementation-plan.md) — architecture, ML design, sprint plan
- [`docs/demo-script.md`](docs/demo-script.md) — the five-minute platform walkthrough
- [`docs/appendix-a-data-source-catalog.md`](docs/appendix-a-data-source-catalog.md) — 34 data sources evaluated on a fixed rubric, with rejections reasoned and 13 composite indicators
- [`docs/appendix-b-synthetic-data-plan.md`](docs/appendix-b-synthetic-data-plan.md) — the India MSME distribution profile (every figure tagged sourced/assumed) and per-source generator specs
- [`docs/cag-gst-feature-analysis.md`](docs/cag-gst-feature-analysis.md) — borrower-health signals mined from CAG GST audit reports
- [`docs/business-impact-model.md`](docs/business-impact-model.md) — the quantified business case
- [`docs/deployment-runbook.md`](docs/deployment-runbook.md) — Cloud Run deployment, step by step

## Tests & CI

```bash
make test    # full unit + integration suite (platform + every installed track)
make eval    # evaluation-harness scorecard on the synthetic holdout
make train   # fit models and print the six-archetype demo scorecard
```

CI (GitHub Actions) regenerates the cohort, runs the full suite, runs the eval
harness, and builds the Docker image on every push.

## Team

Built by **Lambdac Computing** for IDBI Innovate 2026.
