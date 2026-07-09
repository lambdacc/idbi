# CreditPulse — MSME Credit Intelligence Platform

An AI/ML platform that reads an Indian MSME's **alternate-data footprint** — GST
returns, bank/UPI cash flow, EPFO payroll, e-way bills, electricity, licences,
procurement, FASTag and more — and turns it into three things a bank actually
needs: an underwriting decision on a business with no audited financials, an
early warning when a loan already on the book starts to sour, and a fraud call
on the accounts moving the money.

Built for **IDBI Innovate 2026**, answering **three problem statements from one
codebase and one deployment**.

## Live demo

One deployment serves all three entries — open the deep link for your problem statement:

| Problem statement | Opens on | Deep link |
|---|---|---|
| Overview (all three) | platform landing | [`/`](https://creditpulse-66armtf3tq-el.a.run.app/) |
| **PS3 · Financial Health Score** | Financial Health | [`/track03`](https://creditpulse-66armtf3tq-el.a.run.app/track03) |
| **PS4 · Default Prediction Model** | Early Warning | [`/track04`](https://creditpulse-66armtf3tq-el.a.run.app/track04) |
| **PS5 · Open Innovation** | Fraud Intelligence | [`/track05`](https://creditpulse-66armtf3tq-el.a.run.app/track05) |

> All data in this demo is **synthetic** — generated, clearly labelled on screen,
> and calibrated to public India MSME statistics. Real-default backtesting and
> recalibration is the pilot step, not a claim made here. Every metric below is
> measured on that synthetic holdout by the in-repo eval harnesses.

---

## Three problem statements, one codebase

IDBI Innovate 2026 permits one team to submit against multiple problem
statements. CreditPulse is a **single deployable app** with a common Overview
landing page and three self-contained tracks. Each track is an isolated folder
under `app/tracks/`, with its own deep link — so the *same* repository and the
*same* deploy URL back all three submission entries, and a reviewer arriving for
any one problem statement lands directly on that track's page.

| Problem statement | Track | Codebase | Deep link | The one proof |
|---|---|---|---|---|
| **PS3 · Financial Health Score** | Financial Health | shared core (`app/data_gen/`, `app/ml/`, `app/backend/`) + [`app/tracks/t03_financial_health/`](app/tracks/t03_financial_health/) | `/track03` | Explainable health card + turnover-authenticity cross-check |
| **PS4 · Default Prediction Model** | Early Warning | [`app/tracks/t04_early_warning/`](app/tracks/t04_early_warning/) (self-contained) | `/track04` | Flags stress a **median 8 months** before a repayment-only baseline |
| **PS5 · Open Innovation** | Fraud Intelligence | [`app/tracks/t05_fraud_intelligence/`](app/tracks/t05_fraud_intelligence/) (self-contained) | `/track05` | **6/6 mule rings** recovered; **0** false positives on hard-negative gig workers |

> **Reviewers:** open the deep link for your problem statement to land directly
> on that track. **PS3** is the platform foundation — its scoring engine *is* the
> shared `app/ml/` core, with only its pages under `t03_financial_health/`.
> **PS4 and PS5** are self-contained satellite tracks that build on that
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
**underwrite** the new-to-bank MSME (PS3), **monitor** the loan already on the
book for early deterioration (PS4), and **protect** the payment rails from mule
accounts and fraud rings (PS5).

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

- **PS3 · Financial Health** — pick a business archetype, **Run Assessment**, and
  watch the nine-stage pipeline build a Health Card with a lending recommendation
  and plain-language reason codes.
- **PS4 · Early Warning** — a portfolio deterioration radar and a watchlist
  showing which live borrowers are rolling over, and how many months of lead time
  the alt-data signal buys over a repayment-only view.
- **PS5 · Fraud Intelligence** — a fraud desk that scores accounts, expands a
  suspicious account into its ring across the transaction graph, and builds a
  **citation-gated** case file where every claim carries the transaction IDs
  behind it.

## What's under the hood

**Shared foundation** (used by every track; core = PS3 lives here too):

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

Design stance throughout: **rules first, machine learning second** — every score
carries its reasons, every feature is auditable, the model never improves a score
as a risk factor worsens (monotonicity enforced and tested), and no fraud finding
is shown without the transactions that justify it.

## Submission decks

One deck per problem statement, under [`docs/deck/`](docs/deck/):

- [PS3 — Financial Health Score](docs/deck/CreditPulse-PS3-Financial-Health-Score.pptx)
- [PS4 — Default Prediction Model (Early Warning)](docs/deck/CreditPulse-PS4-Default-Prediction-Early-Warning.pptx)
- [PS5 — Open Innovation (Fraud Intelligence)](docs/deck/CreditPulse-PS5-Open-Innovation-Fraud-Intelligence.pptx)

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
