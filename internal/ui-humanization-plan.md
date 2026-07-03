# UI Humanization — Review & Implementation Plan

**Source**: `internal/issues` (02 Jul 2026) · **Status**: ready for pickup · **Target branch**: `ui-review`
**Audience for the UI**: bank ops / management-level users (credit officers, judges at IDBI Innovate). Not data scientists.

This doc is (1) a review of where the current UI falls short of the four issues, with exact file/line evidence, and (2) five self-contained work packages (WP-A … WP-E) an agent can pick up independently. Read §Guardrails and §Copy Bank before starting any WP.

---

## 1 · The four issues, restated

| # | Issue (paraphrased from `internal/issues`) |
|---|---|
| 1 | Every prediction must carry its **rationale/inference in plain language** — a number alone is not meaningful to a human audience. |
| 2 | The pipeline animation is good, but completed stages collapse to bare `title · Completed` rows. Each stage should leave behind a **notebook-style record** — plot + findings + inference — via a details/expand affordance. Explicitly **not console logs**; must read as human-friendly analysis for bank ops/management. |
| 3 | A **Simple / Technical view toggle**, so fixing 1–2 doesn't suffocate non-technical users. |
| 4 | **Across all pages**: more analysis rationale without clutter — info icons / tooltips. |

## 2 · Review — current state vs. each issue

### Issue 1 — predictions lack attached rationale
- Headline numbers render as bare KPI cards: `pages/1_Dashboard.py:44-61` (score, PD, limit, authenticity, confidence, segment) and `pages/3_Financial_Health_Card.py:64-72`. Sub-text is a label ("Flagship check", "CMR-style grade 8/10"), not an inference.
- Reason codes DO exist (`render_reasons`, `components/stage.py:89`) but live in a separate section/page — the number and its "why" are visually divorced.
- There is no overall **verdict narrative** anywhere: nothing says *"This business scores 41/100 mainly because its declared turnover is not corroborated by bank inflows; the low score is a fraud signal, not a repayment-capacity signal."* That sentence is the single most persuasive artifact for the AUTO_COMPONENTS demo and it currently has to be spoken by the presenter.

### Issue 2 — stages evaporate after the animation
- `pages/2_Pipeline.py:143` uses a **single** `detail_ph = st.empty()`; each stage's `render_detail` **overwrites** the previous one (`:175`). After the run, only stage 9's detail remains (`:186`).
- The left rail (`stage_list_html`, `components/stage.py:45-58`) shows only `index · title · Completed` — exactly the "table items" screenshotted in the issue.
- The execution console (`console_html`) is by design a terminal look (`cp-console`) — the issue explicitly says the persistent record must **not** look like this. The console is good *ambience* during playback; it is not the record.
- Structured per-stage data already exists (`Stage.data`, orchestrator `:121-129`) — the fix is presentation + a plain-language findings layer, **not** new computation.

### Issue 3 — no view-mode concept
- Nothing gates technical content today. SHAP waterfall, "K-Means, k=4", "WOE scorecard", "monotonic GBM PD path", PCA axes, engineering names on dimension rows (`3_Financial_Health_Card.py:60`) all render unconditionally.

### Issue 4 — no tooltips/info affordance
- `kpi()` (`components/ui.py:47`) has no tooltip parameter. No page uses `help=` on widgets. Terms a banker will question — *PD, indicative limit, confidence band, bureau-style score, peer segment, authenticity* — have no in-place explanation.

### What is already right (don't regress)
- Module boundaries are clean: frontend renders only; all numbers come from `Stage.data` / `HealthCard`. **Keep it that way — plain-language findings are data, so they are produced in the backend orchestrator, not composed in page code.**
- The a11y pass (commit `422d81d`) added contrast-safe palette, reduced-motion, aria-live on the console, HTML-escaping of names. New components must meet the same bar.
- 124 tests green; `test_pipeline_orchestrator.py` pins stage structure via `_STAGE_DATA_KEYS` — extend, don't break.

