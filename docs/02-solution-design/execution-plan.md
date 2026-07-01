# Execution Plan — MSME Financial Health Scoring Platform Implementation Deliverable

**Status:** Phase 2 execution plan · **Date:** 01 Jul 2026 · **Owner:** Lambdac
**Executes:** [`../bootstrap-prompt-v3`](../bootstrap-prompt-v3) (the AGENT PROMPT this plan was written against)
**Reads with:** [`solution-design.md`](solution-design.md) (spec), [`agentic-execution-plan.md`](agentic-execution-plan.md) (§1,4-7 still valid; §3 schedule superseded by §7 below), [`data-and-intel-sourcing-guide.md`](data-and-intel-sourcing-guide.md), [`intel-cag-gst-feature-analysis.md`](intel-cag-gst-feature-analysis.md), [`../notes/product-framework-notes`](../notes/product-framework-notes), [`../notes/demo-architecture.md`](../notes/demo-architecture.md), [`../../.claude/skills/idbi-hackathon/SKILL.md`](../../.claude/skills/idbi-hackathon/SKILL.md)

---

## Context

This repo (`/home/os/ideaspace/idbi`) is Lambdac's workspace for IDBI Innovate 2026, PS3 (MSME Financial Health Card). The repo already contains a mature Phase-2 spec ("CreditPulse": `docs/02-solution-design/solution-design.md`), deep CAG GST feature research, a data-sourcing reality guide, and a reusable data-source-evaluation rubric (`.claude/skills/idbi-hackathon/SKILL.md`). What's missing — and what the current AGENT PROMPT (stored verbatim in the repo as `docs/bootstrap-prompt-v3`) asks for — is the deliverable that the second IDBI orientation session made newly mandatory: a **widened, justified data-source catalog beyond the obvious four (GST/UPI/AA/EPFO)**, the **composite cross-source indicators** it enables, and a concrete, dated **implementation plan** development agents can build from directly.

Today is **2026-07-01**. The original build schedule (`agentic-execution-plan.md`) assumed a 28-Jun start; zero application code exists yet, so the sprint plan must be recomputed against the **~8 working days actually left** (Jul 1–9) rather than restarted from a hypothetical day 0. The founder go/no-go in `docs/01-decision/DECISION-pending.md` is also still marked PENDING — this plan proceeds on a "go" assumption but must surface this rather than silently assume it.

Three architecture questions that had conflicting answers across existing docs were resolved directly with the user:
1. **Deployment**: GCP **Cloud Run**, single container, internally split into frontend/backend/ML modules (supersedes solution-design.md's AWS-native section and demo-architecture.md's GCE-VM idea).
2. **Frontend**: **Streamlit + Plotly + custom CSS**, staged reveal — animation as a deliberately engineered demo experience using Streamlit's own toolkit, not a React rewrite (confirms demo-architecture.md's Python-first choice; overrides only its "minimal animations" framing).
3. **Repo**: the buildable app code goes **inside this same repo**, alongside the existing `docs/` tree (not a fresh repo) — with a repo-hygiene risk flagged for later (see Risks).

The output of this task is **documentation, not application code**: a markdown implementation plan (plus two appendices) that itself becomes the spec development agents build the actual platform from in a later phase.

## Deliverable structure

Three files under the existing numbered-folder convention (`docs/02-solution-design/`), extending rather than replacing `solution-design.md`:

| File | Content | Maps to brief's numbered sections |
|---|---|---|
| `docs/02-solution-design/implementation-plan.md` (master) | Domain/source synthesis, repo/module structure, ML architecture, frontend+animation spec, sprint plan, deployment, risks | 1, 3, 5, 6, 7, 8, 9 (2 and 4 get a summary + link-out) |
| `docs/02-solution-design/appendix-a-data-source-catalog.md` | Full prioritized data-source catalog (rubric table, all tiers, rejects+reasons) + composite-indicator catalog | 2, in full |
| `docs/02-solution-design/appendix-b-synthetic-data-plan.md` | Per-source generator spec, MSME distribution profile (sourced vs. assumed), per-source accessibility narrative | 4, in full |

Add one banner line at the top of `docs/02-solution-design/agentic-execution-plan.md` noting its §3 day-by-day schedule is superseded by the new sprint plan (§1, §4-7 remain valid) — preserves audit trail rather than deleting history, consistent with this repo's existing pattern of PENDING/superseded banners.

