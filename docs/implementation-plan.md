# Implementation Plan — MSME Financial Health Scoring Platform (CreditPulse MVP)

**Status:** Implementation plan · **Date:** 01 Jul 2026 · **Owner:** Lambdac
**Target:** IDBI Innovate 2026, PS3 — Financial Health Score · **Submission:** 09 Jul 2026 (stage-1 working prototype)
**Reads with:** [`solution-design.md`](solution-design.md) (the pillars/scoring spec this plan builds on), [`appendix-a-data-source-catalog.md`](appendix-a-data-source-catalog.md), [`appendix-b-synthetic-data-plan.md`](appendix-b-synthetic-data-plan.md), [`cag-gst-feature-analysis.md`](cag-gst-feature-analysis.md), [`deployment-runbook.md`](deployment-runbook.md)

**This document, together with its two appendices, is the direct build spec.** Nothing in Sprints 1-4 (§7) should require re-deriving a decision already made here.

---

## 1. Synthesized understanding

### 1.1 The problem, restated precisely

Banks (IDBI) can't assess a large share of MSMEs for credit because traditional underwriting requires audited financials that New-to-Credit (NTC) and New-to-Bank (NTB) enterprises don't reliably produce. This is not a data-*absence* problem — it's a data-*fragmentation* problem: every operating business leaves a wide electronic trail (tax filings, payments, statutory contributions, utility consumption, logistics movements, licences, marketplace activity, legal record) that today sits in disconnected systems no single underwriting process reads together. CreditPulse's thesis: **fuse that trail into a multidimensional, explainable Financial Health Card**, near-real-time, so a credit officer can onboard a viable but credit-invisible MSME instead of auto-rejecting it, while giving the bank a *harder-to-manipulate* signal than any single document a borrower could fabricate.

The second IDBI orientation session made one thing explicit that the first did not: **GST/UPI/AA/EPFO are the floor, not the ceiling.** Evaluation rewards *awareness of the broader digital footprint*, *practicality of integration*, and — the part most entries will skip — *synthesis of multiple sources into composite signals that are harder to fake than any one input*. §2 (and Appendix A in full) is this plan's answer to that bar; it is not optional scope, it is the differentiator.

### 1.2 What already exists and what this plan adds

`solution-design.md` (28 Jun) already locked five scoring pillars — Cash-flow health, Revenue quality & GST discipline, Consistency & integrity, Obligations & leverage, Stability & vintage — a WOE/IV-scorecard-first model philosophy, an explainability contract (reason codes, SHAP), and a Financial Health Card UI concept. `cag-gst-feature-analysis.md` independently mined two CAG (Comptroller & Auditor General of India) audit reports on GST department oversight (Report No. 7/2024 "DORF Phase I", Report No. 25/2025 "DORF Phase II", covering FY2017-21) and produced a vetted, *borrower-health-reframed* feature backlog — critically, one that also flags which of those signals GSTN has since automated away (Rule 36(4) ITC capping, GSTR-2B auto-draft, §16(5) retro-legalisation, sequential filing, e-invoicing expansion), so this plan does not resurrect indicators that no longer discriminate. Earlier sourcing research established the honest access-reality map for the four obvious rails (AA carries bank-deposit + GST + NPS live; **EPF is not live on AA**, UPI has no FI type of its own and must be parsed from bank narration or modelled as a separate PG-style feed).

This plan's job is to (a) widen the source catalog per the orientation steer (§2 / Appendix A), (b) design the cross-source composite layer that synthesis actually requires (§2, §5), (c) turn all of it into a concrete, buildable architecture, sprint plan, and demo experience the remaining ~8 days can execute (§3, §5-8), and (d) say plainly what's uncertain (§9).

### 1.3 Source attribution for domain/ML grounding

- **Credit-scoring methodology**: World Bank, *Credit Scoring Approaches Guidelines* (scorecard/WOE-IV framework, fair-lending practice).
- **Transaction-level MSME scoring precedent**: *A Credit Scoring System Using Transaction-Level Behavioral Data for MSMEs* (published research).
- **GST-specific borrower-health signal mining**: CAG Report No. 7 of 2024 and Report No. 25 of 2025 (public audit reports, cag.gov.in), reframed via `cag-gst-feature-analysis.md` (own analysis).
- **AA/UPI/EPFO access reality**: ReBIT AA specifications (specifications.rebit.org.in), Sahamati AA impact reports (adoption/volume stats), EPFO ECR v2 structure documentation (epfindia.gov.in).
- **Widened data-source catalog and MSME distribution stats**: Appendix A and Appendix B respectively, each individually citation-tagged `(sourced: ...)` / `(assumed: ...)`.
- **Product framing (confidence score, graph/GNN, descriptive-vs-predictive model split)**: internal product-framing notes, treated as design ideas, not external citations.

