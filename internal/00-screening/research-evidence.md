# Research Evidence — IDBI FHS Feasibility Deep-Dive

Graded source compendium backing [`feasibility-deep-dive.md`](feasibility-deep-dive.md). Compiled 27 Jun 2026 from three parallel research sweeps + Lambdac internal docs.
**Grades:** **[P]** primary (regulator/bureau/official spec, verified) · **[S]** secondary, corroborated · **[U]** single-source/vendor, directional only.

---

## A. MSME health-scoring — signals & methods

- **Strongest predictive signals (practitioner consensus):** repayment/bounce behaviour; **GST-vs-bank turnover reconciliation gap** (named the single best fraud/health cross-check); average balance + low-balance frequency + balance volatility; 3 consecutive months of falling balance while inflows hold = stress; GST filing regularity + turnover trend; **DSCR ≥ 1.25**, **FOIR ≤ ~55%**; business vintage. [S]
- **GST data:** lenders use **GSTR-1 + GSTR-3B, 6-12 months**; GSTR-1 is a hard-to-fake government sales ledger; filing regularity is itself a discipline proxy. [S]
- **Methods:** WOE/IV → logistic-regression **scorecards** (interpretable, industry standard) vs **XGBoost/LightGBM** (higher AUC, interpretability deficit). One study XGBoost AUC ≈0.85 vs LR ≈0.72 — dataset-specific, don't over-read. [S]
- **"Good" metrics:** Gini = 2·AUC−1; defensible MSME/retail ranges **AUC ~0.70-0.85, Gini ~0.40-0.70, KS ~30-50**; AUC >0.90 should trigger leakage/overfit suspicion. **No RBI-published numeric benchmark — RBI specifies process, not targets.** [S]

## B. Benchmarks — CIBIL / CRIF

- **CIBIL MSME Rank (CMR): 1-10, 1 = least risky**, predicts 1-year PD; exposure band <₹10L-₹50cr; scored on most recent **24 months** bureau history; PD curve ~CMR-1 ≈1.6% → CMR-10 ≈94.4%; STP "green channel" for CMR-1-3. Exact weights proprietary. [P]
- **CRIF High Mark:** MSME Rank (13-rank, 36-mo observation/12-mo performance) + 300-900 commercial score (900 = lowest risk). Four RBI bureaus: CIBIL, Experian, Equifax, CRIF. [P/S]
- **PoC implication:** natural output = CMR-style 1-10 or CRIF-style 300-900; compete on **transparency**, not on replicating proprietary models.

## C. Ecosystem status (2025-26) — AA / ULI / OCEN / GSTN

- **Account Aggregator [P]:** RBI-regulated consent framework, live since Sept 2021; FIP/FIU/NBFC-AA roles; data-blind consent managers; signed consent artefact; ~2.6B accounts enabled, ~250M+ users (Dec 2025); AA-facilitated lending ~₹1.47L cr / ~1.5cr loans H1 FY26.
- **GSTN-as-FIP [P, verified from GSTN doc]:** notified Nov 2022; flows **GSTR-1 (Table 4) + GSTR-3B, completed returns last 18 months**, plus filing details + basic profile. FI-type **Live**.
- **EPFO correction [P]:** **EPF/PPF NOT live on AA** ("proposed/NA"); **NPS IS live**. The brief's "EPFO" premise must be treated as mock/roadmap.
- **ULI [P/S]:** RBI/RBIH credit rail (ex-PTPFC, rebranded Aug 2024); **64 lenders, 136+ data services, Dec 2025**; last disclosed volumes **Dec 2024 (~600k loans, ~₹27,000 cr; ~160k MSME loans ~₹14,500 cr)**; RBI reviewing amid slower-than-expected adoption.
- **OCEN [S, caveat]:** iSPIRT/CredAll origination protocol, spec **OCEN 4.0**; standalone momentum has **largely shifted into ONDC Financial Services**. Don't present OCEN as a thriving independent network; a "70k loans/₹1,600cr" stat surfaced but is **unverified — exclude.**
- **Spec refs [P]:** ReBIT `https://api.rebit.org.in/schema`, `https://specifications.rebit.org.in/` (NBFC-AA API Spec v2.0.0, per-FI XSDs); RBIH ULI `https://rbihub.in/projects/unified-lending-interface`; OCEN `https://ocen.dev/docs/ocen_4_0/`.