## 3 · Design decisions (locked — WPs implement these)

- **D1 — Findings are backend data.** Extend `Stage` (orchestrator `:121`) with `headline: str` (one-sentence takeaway) and `findings: List[dict]` — each `{"text": str, "tone": "good"|"warn"|"risk"|"neutral", "technical": bool}`. Built by each `_stage_*` builder from values it already computes. `log` stays as the technical trace.
- **D2 — Notebook accumulation on the Pipeline page.** Keep the live animation area, but after each stage completes, append a **persistent cell**: `st.expander("Stage N · Title — <headline>")` containing the findings (styled callouts, not console lines) + the same `render_detail` visualization. After the run: 9 cells remain, newest expanded. The left rail keeps only progress duty; the console becomes Technical-mode-only.
- **D3 — Global Simple/Technical toggle.** In the sidebar via `page_setup()` so it's on every page; persisted in `st.session_state["cp_view_mode"]`; **default Simple**. Simple mode: no model names, no SHAP, no console, no engineering names; inferences in words. Technical mode: everything, plus the trace.
- **D4 — Info icons via one shared component.** `kpi(..., tip=...)` + an accessible CSS tooltip; all tooltip copy centralized in one glossary module so language stays consistent.
- **D5 — One verdict narrative.** A deterministic template-based `verdict(out, card)` in the orchestrator producing 2–3 plain sentences; shown on Health Card (under the recommendation banner) and as stage 9's headline. It must explicitly handle the flagship divergence case (benign PD + low authenticity).

## 4 · Work packages

Dependency order: **WP-A ∥ WP-B → WP-C → WP-D → WP-E.** A and B touch disjoint files and can run in parallel (worktree isolation if concurrent). C needs both. D needs B (and A only for the verdict). E is the closing QA pass.

---

### WP-A — Backend: stage findings + verdict narrative
**Files**: `app/backend/services/pipeline_orchestrator.py`, `app/tests/test_pipeline_orchestrator.py`.

1. Extend `Stage` with `headline: str = ""` and `findings: List[dict] = field(default_factory=list)` (shape per D1). Defaults keep existing constructors valid.
2. Each `_stage_*` builder populates both, **from values already in scope** — no new engine calls, no recomputation. Use the templates in §Copy Bank; thresholds must reuse the existing semantics of `ui.score_class` / `auth_class` / band → tone mapping (good/warn/risk), keeping color and language consistent.
3. Add `def verdict(out: Dict, card: HealthCard) -> List[str]` (module-level, testable): 2–3 sentences per §Copy Bank §CB-9, covering (a) the recommendation + score in words, (b) the dominant driver (top reason code), (c) the authenticity divergence sentence **iff** `pd < 0.05 and turnover_authenticity_score < 55` — the AUTO_COMPONENTS money-shot. Attach as stage 9's `headline`/findings and expose on the `Assessment` (e.g. `assessment.verdict: List[str]`).
4. Tests: extend `_STAGE_DATA_KEYS` runs to assert every stage has a non-empty `headline` and ≥1 finding; every finding text contains **no banned jargon when `technical=False`** (see §Guardrails G4 list); parametrized check that AUTO_COMPONENTS' verdict contains the divergence sentence and TEXTILE's does not.

**Acceptance**: all existing + new tests green; no signature changes to `run_assessment`; findings read as complete sentences (spot-check by rendering `stage.findings` for both archetypes in the test output).

---

### WP-B — Frontend components: view-mode toggle, info tooltips, glossary, CSS
**Files**: `app/frontend/components/ui.py`, `components/state.py`, new `components/glossary.py`, `static/custom.css`.