---

## 2. Data-source catalog & composite indicators — summary (full detail: Appendix A)

Appendix A applies a fixed 12-field source-evaluation rubric to **34 candidates** — the 5 already-covered sources (GST, UPI, AA bank/deposit, EPFO, Bureau) plus a widened 29-candidate sweep across statutory, trade/logistics, utilities/premises, licensing, commerce, and risk/legal areas. The result: **8 Retain-core, 18 Retain-enrichment, 8 Reject**, with every reject carrying a documented reason and eight tier assignments overridden from the initial screening tiers once access-reality research confirmed the real 2026 picture (most notably: ONDC downgraded Core→Reject as still pilot-stage with only ~9 network participants and 3 lenders live; MCA21, DISCOM electricity, and DGFT/ICEGATE downgraded Core→Enrichment as real-but-access-constrained; telecom, ESIC, and commercial LPG downgraded to Reject as having no viable third-party access model today). It closes with a **13-entry composite-indicator catalog** (the flagship pre-existing Turnover-Authenticity Score, plus Energy Intensity, Estimated Production Capacity, Logistics-Activity Index, Premises Authenticity, Business Continuity, Operational Stability, Supply-Chain Consistency, B2G Credibility, Export Orientation, Legal-Risk Overlay, Formal-Identity Integrity, and Credit-Exposure Cross-Check) — each entry naming its constituent sources, the fused signal, and exactly which independently-governed systems a fraudster would need to compromise simultaneously to fake it. One notable finding worth carrying into the pitch: **IDBI Bank is already a live lending partner on GeM Sahay**, so the B2G-Credibility composite extends an integration IDBI already has, not a hypothetical.

**This plan's synthetic-data generator (Appendix B) and feature-engineering layer (§5.2) implement every Retain-tier source from Appendix A — not just the original four.** Where Appendix A tiers a candidate Reject, it is excluded from the build entirely (not silently modeled) — the point of the rubric is that omission is a documented judgment, not an oversight.

---

## 3. Repo and module structure

Single repo, single Cloud-Run-deployable container, internally split into frontend / backend / ML modules. Lives inside this existing repo, alongside `docs/`:

```
app/
  frontend/                Streamlit multipage app (the demo surface)
    Home.py                 entry point: scenario picker + "Run Assessment"
    pages/
      1_Dashboard.py         summary cards (score, grade, risk category, suggested limit, PD, confidence)
      2_Pipeline.py           the staged-reveal pipeline visualization (§6)
      3_Financial_Health_Card.py   final scorecard screen
      4_Explainability.py    SHAP / reason-code views
      5_Architecture.py      static architecture diagram for judges
    components/              reusable Streamlit components (stage_card.py, radar_chart.py, execution_log.py)
    static/custom.css        banking-grade styling (white/light-gray/deep-blue, green/amber/red-only-for-risk)

  backend/
    services/
      pipeline_orchestrator.py   drives the staged pipeline state machine consumed by frontend/pages/2
      scoring_service.py          calls into ml/ and assembles the Health Card payload
    schemas/                pydantic models: Entity, SourceRecord, PillarScore, HealthCard, ReasonCode

  ml/
    features/
      per-source feature modules (one per Retain-tier source in Appendix A, e.g. gst_features.py,
        bank_features.py, epfo_features.py, ewaybill_features.py, electricity_features.py, ...)
      composite_features.py    the cross-source synthesis layer (§5.2) — consumes per-source features,
        emits composite indicators from Appendix A's composite catalog
      turnover_authenticity.py  the differentiator sub-module (GST↔bank, GSTR-1↔3B, GSTR-3B↔e-way-bill,
        GSTR-3B↔TDS/TCS), per cag-gst-feature-analysis.md §6
    models/
      scorecard.py             WOE/IV logistic scorecard
      gbm.py                   monotonic-constrained LightGBM
      clustering.py            K-Means / GMM segmentation
      confidence_score.py       data-completeness confidence score (§5.3)
    explainability/            SHAP wrappers, reason-code templating, stability checks
    eval/                      metrics.py (AUC/Gini/KS), holdout.py (leakage-resistant split), psi.py

  data_gen/
    generators/               one generator per Retain-tier source (mirrors ml/features/ 1:1)
    scenarios.py              the 6 named archetypes (Textile Manufacturer, Retail Kirana, Restaurant,
                              IT Services, Auto Components Supplier, Logistics) + randomizable profiles
    distributions.py          MSME distribution profile from Appendix B (turnover/sector/geography weights)
    profiles.py               health/fraud injection (healthy / stressed / inflated-turnover), with
                              ground-truth labels for the eval harness

  data/                       checked-in synthetic CSVs (gst.csv, bank.csv, epfo.csv, bureau.csv, plus one
                              file per widened retained source, msme_master.csv)
  config/                     scoring_config.yaml (pillar weights, bands), feature_config.yaml (which
                              features are active — the human-owned "which features and why" artifact)
  tests/                      unit tests per ml/ module + one end-to-end pipeline test

Dockerfile                    single-stage Python image; CMD streamlit run app/frontend/Home.py
                              --server.port=$PORT --server.address=0.0.0.0
requirements.txt              pinned versions (supply-chain hygiene)
Makefile                      make demo / make test / make data-gen
START_HERE.md                 root — orientation doc for anyone reading this repo for the first time
README.md                     root — the public-facing submission README
.github/workflows/ci.yml       lint + unit tests + build the Docker image on every push
```

