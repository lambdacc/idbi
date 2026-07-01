# Feasibility Deep-Dive — IDBI Innovate 2026, Financial Health Score track

**Question on the table:** Is this doable, and can **pure agent-based research and development** (the agent does the research and writes the code; humans review at checkpoints) get us to a *competitive, winning* entry?
**Prepared for:** Lambdac Computing — founders · **Date:** 27 Jun 2026 · **Scope:** Track 03 (Financial Health Score) only · **Type:** feasibility verdict + evidence (no build).
**Companion files:** [`research-evidence.md`](research-evidence.md) (graded sources), [`hackathon-brief.md`](hackathon-brief.md), [`screening-assessment.md`](screening-assessment.md), [`orientation-review-and-pivots.md`](orientation-review-and-pivots.md).

> **Update (28 Jun 2026, post-orientation):** The official **PS3 is titled "Financial Health Score"** and matches this deep-dive's concept verbatim (MSME Financial Health Card on GST/UPI/AA/EPFO → multidimensional score → visualize → ULI/OCEN/AA integration → near-real-time, onboarding credit-invisible NTC/NTB MSMEs). **Target and verdict validated; nothing below changes.** New operational facts: a **working prototype is due 9 Jul** on our own synthetic data (sandbox/mock data + AWS/ACC only after the 21 Jul shortlist), **one PS per team**, mandatory PPT template. The §7 agentic operating model now runs against an ~11-day stage-1 clock. See `orientation-review-and-pivots.md`.

---

## 0. Verdict (BLUF)

**Doable: yes, with high confidence.** A credible "MSME Financial Health Card" PoC — multi-source alt-data ingestion → explainable multidimensional score → visual card → AA/ULI integration adapter, demoed on synthetic data — is well within reach for a small team on the hackathon's timeline. The genuinely hard part of credit modelling (validating real predictive accuracy against real defaults) is **not** what this track is asking for and can be honestly deferred to a post-PoC step.

**Can pure agentic R&D get us there: yes to *compete*, with one load-bearing caveat.** The evidence is clear that 2025-26 coding agents reliably build the *engineering* of this product end-to-end and do a solid first pass at the ML. But "**pure**" / fire-and-forget autonomy is **not** what wins. The win-deciding ~30% — domain feature design, evaluation design, explainability that survives a banker's scrutiny, and the business-impact narrative — is exactly where agents measurably fail and where humans must own the decision. Under an **agent-as-fast-implementer + heavy human judgment gates** model, a small expert team is genuinely competitive — and Lambdac is *advantaged*, because the winning levers are the same ones it already engineered into ReconWise.

**Bottom line:** Pursue is the right call (consistent with screening). The realistic operating model is not "an agent builds it while we watch" but "an agent builds it 3-5× faster than we could, and we spend our saved time on the judgment that actually wins." Treat any pitch of *fully autonomous* development as the wrong frame — both for winning and for what a bank wants to hear.

---

## 1. What the track actually asks us to build

From the problem statement (see brief): an **AI/ML MSME Financial Health Card** that (a) aggregates alternate data — GST, UPI/bank, Account Aggregator, "EPFO etc."; (b) computes a **multidimensional financial-health score**; (c) **visualizes** strengths and risks; (d) **integrates with the ULI / OCEN / AA** ecosystems; (e) enables **near-real-time** credit assessment of thin-file / credit-invisible MSMEs.

Decomposed into buildable components:

| # | Component | What it is |
|---|---|---|
| C1 | **Ingestion & normalization** | Parse GST returns, bank/UPI statements, bureau-shaped data into a canonical schema |
| C2 | **Alt-data feature engineering** | Turn raw data into health signals (cash-flow, filing discipline, GST-vs-bank consistency, bounce behaviour, vintage, leverage) — *the domain core* |
| C3 | **Scoring model** | Map features → a multidimensional score + a single rank (CMR-style 1-10 or CRIF-style 300-900) |
| C4 | **Explainability** | Per-decision reason codes / driver breakdown (SHAP or a transparent scorecard) |
| C5 | **Financial Health Card UI** | The visual dashboard: score, pillar strengths/risks, recommended bank action |
| C6 | **AA / ULI integration adapter** | A working, schema-correct mock of the consent-based data pull (ReBIT XSD / ULI API shapes) |
| C7 | **Eval harness** | Metrics, calibration, leakage-resistant validation |
| C8 | **Business-impact + demo** | The quantified NPA/throughput story and the 90-second working demo |