## D. Regulatory / explainability through-line

- **RBI Digital Lending Directions 2025** — notified, effective 8 May 2025 (multi-lender 1 Nov 2025); require creditworthiness assessment, auditable processes, KFS disclosure. [P]
- **RBI draft "Model Risk in Credit"** (5 Aug 2024) — **still draft**; outcomes must be "unbiased, explainable, verifiable"; covers AI/ML & third-party models. Directional, not binding. [P]
- **RBI FREE-AI report** (13 Aug 2025) — "Understandable by Design"; AI credit models must be explainable, auditable, bias-free; customers told they're dealing with AI and able to challenge. Committee report (directional). [P]
- **Implication:** prefer interpretable scorecards / monotonic-constrained GBM + SHAP reason codes; "the model that issues the decision produces the reasons." Strongest demonstrable PoC differentiator.

## E. Synthetic-data ceiling (why FHS > Default Prediction)

- **No real default labels = no real validation** — model learns the generator's assumptions (circularity). [S — J.P. Morgan, Cambridge]
- **Low-default-portfolio / class imbalance** — accuracy misleads (~99.8% by predicting "no default"); Gini/AUC more stable but not immune. [S]
- **Distribution realism is an open research problem.** [S]
- **Tractable on synthetic data:** alt-data feature engineering, scorecard + explainability UI, AA/ULI integration mock, output benchmarked to CMR/CRIF format. **Honest framing wins:** demo pipeline+explainability+integration; state real-default backtesting as post-PoC. [S]

## F. Agentic R&D capability (2025-26)

- **Software engineering — strong:** SWE-bench Verified **>80%** (Claude Opus 4.5, Nov 2025; first over 80%); Terminal-Bench ~**83%** (2026). Data pipeline / API / dashboard / adapter / eval plumbing are within reliable agent competence. [P/S]
- **Autonomous ML engineering — mid-tier, rising:** MLE-bench best **~62-64%** any-medal (early 2026, up from ~17% in 2024) — but offline, vendor-reported, leaderboard frozen pending fairness overhaul. METR RE-Bench: agents beat humans only at short budgets; **at 32h avg human ≈ 2× best agent**. "Kaggle Grandmaster agent" claims disputed/overstated. [P/S]
- **Failure modes (quantified):** long-horizon multi-file coherence collapse (~73% → ~25% on long evolution tasks); under-specification → confident wrong guesses (clarification improved results up to 74%); hallucinated packages (~20% of generations); **~45% of AI-generated samples carried a vulnerability**; domain feature design + eval design are where agents most underperform. [S]
- **Net:** agents excel at bounded, testable, greenfield engineering; they fail at ambiguity, long-horizon coherence, domain judgment, eval design, and security — i.e., the win-deciding parts.

## G. Agent operating-model best practice (convergent: Anthropic, GitHub, ThoughtWorks, practitioners)