**Module boundaries**: `frontend/` never computes anything — it only renders state produced by `backend/services`. `backend/` never implements a model — it calls `ml/`. `ml/` has no Streamlit or FastAPI import — it is pure Python/pandas/sklearn/LightGBM, independently testable and reusable if a stage-2 FastAPI adapter is added later. This mirrors the "clear separation of feature engineering, cross-source synthesis, model training/inference, and scoring aggregation" requirement directly.

---

## 4. Synthetic data generation plan — summary (full detail: Appendix B)

Appendix B specifies, for **every Retain-tier source in Appendix A** (not only GST/UPI/AA/EPFO): a generator design, the distributional parameters it samples from (each tagged sourced/assumed against the MSME Distribution Profile for India), and a short "pitch narrative" paragraph arguing the source's real-world production accessibility — because although the integration itself is synthetic for the hackathon, the catalog's credibility depends on every retained source being realistically obtainable in a real deployment, not just plausible in a demo.

Cross-source consistency is enforced at generation time via `data_gen/profiles.py`: a given synthetic MSME's electricity, EPFO, and factory-licence records are drawn from the *same* underlying "true" production-capacity latent variable (not independently randomized), so the composite indicators in §2/Appendix A are meaningful rather than coincidental — this is what makes the Pipeline's cross-source-synthesis stage (§6) demonstrate a real signal instead of a scripted illusion. Six named archetypes (Textile Manufacturer, Retail Kirana Store, Restaurant, IT Services Company, Auto Components Supplier, Logistics Business) anchor the demo, plus a randomizable generator for variety across repeated demo runs.

---

## 5. ML architecture and model design

### 5.1 Pipeline overview

```
Per-source synthetic data (data_gen/)
        ↓
Per-source feature engineering (ml/features/*.py)          — one module per Retain-tier source
        ↓
Cross-source synthesis layer (ml/features/composite_features.py)   — Appendix A's composite catalog
        ↓                                              + Turnover-Authenticity sub-module
Pillar aggregation (5 pillars, per solution-design.md §4, enriched with the CAG feature backlog
        and the new composite indicators feeding Pillar 3 "Consistency & integrity")
        ↓
   ┌────┴─────────────────┐
   ↓                      ↓
Clustering            Scoring models
(K-Means/GMM)          (WOE/IV scorecard + monotonic LightGBM)
   ↓                      ↓
Peer-segment label    Pillar scores (0-100) + composite score + 1-10 grade + confidence score
   └──────────┬───────────┘
              ↓
      Explainability (SHAP / reason codes)
              ↓
      Financial Health Card payload
```

### 5.2 Cross-source synthesis layer (the required first-class layer)

`ml/features/composite_features.py` implements every composite from Appendix A's synthesis pass as a pure function of already-computed per-source features — never re-reading raw source data directly, so the layer stays testable in isolation. Each composite function returns both a **value** and a **manipulation-resistance rationale string** (surfaced later in reason codes: e.g. "Energy intensity consistent with declared GST turnover — a fraudulent turnover claim would require also faking metered electricity consumption"). This is the mechanism that answers the brief's "combine sources into signals more predictive/harder-to-fake than any single source" requirement directly in code, not just in the pitch deck.

The pre-existing **Turnover-Authenticity Score** (`turnover_authenticity.py`, from `cag-gst-feature-analysis.md` §6: GST↔bank, GSTR-1↔3B, GSTR-3B↔e-way-bill, GSTR-3B↔TDS/TCS) is the headline composite and stays a dedicated module given its differentiation weight; the newer composites (premises-authenticity, business-continuity) feed into the same Pillar 3 bucket as secondary sub-signals rather than becoming a 6th pillar — keeps the pillar count stable and matches solution-design.md.

