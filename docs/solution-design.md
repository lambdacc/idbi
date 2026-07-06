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

---

# Multi-track platform

CreditPulse is now a **platform** answering three IDBI Innovate 2026 problem statements from one codebase and one shared core: PS3 above, plus two self-contained tracks — PS4 Early Warning and PS5 Fraud Intelligence — each with its own product surface but reusing the platform ML kit, staged-pipeline renderer and honesty discipline. All data in every track is synthetic; real-ledger recalibration is the pilot step in each.

## 13. Track 04 — Early Warning (PS4)

**The problem it answers.** PS4 asks for an early-warning system over the *performing* loan book: flag borrowers sliding toward default while there is still time to act, not after EMIs have already bounced. CreditPulse's answer reads the alt-data footprint (GST turnover, bank inflows, UPI, EPFO headcount, energy use) as a *leading* indicator that sags months before repayment behaviour — the internal signal a repayment-only monitor can only see late.

**Product surface (two pages).** *Portfolio Overview* (deep link `track04`) — the book-level radar: KPI row, Green/Amber/Red distribution, this month's band migration, and a flagged-accounts table with per-borrower plain-language drivers. *Watchlist & Cases* (`watchlist`) — the ranked watchlist and a per-borrower case drilldown: the alt-data footprint rolling over the months before repayment slips, marked with three points — EWS first alert, the repayment-only baseline's first alert, and projected default.

**Scoring / decision output.** A calibrated 12-month probability of default per borrower → a **Green / Amber / Red** band under one alerting policy, plus sign-aware plain-language risk drivers (e.g. "inflows lagging declared GST", "missed GST filings"). The headline is **lead time**: on the synthetic holdout the EWS turns Red a **median 11.5 months** before default versus **2.0 months** for a repayment-only baseline — an **8-month** gap — and captures **0.926** of defaulters in its top decile versus **0.519**.

**Honesty stance.** The repayment-only baseline is shown *side by side* so the lead-time gap is an honest same-policy comparison, not a strawman. Lead time is the headline; AUC is reported but deliberately not headlined. All borrowers, panels and labels are synthetic; real-default backtesting and recalibration are the productionization step.

## 14. Track 05 — Fraud Intelligence (PS5)

**The problem it answers.** PS5 asks for detection of rented-out **mule accounts** and the rings behind them — the payment-rail fraud that MHA's December-2026 directive and RBIH's MuleHunter.AI target — with decisions a bank can *explain*. SentinelPulse sits above the flagging layer: it scores accounts, then assembles the evidence and the network into a reviewable case. It is deliberately a transaction-fraud operations desk, unrelated to the lending/scoring in the other tracks (PS5's own "unrelated to PS1–4" fence).

**Product surface (two pages).** *Fraud Desk* (deep link `track05` / `fraud_desk`) — the triage queue, KPIs, suspected-ring count and typology distribution across the flagged desk. *Case Investigation* (`case_investigation`) — the five-stage agentic case file for one account: Triage → Evidence → Network → Adjudication → Case-file compiler, each stage narrated in both a technical and a jargon-free simple view.

**Scoring / decision output.** A 0–100 mule-risk score (an interpretable typology leg blended with an independent anomaly leg) banded **Alert / Review / Clear**, then a case file ending in a recommendation — **Freeze + file STR draft**, **Enhanced monitoring**, or **Clear with note** — that a human analyst approves or overrides. On the synthetic holdout: **6 of 6 rings recovered** (a ring counts as caught when ≥60% of its members are flagged), recall-at-alert **1.0**, precision-at-alert **0.744** — and precision-*ring*-at-alert **1.0**, because the "misses" are themselves ring-associated infrastructure (recruiter/cash-out mules), and **0 of 10** hard-negative false positives.

**Honesty stance.** Every ground of suspicion **cites at least one real transaction ID or is not asserted** — the citation gate refuses uncited claims and degrades to an explicit "insufficient evidence" note instead. Roles (mule / recruiter / cash-out) are *inferred* from observable behaviour, never read from labels; the ground-truth file is eval-only and never touched at score time. The high-velocity gig-worker hard negative is *explainably cleared*, not just un-flagged. All accounts and transactions are synthetic; recalibrating on a bank's real ledger is the pilot step.