This decomposition matters because **doability and agentic-suitability differ sharply by component** (§4, §5).

## 2. Is it doable? (technical + data reality)

**Technically, the build is tractable.** Every component is a known pattern: statement/return parsing, feature engineering, gradient-boosted or scorecard models, SHAP, a web dashboard, a schema-driven API adapter, and an eval harness. None requires novel research. The methods are well-established — WOE/IV scorecards + logistic regression for interpretability, or monotonic-constrained XGBoost/LightGBM + SHAP for performance with explainability (research-evidence §A2).

**The binding reality is data, and it cuts two ways:**

- *In our favour:* the track hands shortlisted teams **synthetic MSME/transaction/UPI datasets**, and the GST→AA path is real and well-documented — **GSTR-1 (Table 4) + GSTR-3B for the last ~18 months** flow consent-based via GSTN-as-FIP (live since Nov 2022). A Financial Health *Card* is fundamentally a **feature-engineering + explainability + integration** exercise, all of which are fully demonstrable on synthetic data.
- *Against us (the ceiling):* **synthetic data cannot validate real predictive accuracy.** Credit-model validation requires backtesting against *real* defaults; on synthetic data the model learns the generator's assumptions, not reality (research-evidence §E, J.P. Morgan/Cambridge). This is a hard ceiling — but it constrains *Default Prediction* (Track 04, with its ~90% accuracy target) far more than it constrains *Financial Health Score*. **It is the single strongest reason Track 03 is the right pick:** a health card wins on transparency, coverage, and integration — things synthetic data *can* show — not on a default-AUC number it cannot honestly produce.

**Two factual corrections to the brief's premise** (don't get caught out by these in the pitch):

1. **EPFO is NOT on the Account Aggregator rails.** EPF/PPF are "proposed/not live" FI types; NPS *is* live. Treat EPFO as a mocked/roadmap signal, not a live integration. (research-evidence §C)
2. **ULI and OCEN are real but less mature than the brief implies.** ULI is RBI/RBIH-operated and scaling (64 lenders, Dec 2025) but last disclosed volumes are Dec 2024 (~₹27,000 cr). **OCEN's standalone momentum has largely migrated into ONDC Financial Services** — speak to "AA + ULI + ONDC/OCEN" accurately rather than treating OCEN as a thriving independent network. (research-evidence §C)

**Doability verdict:** the *PoC asked for* is clearly doable; the *thing synthetic data can't give you* (proven default accuracy) is out of scope for this track. Build the card, demo the integration, and be explicit that real-default recalibration is the productionization step. That honesty is itself a credibility signal to bank judges.

## 3. The agentic R&D question — what the evidence says

Can an agent do the research-and-build? Here is the calibrated evidence, not the hype.

**Agents are strong and reliable at the *engineering*.** On SWE-bench Verified, frontier models now exceed **~80%** (Claude Opus 4.5, Nov 2025); Terminal-Bench (end-to-end terminal/data-science tasks) tops **~83%** (2026). The data pipeline, FastAPI service, dashboard, eval-harness plumbing, and the schema-driven AA/ULI adapter are all "Terminal-Bench-shaped" work the agent does well. (research-evidence §F)

**Agents are improving fast but still mid-tier at autonomous *ML engineering*.** On MLE-bench (real Kaggle tasks), best agents went from ~17% any-medal (2024) to **~62-64%** (early 2026) — a 4× jump, but with heavy caveats (offline tasks, vendor-reported, leaderboard frozen pending a fairness overhaul). On METR's RE-Bench, agents beat human experts only at *short* time budgets; **at 8h+ humans pull ahead, and at 32h the average human scores ~2× the best agent.** "Kaggle Grandmaster agent" claims are disputed and overstated. (research-evidence §F)

**The failure modes are precisely our win-deciding components.** Documented, quantified agent weaknesses: long-horizon multi-file coherence collapses (a model at ~73% on single-issue tasks drops to ~25% on long multi-file evolution); under-specified requirements → confident wrong guesses (forcing clarification improved results up to 74%); hallucinated APIs/packages (~20% of generations); insecure code (~45% of samples carried a vulnerability); and **domain feature design + evaluation design are where generic agents most underperform.** (research-evidence §F)

**So the honest answer to "can *pure* agentic R&D win this?"** — No, not "pure" in the fire-and-forget sense. **Yes** in the sense that matters: an agent, *driven in small, test-green, human-gated increments*, can build this product far faster than a human team, freeing the humans to own the 30% that wins. The consensus operating model (Anthropic, GitHub, ThoughtWorks, practitioners): **spec-first with human sign-off → evals as ground truth → small verifiable increments → explicit review gates → concentrate human effort on feature/data/eval/fairness judgment.** (research-evidence §G)

