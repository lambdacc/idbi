# Phase 1 Screening — IDBI Innovate 2026

**Prepared for:** Lambdac Computing — founders · **Date:** 26 Jun 2026 · **Author:** AI development strategist
**Decision requested:** Go / No-Go on entering IDBI Innovate 2026 with a fully agentic build.
**Bottom line:** **PURSUE — qualified.** Lead with the **Financial Health Score** track. This is one of the rare hackathons where Lambdac's existing competency (reasoning over Indian MSME financial data, explainable + auditable AI) *is* the winning edge, and the prize is a PoC relationship with a bank — strategically on-thesis. The only real cost is focus, during a revenue-seeking window. Conditions for "go" are in §7.

Facts this rests on are in [`hackathon-brief.md`](hackathon-brief.md); citations in [`sources.md`](sources.md).

> **Update (28 Jun 2026, post-orientation):** Official **PS3 = "Financial Health Score"** confirms this track pick — validated, not changed. See [`orientation-review-and-pivots.md`](orientation-review-and-pivots.md) and [`feasibility-deep-dive.md`](feasibility-deep-dive.md). Key operational corrections: working prototype due **9 Jul** (own synthetic data), **one PS per team** (retire the multi-track hedge in §6–7), sandbox/mock data only after the **21 Jul** shortlist.

---

## 1. What the hackathon is really rewarding

It's a **bank** running this, not an accelerator — and the published signals all point one way. The criteria (Innovation, Feasibility, Scalability, Business impact, Technical implementation), the "mistakes to avoid" list (theoretical ideas, weak banking-domain understanding, ignoring compliance, incomplete architecture), and the staged pipeline that ends in a **PoC inside IDBI's own sandbox** mean the real prize isn't ₹15L — it's being judged *deployable inside a regulated bank.*

Read between the lines, the winning entry is:

- **Deployable, not flashy.** Integration-readiness and a credible production architecture beat a slick one-off demo. A bank rewards "we can put this behind our app next quarter."
- **Explainable and compliance-aware.** Banks cannot ship black boxes for credit/risk decisions — they answer to RBI, auditors, and fair-lending norms. Every number needs a defensible "why."
- **Measurable in banking terms.** Impact framed as NPA/default-loss reduction, MSME-loan throughput, cross-sell, or RM time saved — not generic "efficiency."
- **Built on data they gave you.** They hand out synthetic transaction / **MSME financial** / **UPI** datasets and sandbox APIs; judges expect to see those used well.

That profile is almost a description of how Lambdac already builds (deterministic-first, citation-backed, human-in-the-loop, India-residency, eval-harness rigor).

## 2. Best-fit track

**Track 03 — Financial Health Score.** One-line rationale: it is the only track where Lambdac's *unfair advantage* — deep understanding of Indian MSME financial/GST/transaction data plus explainable, auditable AI — directly produces a better answer than a generalist team, and it reuses most of the ReconWise stack.

Quick scan of the alternatives:

| Track | Fit | Why |
|---|---|---|
| **03 Financial Health Score** ⭐ | **High** | MSME financial + UPI data is Lambdac's home turf; explainability is the differentiator a bank actually needs. |
| 04 Default Prediction | Medium | Adjacent, but a pure AUC bake-off where many ML teams compete on the same metric; Lambdac's explainability edge is muted. Strong **fallback**. |
| 05 Novel / Open | Medium | Flexible; a GST-as-alt-data underwriting pitch could shine, but open tracks are noisier to win. Strong **wildcard**. |
| 02 Prospect Assist | Low–Med | CRM/sales-assist; off Lambdac's domain. |
| 01 Digital Wealth (avatar) | Low | Consumer avatar/voice UX — furthest from Lambdac's strengths. |

## 3. Solution concept

**"CreditPulse" — an explainable MSME Financial Health Score for IDBI.** A scoring engine that ingests an MSME's transaction flows, the synthetic MSME financials, and **UPI patterns**, and outputs (a) a financial-health score, (b) the **ranked drivers** behind it in plain language, (c) early-warning/stress flags, and (d) recommended bank actions (credit-readiness, limit, cross-sell, watchlist). Delivered as a dashboard for a relationship manager plus a scoring API ready to drop behind IDBI's app.

