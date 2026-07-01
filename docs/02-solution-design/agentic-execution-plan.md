# Agentic Execution Plan — CreditPulse (stage-1 to 9 Jul)

**Status:** Phase 2 build plan · **Date:** 28 Jun 2026 · **Owner:** Lambdac
**Reads with:** [`solution-design.md`](solution-design.md) (the spec), [`../00-screening/feasibility-deep-dive.md`](../00-screening/feasibility-deep-dive.md) (§7 operating model)

This is the concrete answer to "can pure agentic R&D get us there": **agent-led, human-gated.** The agent does the implementation; humans own the judgment at heavy gates. Target: a **working prototype (deploy link + public GitHub + PPT) by 9 Jul** on our own synthetic data.

---

## 1. Operating model (non-negotiables)

1. **Spec-first.** `solution-design.md` is the spec; no code before it's signed off (done).
2. **Evals as ground truth.** The human-designed eval harness + a leakage-resistant holdout are the agent's success criterion — not the agent's own claims. Built early (Day 2), not last.
3. **Small, test-green increments** behind explicit **review gates** (inner: per component; outer: per milestone). Each increment leaves the repo deployable.
4. **Humans own "the 30%":** feature/data design (C2), eval/fairness design (C7), the score/calibration decision (C3 judgment), security review, and the demo/business narrative (C8).
5. **Security & dependency hygiene:** pin dependencies (guard the ~20% hallucinated-package risk), human security-review gate before deploy (guard the ~45% vuln-rate finding).

## 2. Roles (1-2 people + agent)

| Owner | Responsibility |
|---|---|
| **Lead (domain+eng)** | Spec sign-off, feature/eval/score judgment, gate reviews, demo + pitch |
| **Second (optional, eng)** | Synthetic-data realism, UI polish, deploy/security review |
| **Agent** | Implementation across all components; first-pass features/model; tests; IaC; docs |

## 3. Milestones, checkpoints & ~11-day schedule

Today = Sun 28 Jun. Submission = Wed 9 Jul. (Buffer built in; compresses if needed.)

| Day | Build (agent) | Human gate (the decision) |
|---|---|---|
| **28-29 Jun** | Repo scaffold, CI, AWS skeleton (Terraform), canonical schema, **synthetic-data generator v1** (GST + bank/UPI + EPFO + bureau, with configurable health/fraud profiles) | **G0:** schema + synthetic-data realism sign-off (is this MSME-credible?) |
| **30 Jun** | — (attend IDBI PS deep-dive) | **Lock PS3 scope**; fold any new constraints into the spec |
| **30 Jun-1 Jul** | **Feature engineering** (5 pillars) + **eval harness** (AUC/Gini/KS, calibration, PSI, leakage-resistant holdout) | **G1:** *which features & why*; eval metrics + holdout design (the moat gate) |
| **2-3 Jul** | **Scoring model** (WOE/IV scorecard + optional monotonic GBM) → pillar + composite score → 1-10 grade + bands | **G2:** model choice, calibration, banding; eval passes targets |
| **4-5 Jul** | **Explainability** (reason codes / SHAP, stability test) + **scoring API** (FastAPI) | **G3:** are reason codes defensible & stable? API contract review |
| **5-6 Jul** | **Financial Health Card UI** (score, pillars, reasons, recommendation, flags, override+audit) | **G4:** "does a credit officer get it in 30s?" UX review |
| **6-7 Jul** | **AA/ULI/OCEN mock adapter** (ReBIT XSD shapes + consent artefact) + wire end-to-end | **G5:** adapter correctness vs spec; end-to-end runs |
| **7-8 Jul** | **Deploy** (public link), harden, **security review**, README, eval-report (with synthetic-data honesty note) | **G6:** security gate; deploy live; repo public |
| **8-9 Jul** | **PPT** (fixed template), **demo script + recording**, dry-run | **G7:** final submission review → submit |

**Critical-path note:** if time tightens, cut the GBM (keep the interpretable scorecard), cut the 300-900 analogue, and simplify the UI — but **never** cut the eval harness, the reason codes, or the GST-vs-bank consistency feature (those are the differentiators).

## 4. Toolchain

- **Agent:** Lambdac's coding-agent setup (spec-driven, test-green increments, review gates). Reuse ReconWise scaffolding (LLM gateway, eval scorecard pattern, Terraform).
- **Stack:** Python/FastAPI, Polars, PostgreSQL/pgvector, AWS ap-south-1 (Fargate/Lambda, S3), Bedrock (Claude) for reason-narration only, Next.js/React (or Streamlit for stage-1 speed) for the Card, GitHub + Actions CI.
- **Repo:** public GitHub (submission requirement) — keep secrets out, clean README, reproducible `make demo`.

## 5. Stage-2 plan (post-21 Jul shortlist, if selected)

Refit features/score on **IDBI mock data** in the **ACC/AWS sandbox**; replace the mock adapter with the real sandbox APIs; harden; deepen the eval; polish demo for the 22-31 Jul refined-prototype window; prep for 13 Aug finalist / 21 Aug demo day.

## 6. Risk controls (build-specific)

| Risk | Control |
|---|---|
| Agent long-horizon incoherence | small increments, each test-green; never one mega-run |
| Hallucinated deps / insecure code | pinned deps, human security gate (G6), CI |
| Overfit / leaky eval | human-designed holdout (G1); PSI/calibration, not just accuracy |
| Synthetic-data over-claim | honesty note in eval-report + PPT; recalibration framed as productionization |
| Scope creep vs 9 Jul | the critical-path cut-list in §3 |

## 7. Definition of done (stage-1)

Deploy link live; public GitHub with clean README + reproducible demo; eval scorecard green (with synthetic caveat); Health Card renders score + pillars + reasons + recommendation; scoring API works; AA/ULI mock adapter demonstrated; PPT (template-compliant) + demo recording submitted before 9 Jul.