1. `state.py`: `view_mode() -> str` ("simple"|"technical") and `is_technical() -> bool` reading `st.session_state["cp_view_mode"]` (default "simple").
2. `ui.py page_setup()`: sidebar segmented control / toggle "View: Simple · Technical" bound to that key, rendered on every page under the brand block. Label it in user terms ("Show model internals"), not developer terms.
3. `ui.py kpi()`: add optional `tip: str = ""`; when set, render an info glyph after the label: `<span class='cp-info' tabindex='0' aria-label='<tip>'>ⓘ<span class='cp-tipbox'>…</span></span>`. CSS in `custom.css`: `.cp-info` subtle (opacity ~.55), `.cp-tipbox` hidden by default, shown on `:hover` **and `:focus-visible`** (keyboard reachable), max-width ~30ch, respects the existing light palette and contrast ratios. Also add `.cp-finding` callout styles (`good|warn|risk|neutral` left-border variants, distinct from `.cp-reason`) for WP-C/D.
4. New `components/glossary.py`: single `GLOSSARY: Dict[str, str]` with entries per §Copy Bank §CB-10. All tooltip copy imports from here — never inline strings in pages.

**Acceptance**: toggle appears on every page and persists across page switches within a session; tooltips keyboard-accessible; no layout shift when tips render; AppTest still renders all pages.

---

### WP-C — Pipeline page: notebook-style stage record
**Files**: `app/frontend/pages/2_Pipeline.py`, `components/stage.py`.
**Depends on**: WP-A (findings), WP-B (view mode, `.cp-finding` styles).