### 5.3 Dimension naming — reconciling solution-design.md's pillars with the brief's mandated vocabulary

The brief requires the Health Card to show, at minimum, four named dimensions — **creditworthiness, growth trajectory, repayment capacity, risk profile** — plus at least one authenticity/verification signal. `solution-design.md`'s five pillars were named and engineered before that requirement existed; rather than re-architecting them, this plan **relabels/maps them 1:1** onto the brief's vocabulary (a presentation-layer decision, not a re-engineering one), and keeps the 5th pillar as an explicitly-encouraged additional dimension:

| solution-design.md pillar (engineering name, unchanged) | Health Card label (brief-mandated vocabulary) | Why this mapping |
|---|---|---|
| Cash-flow health | **Repayment Capacity** | Avg balance, volatility, low-balance frequency, net-flow trend directly measure ability to service debt — the literal meaning of repayment capacity |
| Revenue quality & GST discipline | **Growth Trajectory** | Turnover level/YoY trend/seasonality-adjusted growth, composition-threshold-crossing flags — growth-oriented by construction |
| Obligations & leverage | **Creditworthiness** | DSCR, FOIR, bounce/NACH behaviour, bureau delinquency — the classic "can and will this business meet its obligations" framing |
| Consistency & integrity | **Risk Profile** | This is also where the required authenticity/verification signal lives: the **Turnover-Authenticity Score** (§5.2) feeds Risk Profile as an explicit feature layer — the brief's own second option ("as an explicit feature layer feeding risk profile") rather than a 6th standalone dimension, because it keeps the pillar count stable and avoids double-counting the same underlying cross-checks in two places |
| Stability & vintage | **Stability & Vintage** *(kept as-is)* | An additional dimension beyond the mandated 4, retained because business age / banking-relationship length / EPFO workforce stability is a distinct, bank-meaningful going-concern signal not covered by the other four — exactly what the brief calls "additional dimensions... encouraged if they strengthen the demo" |

The Financial Health Card therefore ships **5 dimension scores using this labeling**, plus the composite score, 1-10 grade, and the data-completeness confidence score (§5.4) as separate, non-pillar outputs. `ml/` code keeps the original solution-design.md pillar names internally (feature modules, config keys) — only `frontend/` and `backend/schemas/` use the brief-facing labels — so this is purely a display-layer mapping, applied once in `backend/schemas/HealthCard`.

### 5.4 Scoring models