1. **Spec-first**, human sign-off before code (Spec Kit, Kiro). 2. **Evals/tests as ground truth** ("evals are the new unit tests"); demand evidence, not assertions. 3. **Small verifiable increments**, each leaving the build green. 4. **Review gates** (inner per TDD cycle, outer per milestone) — agent pauses for human permission. 5. **Concentrate human effort on "the 30%"** (Osmani's 70% problem; Willison's "vibe engineering" — AI amplifies senior discipline, doesn't replace it). [S]

## H. Competition & winning bar

- **Incumbent bar:** Perfios (unicorn; bank-statement + GST/ITR/MCA/EPFO analysis; acquired Karza), CRIF CIMR (explainable 13-rank), FinBox (AA-native alt-data), Lentra (sub-minute decisioning, 50+ lenders), Scienaptic (explainability/adverse-action codes), Yubi YuALT. Credible PoC must fuse multiple sources + be explainable + speak AA/ULI/GST + output score+memo+flags + be API-fast. [S]
- **What judges reward:** IDBI's 5 dims (innovation, feasibility, scalability, business impact, technical implementation) + cross-rubric consensus on UX/demo, security, **compliance/explainability**; SBI adds explicit "Regulatory Readiness". Winners (BoB 2024 ComplianceAI; RBI HARBINGER OneRadar) won on **real problem discovery + working demo + tight scope + clean pitch/Q&A**, not cleverness. [S]
- **Field quality:** ~9-12% of registrants submit a working build; overscoping + hollow demo are the median failure. IDBI's eligibility tier self-selects stronger entrants. [S]
- **Win dynamics:** comparable bank contests ~2-4% finalist rate, but effective field for one MSME problem (₹15L pool) is hundreds → ~10-30 finalists. **Asymmetric upside even short of winning:** sandbox APIs, synthetic data, mentorship, and a named **PoC-in-IDBI-sandbox** pathway. [S]

## I. Lambdac internal capability (from ReconWise design docs)

- **Deterministic-first, AI-explains-never-decides**, with **100% citation gating** and verdict-change guards — directly transferable to an explainable credit score. (`03-architecture/ai-rag-and-notice-engine-design.md`)
- **Accuracy-evaluation framework**: golden datasets, precision/recall **gates ≥99%/≥98%**, determinism tests, CI scorecard — eval discipline most hackathon teams lack. (`06-quality/accuracy-evaluation-framework.md`)
- **Bank-grade stack**: AWS ap-south-1, FastAPI, Polars, Postgres/pgvector, Bedrock/Claude, RLS multi-tenancy, audit, Terraform. (`03-architecture/system-architecture.md`)
- **Velocity**: full multi-tenant AI SaaS MVP in **6-8 weeks, 3-4 people** — pre-agentic. (`07-delivery/engineering-plan-and-milestones.md`)

---

## Key uncertainty flags (carry into Phase 2)
1. **EPFO not on AA** — adjust narrative. 2. **ULI 2025 volumes undisclosed** (latest Dec 2024). 3. **OCEN standalone weak** / migrating to ONDC — exclude unverified stats. 4. **RBI Model-Risk circular is draft.** 5. **Gini/KS/AUC "good" ranges are conventions**, not regulator-set. 6. **CMR/CRIF weights proprietary** — only categories/scale public. 7. **Agent benchmark % approximate** (some models postdate research cutoff; corroborated via official leaderboards). 8. **Exact IDBI track wording / prize split / shortlist date** — confirm on portal.

## Source index (selected, by grade)

**Primary:** CIBIL CMR sheet · GSTN AA PDF · Sahamati FI-types table · RBI FREE-AI report · RBI Digital Lending Guidelines · RBI draft Model-Risk circular · ReBIT schema/spec portals · RBIH ULI page · OCEN 4.0 spec · U.K. Sinha Committee report · ULI volume (Business Standard, Dec 2024) · SWE-bench/Terminal-Bench leaderboards · MLE-bench (OpenAI/arXiv) · METR RE-Bench.
**Secondary:** Argus-P (DLD 2025) · KPMG (FREE-AI) · CRIF CIMR · Precisa (cash-flow/GST-bank/DSCR) · Altair (scorecards) · J.P. Morgan & Cambridge (synthetic-data/validation) · Perfios/FinBox/Lentra/Scienaptic/Yubi product pages · fundsforNGOs (IDBI dims) · GFF/SBI & Hack2skill rubrics · BoB & RBI HARBINGER winner writeups · Anthropic/GitHub/ThoughtWorks/Willison/Osmani (agent practice) · METR dev-productivity RCT · Veracode 2025 · slopsquatting & Ambig-SWE (arXiv).

*Full URLs are preserved in the research run; reproduce via the queries in §A-§H if link-level citation is needed for the Phase 2 docs.*