1. `components/stage.py`: add `render_findings(findings, technical: bool)` — renders each finding as a `.cp-finding <tone>` callout; skips `technical=True` items in simple mode. Add `render_stage_cell(stage, technical, expanded)` = expander titled `Stage {index} · {title}` with the **headline as the visible summary line**, body = findings + the stage's `render_detail` visual. (Move/import `render_detail` so both playback and cells share it — no duplicated dispatch.)
2. `2_Pipeline.py` playback path: keep the live animation area for the running stage, but on each stage's completion append its persistent cell into an accumulating `st.container()` (newest expanded, earlier collapsed). When the run finishes, clear the live area — the 9 cells ARE the record.
3. Completed/instant path (`:180-186`): render all 9 cells (stage 9 expanded) instead of only the last stage's detail.
4. View-mode gating: execution console (`console_ph`) renders **only** in technical mode (in simple mode the right column is dropped and the layout widens — don't leave a hole); SHAP block inside the explainability cell is technical-only (the reason codes remain in simple).
5. The left stage rail keeps its animation duty unchanged — it no longer has to carry the record.

**Acceptance**: after a full staged run, every one of the 9 stages is individually expandable with its plot + findings; nothing in a cell body looks like a console (no monospace log walls); replay/instant/back-navigation to the page all show the full record; reduced-motion behavior unchanged.

---

### WP-D — All other pages: attached rationale + info icons + gating
**Files**: `pages/1_Dashboard.py`, `pages/3_Financial_Health_Card.py`, `pages/4_Explainability.py`, `pages/5_Architecture.py`, `Home.py`.
**Depends on**: WP-B (tips/glossary/toggle); WP-A for the verdict.

1. **Health Card**: render `assessment.verdict` sentences directly under the recommendation banner (`:45`) as the page's plain-language summary — this is the Issue-1 centerpiece. Add `tip=` to the 4 KPI cards (`:64-72`) from the glossary. Gate `engineering_name` on dimension rows (`:60`) behind technical mode.
2. **Dashboard**: `tip=` on all 6 KPI cards (`:44-61`); one-line inference under the hero (reuse the first verdict sentence); "K-Means (descriptive only)" sub-line (`:60`) becomes "compared with similar businesses" in simple mode.
3. **Explainability**: section captions get simple-mode phrasing; section 3 (SHAP) technical-only with a simple-mode substitute line ("A second, independent statistical model was used to cross-check these drivers — it agrees."); keep composites in both modes (they're the differentiator; their rationale text is already human-grade).
4. **Architecture**: technical by nature — add a simple-mode banner ("This page shows model internals — switch to Technical view for full detail") rather than stripping it.
5. **Home**: no structural change; add glossary tips to the staged-reveal toggle help text.

**Acceptance**: in Simple mode, a full click-through of all pages surfaces **zero** banned-jargon terms (§G4); every headline number has either an adjacent inference sentence or an info tip; no page gains vertical clutter (tips are icons, inferences are one line).

---

### WP-E — QA, copy pass, docs
**Files**: `docs/05-deliverables/demo-script.md`, `internal/issues`, tests.
**Depends on**: WP-A…D merged.

1. Copy review of every user-visible string added by A–D against §Copy Bank principles (one voice, no hedging, Indian banking vocabulary — Cr/L, CMR-grade analogue).
2. AppTest smoke extended to run all pages in **both** view modes (drive from Home, flip `st.session_state["cp_view_mode"]`).
3. Jargon regression test: a test that walks all `Stage.findings`/`headline`/glossary strings asserting the §G4 banned list is absent from `technical=False` copy (backend-side; the page-level check stays manual).
4. Update `demo-script.md` for the new flow (notebook cells, toggle moment — flip to Technical live during the demo as a beat: "and for your risk team, every internal is one switch away").
5. Mark items resolved in `internal/issues` (append a `— addressed by <commit>` line per item; don't delete the user's text). Full suite green; report final test count.

---

## 5 · Guardrails (all WPs)

- **G1 — Module boundaries are non-negotiable.** Frontend renders only. All inference/finding/verdict **text generation** happens in `backend/services/pipeline_orchestrator.py` (label application is the backend's job). `ml/` is untouched by this entire plan.
- **G2 — No recomputation.** Every finding is a re-statement of a value already in `Stage.data` / `engine_output` / `HealthCard`. If you need a number that isn't there, add it to `Stage.data` in the same stage builder — never compute in a page.
- **G3 — Keep the a11y bar** from commit `422d81d`: 4.5:1 contrast, `prefers-reduced-motion`, keyboard focusability for anything interactive (tooltips included), `html.escape()` on every interpolated entity-derived string.
- **G4 — Banned jargon in Simple mode** (and in any `technical=False` finding): `SHAP`, `WOE`, `IV`, `K-Means`, `PCA`, `centroid`, `GBM`, `LightGBM`, `monotonic`, `percentile`, `z-score`, `scorecard bins`, bare `PD` (write "estimated default risk" or "chance of repayment difficulty"; `Model PD` may appear in Technical only), `latent`, `feature` (write "signal" or "indicator").
- **G5 — Determinism.** Verdicts/findings are template-driven from scored values — no randomness, no LLM calls. Same entity → same words, every run (judges will re-run).
- **G6 — Tests stay green.** 124 passing today; each WP leaves the suite green and adds its own coverage. Don't renumber/rename existing stage keys or `_STAGE_DATA_KEYS` entries — extend only.
- **G7 — Uncommitted-work etiquette.** Work on `ui-review` (or a child branch). Do not commit `internal/issues` content edits except WP-E step 5.

## 6 · Copy Bank

Tone: a senior credit analyst briefing a branch manager — declarative, concrete, one thought per sentence. Always name the *evidence*, then the *inference*. Values in ₹ L/Cr. Templates use `{}` placeholders filled from existing `Stage.data`/`out` fields; tone thresholds mirror `ui.score_class`/`auth_class`/`risk_class`/`band_class` exactly.

- **CB-1 Scenario** — headline: `"Assessing {name}, a {category}-category {sector} business, {age}y in operation."` Finding (neutral): `"The business self-declares {turnover} annual turnover — every claim below is tested against independent records."`
- **CB-2 Ingestion** — headline: `"{connected} of {total} independent data sources hold live records for this business."` Findings: good if ≥14 connected (`"a broad digital footprint — decisions here don't hinge on any single document"`), warn if ≤8 (`"a thin file — the assessment leans on fewer sources, reflected in a lower confidence rating"`). Technical finding: record counts by group.
- **CB-3 Integration** — headline: `"{total_records} records reconciled into one verified business identity."` Finding keyed on `identity_integrity`: ≥0.9 good `"Government registries (GST, PAN, Udyam, MCA) agree on who this business is."`, else warn `"Registry details do not fully agree — identity checks reduce the score's confidence."`
- **CB-4 Features** — headline: `"Raw records distilled into {total_features} measurable business indicators across five dimensions."` Simple finding: name the five dimensions in words; technical finding: per-pillar counts.
- **CB-5 Synthesis** — headline: `"Independent sources cross-checked against each other — signals that are hard to fake."` Flagship finding tone via `auth_class`: ≥80 good `"Declared sales are consistent with actual bank credits and goods movement ({v}/100)."`; 55–79 warn; <55 risk `"Declared sales are NOT supported by bank credits or goods movement ({v}/100) — a possible inflated-turnover attempt."` One finding per non-flagship composite only when it deviates materially (flag_bad > 0.5 or index < 0.4); otherwise a single roll-up sentence — don't list 12 items.
- **CB-6 Peer group** — headline: `"Compared with {n} similar businesses, {name} sits in the '{segment}' group."` Neutral finding: `"Grouping is context for the officer — it never changes the score."` Technical: k, silhouette-chosen, pillar-space.
- **CB-7 Scoring** — headline: `"Financial Health Score {score}/100 — grade {grade}/10, '{band}' track."` Findings: strongest and weakest dimension called out by name with its score; risk finding for PD via `risk_class` phrased as `"The statistical model rates the chance of repayment difficulty as {risk_category}."`
- **CB-8 Explainability** — headline: `"The score's top drivers, stated in plain terms — every one traceable to a source record."` Findings: reason codes are already human-grade — pass through top ±2. Technical finding: `"An independent SHAP cross-check over the challenger model agrees with these drivers."`
- **CB-9 Verdict (stage 9 + Health Card)** — sentence 1: `"{Recommendation}: {name} scores {score}/100 (grade {grade}/10) with an indicative limit of {limit}."` Sentence 2 = top reason code rephrased as the dominant driver. Sentence 3 (conditional, the flagship divergence): `"Note: standard repayment metrics look benign for this business — the caution comes from the turnover-authenticity check, which found declared sales unsupported by independent evidence. A conventional scorecard would likely have approved this application."`
- **CB-10 Glossary (tooltips; ≤ 25 words each)** — `financial_health_score`: "Composite 0–100 measure of overall financial health, built from five dimensions of verified alternate data. Higher is healthier." · `grade`: "1–10 ranking analogous to a bureau's MSME rank; 1 is best." · `pd`: "Statistically estimated chance of repayment difficulty in the next 12 months, from a model trained on similar businesses." · `indicative_limit`: "A starting exposure suggestion derived from verified turnover and the onboarding band — not a sanction." · `confidence`: "How much verified data backs this assessment — more independent sources, higher confidence." · `authenticity`: "Cross-check of declared sales against bank credits and goods movement. Low values suggest inflated declarations." · `peer_segment`: "Descriptive grouping of similar businesses for context; never part of the score." · `bureau_score`: "The same assessment expressed on the familiar 300–900 scale." · `onboarding_band`: "Routing suggestion: fast-track, manual review, or decline." · `sources_connected`: "Independent systems (tax, banking, utilities, registries…) with live records for this business."

## 7 · Definition of done (whole plan)

1. All four `internal/issues` items demonstrably addressed (WP-E annotates the file).
2. Full staged run leaves a 9-cell, expandable, human-readable record; nothing meaningful vanishes when the animation ends.
3. Every headline prediction on every page carries an adjacent inference or an info tip; Health Card opens with the verdict narrative.
4. Simple mode passes the §G4 jargon sweep; Technical mode loses nothing that exists today.
5. Test suite green (≥ current 124 + new coverage); AppTest renders all pages in both modes; demo script updated.