What makes it the smartest, most attractive entry:

1. **GST/alt-data underwriting moat.** Lambdac uniquely understands GST filing behaviour as a signal of MSME health and authenticity — exactly the thin-file underwriting signal banks crave but generic teams won't think to engineer. **The Track 03 problem statement explicitly names GST + UPI + AA + EPFO as inputs and asks for ULI/OCEN/AA integration**, so this angle is endorsed by the brief, not a stretch. The bank reaches GST not as a raw IDBI API but **consent-based via the Account Aggregator framework** (GSTN became an FIP in Nov 2022: last ~18 months of GSTR-1/GSTR-3B + filing history); the build's job is a clean **GSTN-via-AA / ULI adapter**, demoed on synthetic GST data. This is the standout angle (§5).
2. **Explainable by construction.** Same stance as ReconWise — *deterministic-first, AI-second.* The score is computed in code (auditable, reproducible); the LLM only narrates drivers and drafts the RM's action note, with every claim traceable. That's a bank-grade answer to model-risk and fair-lending, not an afterthought.
3. **Production architecture out of the box.** Reuse ReconWise's proven pattern — FastAPI + Polars scoring workers, Postgres, AWS ap-south-1, multi-tenant isolation, audit trail, eval harness — so the demo *is* a deployment blueprint, which is precisely what "integration readiness" rewards.
4. **Impact the bank can price.** Quantify in default-loss avoided and MSME-loan throughput, backed by a simple model in `04-financials/`.

It also compounds rather than distracts: alt-data MSME scoring is already a roadmap extension of ReconWise ("AI Practice OS" → SME-facing finance), so the work is reusable IP, not a detour.

## 4. Feasibility via fully agentic development

**High.** This is a software build — data pipeline, scoring/ML model, explainability layer, dashboard, scoring API — all well within an agent-generates-code-with-human-review-at-checkpoints workflow, especially because Lambdac already has the reference patterns.

Natural human checkpoints: (1) data-schema + scoring-feature design sign-off, (2) model/scoring logic + explainability review, (3) demo + impact-narrative review, (4) submission package review.

**Blockers / risks to flag:**

- **Gated data (timing risk).** Real sandbox APIs and datasets unlock only *after* shortlisting, at an unconfirmed date between 9 and 31 Jul. The agentic build must start on **synthetic/self-generated MSME data** and treat live-API integration as a later checkpoint. Plan for it; don't depend on it for the core demo.
- **Synthetic data ceiling.** Model accuracy is bounded by the provided data — reinforces competing on **explainability + approach + deployability**, not raw AUC.
- **Unknown API contracts.** Integration depth is unknowable pre-shortlist; design to a clean adapter so the sandbox plugs in without rework.
- **Domain-credibility burden.** A bank's MSME-credit judges will probe assumptions; the agent's output needs a human with banking/credit sense at the review checkpoints (mentors provided can fill gaps).
- **Opportunity cost (the real one).** Lambdac's own strategy docs say "say no to everything for 90 days" while chasing first ReconWise revenue. Diverting the team is the genuine risk — see §7.

No technical blocker is fatal; the binding constraint is calendar + focus, not capability.

## 5. Win potential & standout angle

**Win potential: above average, conditional on focus.** Most teams will either bolt a black-box model onto Default Prediction (an AUC contest) or build a flashy avatar with thin substance. Lambdac can occupy the gap a bank actually cares about: **a deployable, explainable, audit-ready solution.**

The specific angle that makes us stand out: **"The score a bank can defend."** An MSME health score driven partly by **GST filing behaviour as alternative data**, where every point is explained and traceable, packaged with a production architecture and a default-loss-reduction impact model. It hits all five criteria at once — innovative signal (GST alt-data), feasible (built on their data), scalable (stateless AWS pattern), business impact (NPA/throughput), technical implementation (real architecture, not slides) — and it's the one entry whose engineering rigor a bank will recognize as "ready for our sandbox."

## 6. Recommendation

**PURSUE (qualified), targeting Financial Health Score, with Default Prediction as fallback and a GST-alt-data Novel-track pitch as wildcard.**