Do **not** create `START_HERE.md`/`README.md`/the actual `app/` code tree yet — those are Sprint deliverables for a later implementation phase, not this planning deliverable.

## Execution sequence

**Direct synthesis (no research needed — draft from material already gathered):**
- Domain/source synthesis (§1), repo/module structure (§3), ML architecture (§5), frontend/animation spec (§6), sprint plan (§7), deployment architecture (§8), risks (§9) — all synthesized from `solution-design.md`, `intel-cag-gst-feature-analysis.md`, `data-and-intel-sourcing-guide.md`, `product-framework-notes`, `demo-architecture.md`, `agentic-execution-plan.md`, and the SKILL.md rubric, per the content blueprints below.

**Delegated research (run as parallel agent calls, merge after):**
1. **Data-source catalog** (§2 / Appendix A): brief a research agent to take the 29-candidate seed list below and run **Steps 2–4 of the `idbi-hackathon` SKILL** (fetch it via the Skill tool rather than re-deriving the rubric) — score each candidate on the 12-field rubric, tier into Retain-core/Retain-enrichment/Reject, then do the composite-indicator synthesis pass. It should use web research to firm up the ~12 candidates flagged "needs research" below (e.g., e-way bill third-party access model, FASTag/IHMCL licensing, DISCOM smart-meter API coverage, MCA21 V3 API terms, ONDC/GeM data-sharing model, telecom alt-data partnerships).
2. **MSME distribution profile** (§4 / Appendix B): brief a research agent to gather India MSME distribution stats (Udyam dashboard, NSS 73rd Round, ASI factory census, PLFS wages, RBI MSME credit-gap reports, GSTN annual report turnover-band distribution) with every figure tagged `(sourced: citation)` or `(assumed)` — same discipline as the existing CAG-analysis doc.

Kick off both research threads first (longest poles), do direct-synthesis sections while waiting, then merge everything into the 3 files. Do a final consistency read-through before considering the deliverable done.

## Content blueprint: data-source catalog seed list (starting point for research)

29 candidates across the SKILL.md's 7 areas + ONDC/GeM (from `product-framework-notes`). Legend: Tier C=core, E=enrichment, R=reject; Research Y=needs web verification, N=domain knowledge sufficient.

| # | Source | Area | Tier | Research | Rationale |
|---|---|---|---|---|---|
| 1 | Udyam Registration | Statutory | C | N | Identity/segment anchor, near-universal |
| 2 | PAN/GSTIN verification (Protean/NSDL) | Statutory | C | N | KYC anchor, low-cost API |
| 3 | MCA21 (directors/beneficial ownership/charges) | Statutory | C | Y | Graph-layer linkage; verify API/bulk terms |
| 4 | ESIC contributions | Statutory | E | Y | Payroll-adjacent to EPFO |
| 5 | ITR/AIS/Form 26AS (consent) | Statutory | E | Y | Powerful, not yet on AA rails — verify |
| 6 | E-way bill (NIC EWB) | Logistics | C | Y | Already central to Turnover-Authenticity |
| 7 | FASTag/NHAI toll (IHMCL) | Logistics | E | Y | Logistics proxy; verify aggregator API |
| 8 | Vahan/Parivahan vehicle registration | Logistics | E | N | Public API; asset/capacity signal |
| 9 | DGFT/IEC + ICEGATE shipping bills | Logistics | E | Y | Export-sector-conditional |
| 10 | Customs Bill-of-Entry | Logistics | R | N | Narrow applicability — fold into #9 |
| 11 | Electricity (DISCOM billing/smart meter) | Utilities | C | Y | Energy-intensity/production-capacity composite driver |
| 12 | Water utility billing | Utilities | R | N | Patchy digitization, weak marginal signal |
| 13 | Commercial LPG | Utilities | E | N | Sector-conditional (F&B/mfg) production proxy |
| 14 | Property tax (municipal) | Premises | E | Y | Premises-authenticity composite; coverage varies by city |
| 15 | Commercial lease/rent registration | Premises | R | N | Widely informal/unregistered |
| 16 | Telecom (mobile/broadband tenure/usage) | Premises | E | Y | Continuity proxy |
| 17 | FSSAI licence | Licensing | E | N | Sector-conditional, public licence search |
| 18 | Factory licence | Licensing | E | N | Production-capacity composite constituent |
| 19 | Pollution Control Board consent | Licensing | E | N | Sector-conditional (manufacturing) |
| 20 | Shops & Establishment registration | Licensing | E | N | Vintage/identity anchor |
| 21 | ONDC seller/network data | Commerce | C | Y | Explicit brief ask; verify lender-facing data-sharing model |
| 22 | GeM seller transaction history | Commerce | E | Y | B2G revenue read; niche |
| 23 | POS/QR acceptance | Commerce | E | N | Sub-item of UPI/PG, not new core |
| 24 | E-commerce marketplace seller dashboards | Commerce | E | Y | Proprietary/consent-gated |
| 25 | Insurance (policy/claims) | Risk/legal | E | N | Asset-base proxy |
| 26 | Court records (e-Courts/NJDG) | Risk/legal | E | N | Public, manipulation-resistant, litigation flag |
| 27 | Insolvency/IBC (NCLT/IBBI) | Risk/legal | E | N | Public, strong negative flag |
| 28 | Govt procurement/tenders (CPPP) | Risk/legal | E | N | Overlaps GeM; independent credibility signal |
| 29 | Satellite/geospatial | Geospatial | R | N | Impractical at MSME-unit resolution in this timeline |