| Component | Choice | Why |
|---|---|---|
| Pillar/composite scorecard | **WOE/IV logistic regression** (per bin-transformed features) | Interpretable-by-construction backbone; every point contribution is natively explainable — no post-hoc approximation needed for the primary decision path |
| Lift model | **Monotonic-constrained LightGBM** (preferred over XGBoost for faster iteration in the remaining days; monotonic constraints keep it bank-defensible — e.g. score must not *improve* as bounce frequency increases) | Optional ensemble on top of the scorecard for ranking lift; SHAP explains it when active |
| Segmentation | **K-Means** (k=3-5, chosen via silhouette score), optional **Gaussian Mixture** for soft cluster membership | Descriptive peer-grouping / archetype narrative for the UI's "who is this business like" moment — explicitly *not* part of the credit decision path, to avoid conflating descriptive and predictive outputs |
| Data-completeness confidence score | New: `ml/models/confidence_score.py` — weighted by (source coverage present for this MSME) × (that source's per-feature information value) | States *how thin the file is*, so a thin-file MSME gets a hedged score instead of an auto-reject. Ships as a 6th first-class output alongside the 5 pillar scores and composite score — not folded into any pillar, so it can be surfaced on the Health Card independently ("Score: 78/100, Confidence: Medium — 6 of 9 available sources connected") |
| Cross-source synthesis | Deterministic ratio/consistency functions (pandas/Polars) — **not** a graph neural network | A graph/GNN entity-linkage layer is a real future direction but explicitly deferred to stage-2/future-work: it needs credible synthetic entity-linkage data (promoters/suppliers/buyers) this timeline can't build and validate defensibly in 8 days |
| Authenticity/verification signal (required by brief) | Turnover-Authenticity Score (§5.2) | Sufficient on its own to satisfy the brief's "at least one authenticity/verification signal" requirement; it is the single most differentiated piece of this build and is protected scope — never cut under schedule pressure |

**Output contract** (the Financial Health Card payload): 5 dimension scores (0-100, labeled per §5.3 — Repayment Capacity, Growth Trajectory, Creditworthiness, Risk Profile, Stability & Vintage) + composite Financial Health Score + 1-10 CMR-style grade (1=healthiest, per solution-design.md's existing banding) + data-completeness confidence score + peer-segment label (from clustering, descriptive only) + top reason codes (positive and negative) + recommendation (Approve / Approve-with-conditions / Request-more-info / Escalate / Decline, with indicative limit/tenure/band).

### 5.5 Explainability & evaluation

Unchanged from `solution-design.md` §6 and §9 — SHAP for the GBM path, native point-contributions for the scorecard, reason-code stability tested across recalibration, and a leakage-resistant holdout with AUC/Gini/KS/PSI as the eval harness's ground truth (built early in Sprint 1, never last).

---

## 6. Frontend design and animation flow

**Stack**: Streamlit + Plotly + custom CSS. Animation means a deliberately staged, timed reveal built from Streamlit's own primitives (`st.empty()` placeholders updated on a timed loop, `st.progress`, animated Plotly transitions, CSS keyframe transitions on card containers) — not a JS motion library. A user-facing "Instant mode" toggle skips straight to the final Health Card for repeated demo runs/judge Q&A; the staged version is the default first impression.

### 6.1 Demo flow (top level)

1. User opens the app → scenario picker (6 named archetypes + "Randomize").
2. User clicks **Run Assessment**.
3. The staged pipeline (6.2) plays automatically, each stage auto-advancing.
4. Financial Health Card renders (6.2, stage 9), then stays static for review/export.

### 6.2 Stage-by-stage animation spec (mandatory per the brief — every stage below must exist before frontend implementation starts)

| # | Stage | What's shown | Trigger to advance | Approx. duration |
|---|---|---|---|---|
| 1 | **Scenario lock-in** | Selected MSME card slides in (name, sector, Udyam category); execution log prints `"Loading entity: <name>..."` | Auto, on click of Run Assessment | 1.5s |
| 2 | **Data ingestion — breadth reveal** | A grid of source icons (one per Retain-tier source in Appendix A — GST, Bank/UPI, AA, EPFO, Bureau, Udyam, MCA21, e-way bill, electricity, ONDC, ...) lights up one-by-one in sequence with a checkmark + `"Loaded N records"` line in the execution console; this is the deliberate "breadth" moment the brief calls out | Auto-advance via timed loop (~250-400ms per icon) | 4-6s (scales with source count) |
| 3 | **Data integration** | Icons animate converging into a single "Entity" node (canonical schema resolution); console prints normalization steps | Auto, fixed delay after last icon lands | 2s |
| 4 | **Feature engineering** | Per-pillar counters animate incrementing (e.g. "Cash-flow features: 0→12") across 5 small progress bars | Auto, fixed delay | 2.5s |
| 5 | **Cross-source synthesis** | The differentiator moment: animated lines connect pairs of source icons into composite-indicator nodes (e.g. Electricity + GST → "Energy Intensity ✓", Property-tax + Electricity + GST-address → "Premises Authenticity ✓"), each appearing with its manipulation-resistance rationale string as a tooltip | Auto, one composite reveal per ~600ms | 3-5s |
| 6 | **Clustering** | A Plotly scatter animates points settling into 3-5 colored clusters; the current MSME's point highlights and a label appears ("Peer group: Established Manufacturing SMEs") | Auto, Plotly transition | 2.5s |
| 7 | **Scoring** | 5 pillar score bars fill from 0 to their final value with easing; composite score counts up numerically alongside | Auto, on scoring model completion | 3s |
| 8 | **Explainability** | SHAP-style waterfall bars animate in (top 3 positive, top 3 negative reasons), each with its plain-language reason code | Auto, fixed delay after scoring | 3s |
| 9 | **Financial Health Card** | Full card assembles: radar chart draws in dimension-by-dimension, score/grade/confidence badges fade in, recommendation panel slides up | Auto, final stage — stays on screen (no further auto-advance) | 2.5s reveal, then static |

Total staged runtime: **~25-30 seconds** end-to-end — long enough to read as a real pipeline, short enough not to stall a live judge demo. "Instant mode" (skip to stage 9) exists for repeat runs.

### 6.3 Visual style

Banking-grade: white background, light-gray panels, deep-blue accent, green for positive, amber for warnings, red reserved for high-risk-only, rounded cards, consistent spacing, professional typography, responsive layout, custom CSS throughout (no default Streamlit look).

---

## 7. Sprint-by-sprint breakdown (recomputed against 01-09 Jul 2026, ~8 working days)

Four sprints against the remaining runway, each ending in working, testable software — integration and testing are never deferred to the end. Definition of done for stage-1: deploy link live, public GitHub with a clean README and reproducible demo, eval scorecard green (with the synthetic-data caveat stated), Health Card rendering score + dimensions + reasons + recommendation, and the submission deck + demo recording in before 9 Jul.

### Sprint 1 — Foundations (Jul 1-3)
**Deliverables**: repo/module scaffold (§3) + Dockerfile skeleton that builds and serves a placeholder Streamlit page on Cloud Run; synthetic-data generators for every Retain-tier source in Appendix A (not just the original four); the 5-pillar + composite feature-engineering layer (§5.2); the eval harness (AUC/Gini/KS/PSI, leakage-resistant holdout) built and wired to synthetic labels.
**Acceptance/test criteria**: (a) `make data-gen` produces schema-valid CSVs for every retained source, checked by an automated schema-validation test per source; (b) `make test` runs a green unit-test suite covering every feature module and every composite-indicator function; (c) the eval harness runs end-to-end on the synthetic holdout and reports AUC/Gini/KS/PSI numbers (values need not be tuned yet — the harness existing and running is the gate, per the "evals as ground truth, built early" principle); (d) manual check: `docker build` + local run serves a page on `$PORT`.

### Sprint 2 — Scoring intelligence (Jul 4-5)
**Deliverables**: WOE/IV scorecard + monotonic LightGBM; K-Means segmentation; composite score, 1-10 grade, and onboarding bands; data-completeness confidence score; SHAP/reason-code generation with a stability check across recalibration runs.
**Acceptance/test criteria**: (a) automated tests assert scorecard output is monotonic in each engineered feature per its documented directional expectation (e.g. score must not improve as bounce frequency increases); (b) reason codes are asserted non-empty and directionally consistent (top positive/negative reasons match the sign of their underlying feature contribution) via unit test; (c) a documented manual demo script runs all 6 archetypes end-to-end and records the resulting grade/score/confidence for each, checked against the human's expectation of what a "healthy" vs. "stressed" archetype should score (sanity check, not a formal test).

### Sprint 3 — Demo experience (Jul 6-7)
**Deliverables**: full Streamlit staged-reveal UI (§6) wired end-to-end to the backend/ML layers; Financial Health Card final screen; mock AA/ULI/OCEN adapter **only if time remains after the above** (first candidate to drop under schedule pressure, per the protected cut-list below).
**Acceptance/test criteria**: (a) a documented manual demo script covering the full 9-stage animation flow (§6.2) with expected on-screen content at each stage, run by a second person unfamiliar with the internals — the "does a credit officer get it in 30 seconds" UX review; (b) an automated smoke test that exercises the Streamlit app's callable pipeline-orchestrator functions (not the UI itself) end-to-end for at least 2 archetypes without exceptions.

### Sprint 4 — Deploy & submit (Jul 8-9)
**Deliverables**: Cloud Run deployment (public URL live, per [`deployment-runbook.md`](deployment-runbook.md)); security/secrets review (no keys in repo, pinned dependencies); repo-hygiene pass; `START_HERE.md` + public `README.md`; submission deck (fixed template) + demo recording; final dry run.
**Acceptance/test criteria**: (a) the deploy link is reachable and completes a full assessment run for at least one archetype, checked manually right before submission; (b) `git secrets`/manual grep confirms no credentials committed; (c) CI (`ci.yml`) is green on the final commit; (d) the submission checklist is fully ticked.

**Protected under schedule pressure** (never cut): the eval harness, the reason codes, the GST-vs-bank Turnover-Authenticity feature. **First to cut if squeezed further**: the mock AA/ULI/OCEN adapter, then the monotonic-LightGBM lift model (scorecard alone still satisfies the brief), then the 300-900 bureau-style score analogue (the 1-10 grade alone is sufficient).

---

## 8. Deployment architecture (Google Cloud Run)

- **Container**: single image built from the repo's `Dockerfile`; `CMD streamlit run app/frontend/Home.py --server.port=$PORT --server.address=0.0.0.0`. Streamlit reads `$PORT` at runtime — Cloud Run injects it, no hardcoding.
- **Sizing**: start at **2 vCPU / 2 GiB memory** — sklearn/LightGBM/Plotly/Streamlit's footprint is modest for a single-session demo; scale up only if the live demo shows latency issues.
- **Concurrency & session affinity**: Streamlit's UI reactivity runs over a persistent WebSocket connection per browser session. Enable Cloud Run's **session affinity** and keep **concurrency modest per instance** (Cloud Run defaults to 80 — verify this is safe for a stateful Streamlit process at build time; reduce if sessions interfere with each other) so a user's pipeline animation doesn't get routed across instances mid-run.
- **Scale-to-zero vs. min-instances**: **scale-to-zero (min-instances=0)** by default for lowest cost between demo sessions; set **min-instances=1** for the actual judging window (21 Jul shortlist announcement onward, and demo day) to avoid a cold-start stall in front of judges — a small, deliberate, time-boxed cost tradeoff, not a permanent always-on instance.
- **Build/deploy path**: GitHub Actions (`ci.yml`) builds the image on push to `main`, pushes to Artifact Registry, deploys to Cloud Run — `gcloud run deploy` as the final step, gated on CI passing. No Terraform needed for a single-service MVP; a short `deploy.sh` documenting the exact `gcloud` commands is sufficient and more auditable at this scale than IaC overhead.
- **Secrets**: none required for stage-1 (no real external API keys — everything is synthetic/local). If a Bedrock/Claude-style narration call is added later, use Cloud Run's built-in Secret Manager integration, never a committed `.env`.
- **Residency**: no PII/customer data is used (synthetic only) — this removes the ap-south-1/India-residency constraint that mattered for the original AWS-native plan; any Cloud Run region is acceptable for stage-1, though `asia-south1` (Mumbai) is the natural choice for latency and optics with an Indian bank audience.
- **Verify at implementation time, not assumed here**: exact current Cloud Run WebSocket/session-affinity configuration flags and default request-timeout — these change over time; confirm against live GCP documentation during Sprint 1, not from this plan's memory.

---

## 9. Risks and open questions

| Risk / open question | Status | Handling |
|---|---|---|
| EPFO is not live on Account Aggregator rails | Known, handled | Must stay framed as mocked/roadmap in the pitch and demo narration — never presented as a live integration. |
| Synthetic-data ceiling — no real-default backtesting is possible pre-pilot | Known, handled | Stated honestly in the eval report and deck; real-default recalibration is explicitly the post-hackathon productionization step, not a stage-1 claim. |
| Cloud Run + Streamlit WebSocket behavior (session affinity, cold starts, request timeout) | Needs verification | Confirm against current GCP docs during deployment (see `deployment-runbook.md`) before treating §8's config as final. |
| Widened data sources are *catalogued and modeled synthetically*, not really integrated | By design (explicit brief instruction) | The "synthetic data only" out-of-scope constraint governs integration, not catalog breadth — Appendix A's accessibility narrative for each retained source is what argues real-world obtainability; this is intentional, not a shortcut. |
| Schedule compression (model + explainability work lands in the 2-day Sprint 2) | Real risk | Flagged explicitly in §7; the protected/cut-list ordering in §7 exists precisely to absorb this risk without touching the differentiators. |
| Real bank/core-banking integration, production-grade auth/multi-tenancy, real GST/AA API integration, HA infra | Explicitly out of scope per the brief | Not built; if any later prove necessary to reach a core objective, that would be a new open question requiring a human decision — none identified as necessary so far. |
| Graph/GNN cross-entity linkage | Deferred, not built | No credible synthetic entity-linkage data achievable in the runway with enough rigor to defend under judge questioning; noted in §5.4 as a stage-2/future-work item, not silently dropped. |

---

## 10. Track 04 — Early Warning (PS4)

**Design intent.** A portfolio early-warning model that fires on the *performing* book. The whole track is built around one thesis encoded in the data: the alt-data footprint (GST/UPI/EPFO/energy) is a *leading* indicator that deteriorates months before repayment behaviour does, so an alt-data model warns earlier than a repayment-only monitor. Anti-leakage discipline is therefore the first-class engineering concern, not an afterthought.

**Module map** (self-contained under `app/tracks/t04_early_warning/`, reusing the platform ML kit read-only):

```
data_gen/panel.py        24-month latent-driven loan/repayment/alt-data panel; repayment
                         responds to health_{t-Δ} (Δ~5-9mo) so DPD lags the alt-data sag
data_gen/build.py        build/write/ensure the four panel CSVs; reuses app.data_gen.build_dataset
                         .build_profiles so entity_ids/archetypes/latents match Track 03
        ↓
ml/features.py           build_snapshots(): per-(entity, as-of) causal features (FEATURE_COLS,
                         FEATURE_DIRECTIONS monotone table); _window() RAISES LeakageError on a
                         future-window request — the structural anti-leakage guard
ml/model.py              EWSEngine: two MonotonicGBM models on one snapshot pipeline + one band rule
ml/ews_metrics.py        lead-time distribution + capture@decile (entity-level holdout)
        ↓
service.py / ui_state.py orchestration: MonitoringRun / CaseDetail payloads (backend narrates)
        ↓
pages/portfolio_overview.py   book-level radar (deep link track04)
pages/watchlist.py            ranked watchlist + per-borrower money-chart drilldown (watchlist)
```

**Key ML choices.** `EWSEngine` fits **two models through one pipeline** so the comparison is honest: **EWS** — a monotonic-constrained LightGBM (`MonotonicGBM`, with `PostHocCalibrator`/isotonic calibration wired inside it) on the full repayment + alt-data feature set against `default_within_12m`; and the **baseline** — the same pipeline restricted to repayment-only features against `default_within_3m` (the internal SAJAG-style stand-in that can only see EMIs bounce). Both share one band rule on the calibrated PD (Red ≥ 0.30, Amber ≥ 0.10). The monotone direction table (`FEATURE_DIRECTIONS`) keeps every constraint bank-defensible (score cannot improve as bounces rise). Headline metric is **lead time** (median 11.5 vs 2.0 months = 8-month gap; capture@decile 0.926 vs 0.519 on the synthetic holdout); AUC is computed but not headlined.

**Leakage / citation integrity.** Enforced structurally, not by convention: (a) the train/holdout split is **entity-level** with an asserted-empty intersection, and demo archetypes are pinned into train so they never inflate holdout metrics; (b) every windowed feature routes through `_window()`, which raises `LeakageError` rather than serve any month past the snapshot; (c) no label-derived field is read in `features.py` at all — `default_month`/`ramp_start`/`lead_alt` live only in the labels file and are joined in a *separate* `_attach_labels()` step in `model.py`, which also drops all at/after-default snapshots. Generation is deterministic (identical `--n`/`--seed` → byte-identical CSVs).

## 11. Track 05 — Fraud Intelligence (PS5)

**Design intent.** A mule-account detection and case-assembly desk that sits *above* the network-flagging layer (RBIH MuleHunter.AI / the MHA Dec-2026 integration mandate): score accounts, then assemble explainable evidence and the surrounding ring into a reviewable case. Two design commitments drive it — an interpretable, evidence-bearing score, and a hard **citation gate** so no claim reaches a case file without a receipt.

**Module map** (self-contained under `app/tracks/t05_fraud_intelligence/`; the eval labels file is read by exactly one module):

```
data_gen/typologies.py   the 8 canonical typology names + injectors; legit.py hard negatives
data_gen/build.py        accounts.csv / transactions.csv (engine inputs) + fraud_ground_truth.csv
                         (EVAL-ONLY)
        ↓
ml/features.py           per-account AccountLedger + behavioural feature matrix
ml/typologies.py         the 8 deterministic detectors; each returns a TypologyHit carrying the
                         concrete txn_ids/counterparties/devices that triggered it (no labels)
ml/model.py              FraudEngine: typology leg ⊕ Isolation-Forest anomaly leg; expand_ring() BFS
ml/eval/fraud_metrics.py the ONLY module permitted to read fraud_ground_truth.csv
        ↓
case_orchestrator.py     5-stage agentic case: Triage→Evidence→Network→Adjudication→Case-file,
                         each a reused pipeline_orchestrator.Stage; owns all user-facing copy
        ↓
pages/fraud_desk.py           triage queue, KPIs, ring/typology distribution (track05)
pages/case_investigation.py   the five-stage case file for one account (case_investigation)
```

**Key ML choices.** `FraudEngine` blends two independent voices into a 0–100 mule-risk score: **`mule_risk = 0.55 · typology_max_blend + 0.45 · (100 · anomaly_excess)`** — an interpretable, evidence-bearing typology leg (the top-two fired detectors, 0.75/0.25) plus an **Isolation Forest** anomaly leg scored as *excess* over the clearly-genuine cohort (badness-oriented features, "normal" anchored at the 90th percentile of the zero-badness set so only true outliers rise). Bands: Alert ≥ 65, Review ≥ 45. Ring discovery is a **pure-python BFS** over shared-device and high-value-transfer edges (no networkx), with deterministic role inference (mule / recruiter / cash-out) from observable ledger behaviour. The case orchestrator is *agentic-deterministic*: orchestrated specialist stages with a human approve/override gate and **no runtime LLM** (an LLM narrative layer is disclosed as an optional pilot step only).

**Leakage / citation integrity.** The differentiator is enforced at construction: a `Ground` (a ground of suspicion) **raises `CitationError` if its `txn_ids` is empty**, so an uncited claim can never reach a case file — a detector that fires without usable evidence degrades to an explicit "insufficient evidence" note. The detector and the generator's injector **share no code path** (the detector recovers each pattern from raw rows). Ring roles are *inferred*, never read from labels; and `fraud_ground_truth.csv` is read *only* in `ml/eval/fraud_metrics.py`, never by the engine, features, typologies or orchestrator at score time. Synthetic-holdout scorecard: **6/6 rings recovered** (caught = ≥60% of members flagged), recall@alert 1.0, precision@alert 0.744 with precision_ring@alert 1.0 (the misses are ring-associated infrastructure), and 0/10 hard-negative false positives (the explainably-cleared high-velocity gig worker).