Reasoning: rare, genuine alignment between the task and Lambdac's moat; low marginal build cost (the stack and patterns already exist and the output is reusable IP); and a prize — a bank PoC and relationship — that is directly on Lambdac's long-game thesis of reaching SMEs through trusted financial institutions. The honest counter-weight is opportunity cost during the ReconWise revenue push, which is why this is *qualified*, not unconditional. Treat it as a **time-boxed, 1–2 person effort that reuses ReconWise IP**, not a team-wide pivot — see conditions below.

## 7. Conditions for "Go" (decide by ~7 Jul)

1. **Capacity:** ≤ 1–2 people can be ring-fenced without stalling ReconWise design-partner work.
2. **Reuse, don't rebuild:** the entry must lean on existing ReconWise stack/patterns and produce reusable IP (alt-data scoring), or it's a no.
3. **Eligibility & IP terms** (team registration, multi-track rules, who owns the PoC) check out as acceptable — confirm on the portal first.
4. **Track confirmed** after a 30-minute review of the actual problem statements on the portal (this screening is from secondary sources for some specifics).

If any of 1–3 fails, **pass** and revisit for a future, better-timed hackathon using this same screening kit.

---

# Phase 2 Kickoff

Everything needed to resume without re-deriving context.

## A. Open questions & assumptions to validate

- Confirm the **exact track problem statements** on the Hack2skill portal (some specifics here are from press/secondary sources).
- **Shortlist date** and what sandbox/data access actually includes; dataset schemas.
- **Evaluation weights**, team-size limits, **multi-track entry** allowed?
- **IP / PoC ownership** terms; whether ₹15L is cash vs. PoC-contract value; any equity/usage rights IDBI takes.
- **GST data path (mostly confirmed):** Track 03 names GST/AA/ULI/OCEN explicitly, and GST is reachable consent-based via the AA framework (GSTN = FIP since Nov 2022). **Open item:** does the sandbox actually ship sample/synthetic GST returns, or must we generate them? Confirm on portal; if absent, generate synthetic GSTR-1/3B to demo the adapter.
- Assumption: a 1–2 person time-boxed effort can hit a credible 9 Jul submission and 31 Jul prototype — pressure-test against the ReconWise calendar.

## B. Key decisions still to be made

- **Final track** (Financial Health Score vs. Default Prediction vs. Novel) — confirm post portal-review.
- **Scope** for the 9 Jul idea submission vs. the 31 Jul working prototype (define the minimum lovable demo).
- **How much ReconWise stack to reuse** vs. build fresh; repo strategy (fork patterns into `06-build/`).
- **Team allocation & time-box**; who owns the banking-domain review checkpoint.
- **Demo data strategy** pre-shortlist (synthetic generation plan) and the sandbox-integration adapter design.

## C. Phase 2 documents to produce (outline)

1. **Solution design** (`02-solution-design/`) — architecture, scoring/ML approach, explainability design, data pipeline, sandbox-integration adapter.
2. **Criteria mapping** (`03-criteria-mapping/`) — feature-by-feature map of the build to the 5 judging criteria; demo script that visibly hits each.
3. **Financials / impact model** (`04-financials/`) — default-loss-avoided and MSME-throughput model; cost-to-serve; PoC commercial framing.
4. **Deliverables package** (`05-deliverables/`) — submission checklist, pitch deck, demo video, prototype, repo link, README; mapped to portal requirements + dates.
5. **Build** (`06-build/`) — agentically generated code + eval harness, with human-review checkpoints logged.

## D. Time-sensitive triggers (deadlines drive everything)

| Trigger | Date | Action |
|---|---|---|
| **Go/No-Go decision** | **by 7 Jul 2026** | Apply §7 conditions; if go, start Phase 2 immediately. |
| **Register + initial submission** | **9 Jul 2026** | Must register and submit the idea. ~13 days out from this screening — Phase 2 has to kick off within ~days of a "go." |
| **Shortlist (est.)** | mid-Jul (TBC) | If shortlisted, integrate sandbox APIs/data at checkpoint 3. |
| **Final prototype** | **31 Jul 2026** | Working prototype + deliverables package locked. |
| **Grand Finale** | **21 Aug 2026** | Pitch; rewards/PoC follow. |

**Critical path:** the 9 Jul registration/idea deadline is the binding trigger. A "go" must happen by ~7 Jul or the opportunity closes for this cycle.