**Composite catalog** to build in §2 (extend SKILL.md's 7 starters): energy-intensity (11+GST), production-capacity (11+EPFO+18), premises-authenticity (14+11+GST-address), business-continuity (16+AA+UPI), B2G-credibility (22+28), export-orientation (9+GST), legal-risk-overlay (26+27 on promoter PAN).

## Content blueprint: ML architecture

| Layer | Choice | Rationale |
|---|---|---|
| Clustering | K-Means (k=3-5 via silhouette), optional GMM | Descriptive segmentation/archetype narrative only — never the credit decision itself |
| Cross-source synthesis | Deterministic ratio/consistency feature module (pandas/Polars) | GNN/graph-linkage (from `product-framework-notes`) explicitly deferred — too heavy for 8 days, no credible synthetic linkage data in time |
| Scorecard | WOE/IV logistic (confirmed from solution-design.md) + monotonic-constrained **LightGBM** (prefer over XGBoost for iteration speed) | Add a **data-completeness confidence score** (source-coverage × per-source IV weight) as a 6th first-class output alongside the 5 pillars — carries the "lend cautiously on partial data" narrative from `product-framework-notes` |
| Authenticity signal | Existing **Turnover-Authenticity Score** sub-module (GST↔bank, GSTR-1↔3B, GSTR-3B↔e-way-bill, GSTR-3B↔TDS/TCS) | Confirmed sufficient to satisfy the brief's authenticity-signal requirement; fold in premises-authenticity and business-continuity composites as secondary sub-signals in the same pillar |

## Content blueprint: repo/module structure (Cloud Run, single container)

```
app/
  frontend/        Streamlit multipage: Home.py + pages/ (Dashboard, Synthetic MSME, Pipeline,
                    Financial Health Card, Explainability, Architecture) + components/ + static/custom.css
  backend/         services/ (scoring_service.py, pipeline_orchestrator.py), schemas/ (pydantic)
  ml/              features/ (per-source + composite_features.py + turnover_authenticity.py),
                    models/ (scorecard.py, gbm.py, clustering.py, confidence_score.py),
                    explainability/, eval/ (metrics.py, holdout.py, psi.py)
  data_gen/        one generator per retained source + scenarios.py (6 archetypes) + distributions.py
  data/            checked-in synthetic CSVs
  config/          scoring_config.yaml, feature_config.yaml
  tests/
Dockerfile          CMD streamlit run app/frontend/Home.py --server.port=$PORT
requirements.txt    pinned versions
Makefile            make demo / make test / make data-gen
START_HERE.md        root, framed "for a human or agent" — replaces AGENTS.md
README.md            root — public submission README
.github/workflows/ci.yml
```

Deployment notes to include in §8: Cloud Run must receive traffic on `$PORT`; Streamlit's WebSocket reactivity needs **session affinity enabled** and works best with **min-instances=1 during demo/judging windows** (trading small always-on cost for avoiding a cold-start stall mid-demo), scale-to-zero otherwise for cost; size around 2 vCPU / 2GiB as a starting point (sklearn/LightGBM/Plotly footprint is modest). Flag these as defaults to confirm against current Cloud Run docs at implementation time, not as verified facts.

## Content blueprint: sprint plan (recomputed against Jul 1–9, ~8 working days)

Replaces only §3 (the day-by-day table) of `agentic-execution-plan.md`; its §1 operating model, §4 toolchain (update AWS→GCP/Cloud Run, Next.js→Streamlit-only), §5 stage-2 plan, §6 risk controls, §7 definition-of-done remain valid and should be referenced, not restated. Consolidated to **4 sprints** (folding the original G0-G7 gates together under time pressure):

| Sprint | Days | Deliverables | Merged gates |
|---|---|---|---|
| **Sprint 1** | Jul 1-3 | Repo/module scaffold + Dockerfile skeleton; synthetic-data generators for every retained source; 5-pillar + composite features; eval harness (AUC/Gini/KS/PSI, leakage-resistant holdout) | G0+G1: schema/synthetic-data realism + feature list/eval design sign-off |
| **Sprint 2** | Jul 4-5 | WOE/IV scorecard + monotonic LightGBM; K-Means segmentation; composite score/1-10 grade/bands; SHAP/reason codes | G2+G3: model/calibration/banding + reason-code defensibility |
| **Sprint 3** | Jul 6-7 | Streamlit staged-reveal UI end-to-end; Financial Health Card; mock AA/ULI adapter only if time allows | G4(+G5 optional): "credit officer gets it in 30s" UX review |
| **Sprint 4** | Jul 8-9 | Cloud Run deploy, security/secrets review, repo-hygiene pass, START_HERE.md/README, PPT, demo recording, submit | G6+G7: security + final submission review |

Each sprint's deliverable list in the final doc must specify concrete acceptance/test criteria per the brief (e.g., Sprint 1: eval harness runs green on synthetic holdout + generators produce schema-valid output for every retained source, verified by an automated test; Sprint 3: manual demo script with expected screen-by-screen outputs). Flag in §9 that compressing G2+G3 into 2 days is the biggest schedule risk, and that the mock AA/ULI/OCEN adapter is the first thing to drop if squeezed further (consistent with the original cut-list, which never protected it — only the eval harness, reason codes, and GST-vs-bank consistency feature are protected).

## Risks / open questions to surface in §9 (do not silently resolve)

- Founder go/no-go (`DECISION-pending.md`) is still PENDING — this plan assumes "go."
- Repo hygiene: `docs/bootstrap-prompt*`, `docs/00-screening/*`, `docs/01-decision/*` read as internal strategy artifacts and will be visible in the public submission repo since the user chose to build in this same repo — needs an explicit human decision (relocate under `internal/`, exclude via a submission branch, or accept as-is) before Jul 9.
- EPFO is not live on AA rails — must stay framed as mocked/roadmap in the pitch, never presented as live.
- Synthetic-data ceiling — real-default backtesting is a post-hackathon productionization step, not something this MVP can prove; state this honestly rather than over-claiming accuracy.
- Cloud Run + Streamlit WebSocket behavior (session affinity, cold starts) should be confirmed against current GCP docs at implementation time.

## Verification

Since this task's output is documentation, not running code, verify completeness rather than runtime behavior:
1. Confirm all three files exist and every one of the brief's 9 numbered sections is covered (directly in the master doc or via a clear link-out to an appendix).
2. Confirm the data-source catalog appendix actually followed the SKILL.md's 4-step procedure (enumerate → score all 12 fields per candidate → tier with rejection reasons → composite synthesis pass) rather than skipping steps.
3. Confirm every MSME-distribution figure in Appendix B is tagged `(sourced: citation)` or `(assumed)` — no bare unsourced numbers.
4. Confirm the sprint plan's dates are internally consistent with "today = 2026-07-01, submission = 2026-07-09" and that `agentic-execution-plan.md` carries the superseded-banner rather than being silently overwritten.
5. Read the three new files back top-to-bottom for cross-reference consistency (e.g., pillar names match between solution-design.md, the ML architecture section, and the Financial Health Card frontend spec).