## 4. Doability × agentic-suitability scorecard

Rating each component on technical doability, how much of it an agent can own, and data availability for a PoC. ("Human-owns" = the judgment a person must supply at the gate.)

| Component | Doable? | Agent can own | Human owns (the gate) | Data for PoC |
|---|---|---|---|---|
| C1 Ingestion/normalization | High | **High** — parsers, schema mapping | Canonical schema sign-off, edge-case rules | Synthetic + ReBIT XSD shapes ✅ |
| C2 Feature engineering | High | **Medium** — implements fast, proposes features | *Which* features, why, validation — **the moat** | Synthetic ✅ |
| C3 Scoring model | High | **High** — train/tune/CV | Target definition, calibration, monotonic constraints | Synthetic ✅ (accuracy not validatable) |
| C4 Explainability | High | **High** — SHAP/reason-code impl | Are reason codes *defensible & stable*? | Synthetic ✅ |
| C5 Health Card UI | High | **High** — dashboard build | UX of "what a banker needs to see" | n/a ✅ |
| C6 AA/ULI adapter | High | **High** — schema-driven mock | Correctness vs ReBIT/ULI spec; consent model | Public specs ✅ |
| C7 Eval harness | Medium | **Medium** — implements metrics | Metric choice + **leakage-resistant holdout** (agents overfit weak evals) | Synthetic ⚠ ceiling |
| C8 Business case + demo | Medium | **Low** — drafts only | The narrative, numbers, live demo, Q&A | n/a ✅ |

**Read of the scorecard:** ~5 of 8 components are high-agentic-ownership engineering the agent accelerates dramatically. The 3 that decide the contest (C2, C7, C8 — and the judgment slice of C3/C4) are human-owned. That is the whole feasibility story in one table.

## 5. Can *we specifically* compete? (Lambdac's edge)

The winning levers in this kind of bank hackathon are remarkably stable across rubrics: **deployability, explainability, domain depth, a working demo, and a quantified business case** — not raw model cleverness (research-evidence §H, BoB/RBI HARBINGER winner patterns). Crucially, **Lambdac has already engineered for exactly these** in ReconWise:

| Winning lever | What Lambdac already does (evidence from ReconWise docs) |
|---|---|
| **Explainability / "model issues its own reasons"** | ReconWise's core stance is *deterministic-first, AI-second; the AI explains, never decides*, with **citation gating (100% of claims must resolve to a source)** and a verdict-change guard. This is the same architecture a bank wants for a credit score. |
| **Eval rigor that survives scrutiny** | A real accuracy-evaluation framework with golden datasets, per-class precision/recall **gates (≥99%/≥98%)**, determinism tests, and a CI scorecard. Most hackathon teams have *no* eval discipline; this is a differentiator. |
| **Deployable, bank-grade architecture** | Existing AWS **ap-south-1** stack (FastAPI, Polars, Postgres/pgvector, Bedrock/Claude, RLS multi-tenancy, audit trail, Terraform). The demo *is* a deployment blueprint — which is what "integration readiness" scores. |
| **Domain depth in GST/Indian fin-data** | ReconWise is built on GST returns (GSTR-2B/2A, ITC) and Indian compliance — directly transferable to GST-as-alt-data feature engineering, the C2 moat. |
| **Proven build velocity with a tiny team** | ReconWise plan: a full multi-tenant AI SaaS MVP in **6-8 weeks with 3-4 people** — and that was *before* leaning hard on agentic build. The hackathon scope is a fraction of that. |

In short: the parts of this challenge that agents can't do, **Lambdac has already proven it does** — and the parts agents *can* do are what compress the timeline. That combination is the argument for competing.

**Competition reality (balanced):** the field's *median* is weak — across comparable hackathons ~9-12% of registrants even submit a working build, and overscoping + hollow demos are the norm. But the *bar* set by incumbents (Perfios, CRIF CIMR, FinBox, Lentra, Scienaptic) is high, and IDBI's eligibility tier (startups/fintechs/professionals) self-selects a stronger-than-average field. Finalist rates at comparable bank contests run ~2-4%, but the *effective* field for one named MSME problem with a ₹15L pool is hundreds, not tens of thousands, narrowing to ~10-30 finalists. **For a focused expert team hitting all the winning levers, this is a favourable risk/reward bet** — and the downside is cushioned: even short of first place, the sandbox access, mentorship, and named **PoC-in-IDBI's-sandbox pathway** are strategically valuable (research-evidence §H).

