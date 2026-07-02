# Solution Design — CreditPulse (IDBI PS3: Financial Health Score)

**Status:** Product & scoring specification · **Date:** 28 Jun 2026 · **Owner:** Lambdac
**Target:** IDBI Innovate 2026, **PS3 — Financial Health Score** (MSME Financial Health Card)
**Companions:** [`implementation-plan.md`](implementation-plan.md) (the build plan elaborating this spec), [`business-impact-model.md`](business-impact-model.md), [`cag-gst-feature-analysis.md`](cag-gst-feature-analysis.md)

---

## 1. Objective (locked to the official PS3)

Build an **AI/ML MSME Financial Health Card** that aggregates alternate data (GST, UPI/bank, AA, EPFO), computes a **multidimensional financial-health score**, **visualizes strengths and risks**, **integrates with ULI/OCEN/AA**, enables **near-real-time** assessment, and **expands onboarding of credit-invisible NTC/NTB MSMEs while improving portfolio quality.**

**Design stance (inherited from Lambdac's ReconWise platform):** *deterministic-first, AI-second; the model issues the decision and the reasons together; human-in-the-loop; explainable and auditable by construction* — built for what a regulated bank can actually deploy.

**One-line pitch:** *CreditPulse turns the alternate-data exhaust of a credit-invisible MSME — GST returns, bank/UPI cash-flow, EPFO, bureau — into a transparent, multidimensional Financial Health Card in seconds: a score, the reasons behind it, the right product and indicative limit, and an AA/ULI-ready API the bank can deploy.*

## 2. Users & primary flow

Primary user: an **IDBI credit officer / RM** assessing an MSME that lacks traditional financials. Secondary: a **risk/portfolio head** monitoring inflow quality.

Happy path: select/enter an MSME (or receive an AA consent-fulfilled data bundle) → CreditPulse pulls/loads the alt-data → computes pillar scores + composite health score → renders the **Health Card** (score, strengths, risks, reasons, recommended product, indicative limit, key flags) → officer reviews, accepts/overrides with audit trail → decision + reasons exportable; score available via API for STP.

## 3. Data sources & ingestion (C1)

| Source | Signals it carries | Stage-1 (own synthetic) | Stage-2 (IDBI mock) | Production |
|---|---|---|---|---|
| **GST** (GSTR-1, GSTR-3B) | turnover level/trend, filing regularity, customer concentration, seasonality | synth generator | mock or GSTN-via-AA | GSTN-as-FIP via AA (last ~18 mo) |
| **Bank / UPI (AA)** | cash-flow stability, avg balance, inflow channels, bounce behaviour | synth statements | AA-shaped mock | AA consent flow |
| **EPFO** | workforce size & PF-contribution stability (going-concern proxy) | synth (mock) | mock | *not yet on AA rails — mock/alt now, AA-ready later* |
| **Bureau (CIBIL/CRIF MSME)** | existing obligations, delinquency, vintage | synth | mock | bureau API |

**Canonical schema:** all sources normalized to a single `Entity` + per-source records (mirrors ReconWise's canonical-Invoice pattern). One ingestion contract → many adapters.
**Integration adapter (C6):** a clean **AA/ULI/OCEN adapter** modelled on **ReBIT XML/XSD** (NBFC-AA API spec) + the signed **consent-artefact** model, and ULI's API shape. Stage-1 ships a faithful *mock* of this adapter so the real sandbox plugs in at stage-2 without rework. *(Note the consent reality: AA requires borrower consent; "low/no-consent" identification leans on GST/public signals first, AA enrichment on consent.)*

## 4. Feature engineering (C2 — the domain moat)

Multidimensional by design — five health **pillars**, each a small, explainable feature group grounded in published cash-flow-underwriting research:

1. **Cash-flow health** — avg monthly balance, low-balance/overdraft frequency, balance volatility, net-flow trend, 3-month declining-balance-with-stable-inflow stress flag.
2. **Revenue quality & GST discipline** — GSTR-3B turnover level & YoY trend, filing regularity/timeliness, customer concentration, seasonality-adjusted growth.
3. **Consistency & integrity** — **GST-vs-bank turnover reconciliation gap** (our signature cross-check, straight from ReconWise DNA), circular-flow / anomaly flags.
4. **Obligations & leverage** — DSCR (target ≥1.25), FOIR (≤~55%), bounce/NACH behaviour, bureau delinquency.
5. **Stability & vintage** — business age, banking-relationship length, **EPFO workforce stability**.

Each feature is defined deterministically in code (auditable), with a documented rationale for why it earns its place — kept only if it proves out in the evaluation harness.

**Feature intelligence from CAG GST audits:** see [`cag-gst-feature-analysis.md`](cag-gst-feature-analysis.md) for a vetted backlog mined from CAG audit reports — especially **GSTN-stable ratio features** (ITC/tax-paid, IGST/CGST+SGST, exempted/taxable, credit-notes/turnover), a **risk-prone HSN/SAC sector overlay**, growth flags (composition-threshold crossing), and a proposed **Turnover-Authenticity sub-module** (GST↔bank, GSTR-1↔3B, 3B↔e-way-bill, 3B↔TDS/TCS). That doc also flags which historical indicators are now **obsolete** because GSTN auto-enforces them (e.g., 2A-vs-3B ITC, late-ITC §16(5)) — we deliberately exclude those.

## 5. Scoring model & multidimensional score (C3)

- **Pillar scores** (0-100 each) → a **composite Financial Health Score**, output on a bank-familiar convention: a **1-10 health grade (CMR-style, 1 = healthiest)** *and* an optional 300-900 analogue, with a clear **onboarding band** (e.g., grades 1-3 → fast-track; 4-6 → review; 7-10 → decline/nurture).
- **Model choice — interpretable by construction:** a **WOE/IV scorecard (logistic)** as the transparent backbone, optionally a **monotonic-constrained gradient-boosted model (XGBoost/LightGBM)** for lift — never an opaque black box. Deterministic feature layer first; ML for ranking; reasons always attached.
- **Calibration & honesty:** on synthetic data we calibrate to the generator and **state explicitly that real-default backtesting + recalibration is the productionization step** — turning the synthetic-data ceiling into a credibility signal rather than a hidden weakness.

## 6. Explainability (C4 — bank-grade)

- **Reason codes per decision:** top positive/negative drivers in plain language (e.g., "On-time GST filing 11/12 months (+)", "Bank inflows 38% below GST turnover (–)"). SHAP for the GBM path; native point-contributions for the scorecard.
- **Stability:** reason codes validated for consistency across recalibration (research flagged SHAP instability — we test for it).
- **Auditability:** every score carries its inputs, feature values, model/prompt version, and reasons — the same provenance discipline as ReconWise's citation gating. Aligns with RBI's "understandable by design" / explainable-credit expectations.

## 7. The Financial Health Card (C5 — visualization)

A single screen: **composite grade + score**, a **pillar radar/bar** (strengths vs risks), **top reasons**, **recommended product + indicative limit**, **key risk flags** (e.g., GST-bank mismatch, declining balance), and an **onboarding recommendation** with an officer accept/override + audit trail. Designed for "what a credit officer needs in 30 seconds."

## 8. Near-real-time API & architecture (C6 + deployment)

- **Scoring API:** `POST /score` (entity + data bundle → score, pillars, reasons, recommendation); `GET /card/{id}`; an `/ingest` for AA-fulfilment callbacks. Sub-minute target (incumbents decision in <1 min).
- **Deployment (superseded — see [`implementation-plan.md`](implementation-plan.md) §8):** the stage-1 prototype ships as a single container on **Google Cloud Run** (scale-to-zero, Mumbai region). The production-architecture sketch (managed Postgres, object storage, LLM-narrated reason codes on a deterministic core, IaC, OpenTelemetry, India residency, per-tenant isolation, audit log) carries over to whichever cloud a bank pilot lands on.
- **Stage-1 deployment:** a publicly reachable demo (deploy link) + public GitHub repo — the two mechanical submission requirements.

## 9. Evaluation & validation harness (C7)

- **Metrics:** discrimination (AUC/Gini/KS) on the synthetic holdout, **calibration**, **stability/PSI**, and **segment performance** — with a deliberately **leakage-resistant holdout** design (demo entities never leak into reported test metrics).
- **Determinism & integrity tests** (ReconWise pattern): re-runs are identical; pillar/composite math ties out.
- **Honesty gate:** the eval report states synthetic-data limits and the real-data recalibration plan. A CI scorecard mirrors ReconWise's release-gate table.

## 10. Trust, compliance & residency

Explainable-by-construction; human-in-the-loop with override + audit; India data residency; no training on customer data; consent-first AA posture; DPDP-aware. Maps to RBI digital-lending / model-risk / FREE-AI explainability expectations. This posture is itself a first-class requirement for a bank, not an afterthought.

## 11. Scope by stage

- **Stage-1 (≤9 Jul, own synthetic data):** C1-C7 at demo quality on a synthetic MSME cohort + the mock AA/ULI adapter + the Health Card UI + scoring API + deploy link + GitHub + PPT. Differentiation concentrated in C2/C4/C6 and the C8 narrative.
- **Stage-2 (22-31 Jul, IDBI mock data in ACC/AWS sandbox):** re-fit features/score on IDBI mock data, wire the real sandbox adapter, harden, polish the demo.
- **Production (post-hackathon pilot):** real GSTN-via-AA + bureau + AA bank feeds, real-default backtesting & recalibration, model-risk sign-off.

## 12. Why this approach

It addresses all five evaluation dimensions at once: **innovative** (GST-vs-bank consistency + a multidimensional alt-data card), **feasible** (built on the data sources the problem statement names, on a proven stack), **scalable** (cloud-native, API-first), **business impact** (onboard credit-invisible MSMEs + protect portfolio quality — PS3's exact stated outcome), **technical implementation** (real architecture, eval harness, explainability — not slides). The core strength is what Lambdac already does in production: **explainable, auditable, GST-fluent, deployable.**