## 6. Blockers & risks (with mitigations)

| Risk | Severity | Mitigation |
|---|---|---|
| **Synthetic-data validation ceiling** — can't prove real accuracy | High (but track-appropriate) | Compete on explainability/coverage/integration, not AUC; state real-default recalibration as the productionization step. Pick FHS over Default Prediction precisely for this. |
| **Data/API gating** — real sandbox APIs & datasets unlock only post-shortlist (date unconfirmed) | Medium | Build on self-generated synthetic data + public ReBIT/ULI specs; design a clean adapter so the sandbox plugs in at a later checkpoint. |
| **"Pure agentic" framing fails** — fire-and-forget yields a mid-pack, possibly insecure entry | High | Adopt the human-gated operating model (§3); never present "fully autonomous build" to a bank — present "AI-accelerated, human-validated." |
| **Agent failure modes** — long-horizon incoherence, hallucinated deps, ~45% vuln rate | Medium | Small test-green increments; eval/tests as ground truth; human security review gate; pin dependencies. |
| **Explainability not defensible** — SHAP unstable across recalibration | Medium | Prefer interpretable scorecard or monotonic-constrained GBM; validate reason-code stability; lean on ReconWise's citation-gating discipline. |
| **Brief premise errors** (EPFO on AA; OCEN as live network) | Low | Correct them in our solution narrative — turning a trap into a credibility signal. |
| **Opportunity cost vs ReconWise** | Medium-High | Time-box to 1-2 people; reuse ReconWise IP so work compounds (alt-data scoring is already on their roadmap). |

None is fatal. The two that most shape strategy are the **synthetic-data ceiling** (→ pick FHS, compete on transparency) and the **agentic operating model** (→ human-gated, not pure-autonomous).

## 7. What it would take to win (resourcing & operating model)

**Scope of a winning PoC:** all 8 components at demo quality, with the differentiation concentrated in C2 (a genuinely smart GST-as-alt-data feature set), C4 (defensible reason codes), C6 (a correct AA/ULI adapter), and C8 (a quantified NPA-reduction / thin-file-inclusion story + a 90-second live demo).

**Team & time:** 1-2 people, time-boxed, against the IDBI calendar (register by 9 Jul; prototype by 31 Jul; finale 21 Aug). This is comfortably less than the ReconWise 6-8 week MVP, and agentic build compresses it further.

**The agentic operating model (this is the answer to the user's question, made concrete):**

1. **Spec-first.** Human writes/sign-off a tight spec + the eval definition *before* code. (Agents fail on ambiguity; specs fix that.)
2. **Evals as ground truth.** Human-designed metrics + a leakage-resistant holdout are the agent's success criterion — not the agent's own assertions.
3. **Small, test-green increments** behind explicit **review gates** (inner: per TDD cycle; outer: per component/milestone).
4. **Concentrate human time on the 30%:** feature/data judgment (C2), eval/fairness design (C7), the business narrative and demo (C8), and a security review gate.
5. **Toolchain:** the agent for implementation across C1/C3/C5/C6 and first-pass C2/C4; humans own decisions at every gate. Reuse ReconWise patterns (LLM gateway, eval scorecard, AWS/Terraform) as scaffolding.

Under this model the honest claim is: **agentic R&D makes a 1-2 person team perform like a 4-5 person team — enough to clear every winning lever in the time available.** That is what "can pure agentic R&D enable us to compete" resolves to: not pure, but agent-led-human-gated, and yes.

## 8. Recommendation

**Proceed to Phase 2 on Track 03.** The build is doable, the data story is favourable for a *health card* (less so for default prediction), and an agent-led, human-gated development model is both feasible and well-matched to Lambdac's proven strengths. Adopt the operating model in §7, scope the PoC to the 8 components with differentiation in C2/C4/C6/C8, and frame the entry to bank judges as **AI-accelerated, human-validated, explainable, and deployable** — never as "fully autonomous."

The one decision this deep-dive sharpens: **commit to Financial Health Score over Default Prediction**, specifically because the synthetic-data ceiling makes the latter's accuracy claims un-provable while the former's win on transparency and integration is fully demonstrable.

---

*Evidence, source grades, and citations: [`research-evidence.md`](research-evidence.md). This deep-dive supersedes the lighter feasibility notes in `screening-assessment.md` §4.*
