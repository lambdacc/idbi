# Multi-Track Implementation Plan — CreditPulse Platform (PS3 + PS4 + PS5)

**Date:** 04 Jul 2026 · **Deadline:** working prototype + PPT + repo per track, **09 Jul 2026**
**Decision record:** `../04-second-track/second-track-assessment.md` (research + rationale). Founder approved building **both** PS4 and PS5 on 04 Jul 2026.
**Audience:** implementation agents (Opus/Sonnet). Each work package (WP) file is self-contained; read this README first, then your WP file, then the code files it lists. **Do not trust descriptions of code in these docs over the code itself — the repo had an outside UI redesign (branch `frontend-redesign`, "Ledger" system); always read current files before editing.**

---

## 1. What we are building

One application, one deployment, three hackathon tracks as navigation groups:

| Nav group | Track | Content |
|---|---|---|
| **Platform** | — | New Overview landing page (default): platform pitch, three track cards, honesty note |
| **Track 03 · Financial Health** | PS3 (built) | Run Assessment (current Home), Dashboard, Pipeline, Health Card, Explainability |
| **Track 04 · Early Warning** | PS4 (new) | Portfolio Overview · Watchlist & Case Drilldown *(stretch: Monitoring Pipeline)* |
| **Track 05 · Fraud Intelligence** | PS5 (new) | Fraud Desk · Case Investigation *(stretch: Network View)* |
| **Reference** | — | Architecture (updated to cover the platform) |

**Track 04 — "Portfolio Early Warning":** 12-month-horizon MSME default early-warning on a synthetic loan book grown out of the existing cohort. Thesis encoded in data and demo: *alt-data (monthly GST, UPI inflows, EPFO payroll) deteriorates 6–12 months before repayment behaviour does; a repayment-only 3-month baseline (the stand-in for IDBI's internal SAJAG-style model) alerts late; ours alerts early — and explains why.* Metrics: lead time, capture@decile, alert precision — NOT raw accuracy.

**Track 05 — "SentinelPulse":** explainable mule-account detection (typology rules + Isolation-Forest anomaly leg + ring expansion) with a **deterministic agentic investigation workflow** that assembles a citation-gated case file (every claim resolves to specific transaction IDs) for human approval. Hooks: RBIH MuleHunter.AI momentum + MHA directive (all FIs integrate mule detection by Dec 2026) + RBI FREE-AI explainability sutras.

## 1a. Repo layout — track isolation (founder constraint, 04 Jul)

Each PS is submitted as a git repo; the founder must be able to produce a per-track repo by **deleting the other tracks' folders and nothing else**. Therefore:

```
app/
  data_gen/            # PLATFORM CORE: cohort generators, latents, distributions (ships in every variant)
  ml/                  # PLATFORM CORE: models/ (woe, gbm, calibration, clustering, anomaly, …),
                       #   features/, explainability/, eval/ framework — the shared ML kit
  backend/             # PLATFORM CORE: shared Stage/Assessment dataclass module(s) only
  frontend/            # PLATFORM CORE: main.py router (NOT app.py — collides with the app package), tracks.py registry, components/, static/,
                       #   pages/platform/ (Overview) — no track logic
  tracks/
    t03_financial_health/   # engine glue (ScoringEngine wiring + prefit hook), pipeline_orchestrator,
                            #   scoring_service, pages/, tests/
    t04_early_warning/      # loan-book data_gen, ml (features/model/eval), ews orchestrator, pages/, charts, tests/
    t05_fraud_intelligence/ # fraud data_gen + profiles, ml (typologies/features/model/eval),
                            #   case orchestrator, pages/, charts, tests/
```

- **D10 — Isolation rules:** a track may import from platform core; a track must NEVER import from another track. `rm -rf app/tracks/<any>` leaves the app fully working: the `tracks.py` registry **auto-detects** installed tracks (path-exists / guarded import), `app/ml/prefit.py` warms only present engines (guarded imports), `Makefile test` discovers each track's tests from inside its folder (`pytest app/tests app/tracks`), and the Overview page renders cards only for installed tracks. Enforced by an import-linter test in platform tests (grep/AST: no `app.tracks.tXX` import from a different `app.tracks.tYY`).
- **D11 — Stable URL entry points:** `st.Page(..., url_path=...)`: Overview = default root; T03 Run Assessment = `track03`; T04 Portfolio Overview = `track04`; T05 Fraud Desk = `track05`. These are the per-PS submission deep links; every start page must render sensibly on a cold session (no assessment seeded).
- **Migration note (WP-R):** existing PS3 code MOVES into `app/tracks/t03_financial_health/` (git mv + import-path fixes; the 166-test suite is the safety net). Shared-kit modules (`ml/models`, `ml/features`, `ml/explainability`, `ml/eval`, `data_gen`) stay in core — they are libraries used by tracks, not track code. `ml/engine.py` (ScoringEngine) is T03's and moves with it; if `ml/features`/`explainability` prove too T03-entangled to be honest "core", prefer moving them into t03 and having t04/t05 own their features outright — decide by inspection, record in the WP-R report.

## 2. Locked architecture decisions

- **D1 — Navigation:** switch the entrypoint from the `pages/` auto-registry to explicit `st.navigation`/`st.Page` (both confirmed available in pinned Streamlit 1.39.0). New router `app/frontend/main.py` (**not `app.py`** — a file named `app.py` in `app/frontend/` shadows the `app` package and breaks all imports, see wp-s-findings.md); **page FILES keep their current paths** (`Home.py`, `pages/*.py`) to minimize churn; nav labels/groups/icons defined once in a declarative `app/frontend/tracks.py` registry.
- **D2 — Shell owns chrome:** with `st.navigation`, the entrypoint runs on every rerun (it is the router). `page_setup()`-style global chrome (CSS injection, sidebar brand, view toggle, set_page_config) moves into the router so each page stops repeating it. Pages keep only their titles/content. `ui.page_setup` remains but is split: `ui.shell_setup()` (router-level) + `ui.page_header(title)` (page-level). Backward-compat: `page_setup` may stay as a thin deprecated alias during migration if it shrinks the diff.
- **D3 — Session/state contracts unchanged:** `cp_view_mode` ("simple"/"technical"), `cp_assessment`, `cp_pipeline_played`, `cp_instant` keep their exact names and semantics. New tracks add parallel keys: `cp_monitoring_run`, `cp_case_<...>` (see WP files).
- **D4 — Engines:** three engine singletons behind `st.cache_resource` in `components/state.py`: existing `get_engine()` (ScoringEngine) + new `get_ews_engine()` (EWSEngine) + new `get_fraud_engine()` (FraudEngine). Each engine follows the ScoringEngine pattern exactly: `fit(...)`, `save()/load` with a `STATE_VERSION` class attr stamped in `__getstate__` and checked on prefit-load, mtime-vs-source staleness check, fallback to refit. `app/ml/prefit.py` warms all three pickles (skip-if-fresh per engine).
- **D5 — No new dependencies. No runtime LLM.** Everything renders from deterministic computation + template narration (the existing `verdict()`/findings pattern). Graph work (ring expansion, layout) is implemented in plain python/pandas (BFS/union-find + deterministic circular layout) — **networkx is NOT added**. PS5's "agentic" framing = orchestrated specialist stages with human approval, disclosed honestly on-screen.
- **D6 — Module boundaries (unchanged, enforced):** `frontend/` renders only — no computation, no copy generation; `backend/` orchestrates and owns all brief-facing labels/narratives; `ml/` computes, framework-clean (pandas/sklearn/lightgbm only). Any inference text a page shows must arrive pre-composed from backend.
- **D7 — Dual-audience views everywhere:** every new page supports Simple and Technical modes via `state.is_technical()`. The banned-jargon guardrail extends to new pages; new terms (DPD, NPA, EWS, PD-horizon, mule, typology, STR, Isolation Forest…) get Simple-mode synonyms and `glossary.py` entries. The jargon test's banned list grows accordingly.
- **D8 — Data honesty:** all new data is synthetic, latent-driven (same philosophy as `profiles.py`: hidden truth variables generate consistent multi-source signals), labelled synthetic on-screen, with "real-data recalibration is the pilot step" notes in each track's UI and docs.
- **D9 — Demo-first scope control:** per track, 2 core pages are the must-demo MVP. Stretch items have explicit cut lines in each WP. When time pressure hits, cut stretch — never cut tests or honesty notes.

## 3. Work packages, waves, and file ownership

| Wave | WPs (parallel within wave) | Blocks on |
|---|---|---|
| **0** | **WP-S** navigation spike (small, serial) | — |
| **1** | **WP-R** base refactor ∥ **WP-4D** T04 data ∥ **WP-5D** T05 data | WP-S |
| **2** | **WP-4M** EWS ML ∥ **WP-5M** fraud ML | WP-4D / WP-5D respectively (WP-R not required) |
| **3** | **WP-4A** T04 backend+frontend ∥ **WP-5A** T05 backend+frontend | WP-R + WP-4M / WP-R + WP-5M |
| **4** | **WP-V** verification, docs, submission packaging | all |

**WP files:** `wp-s-nav-spike.md` · `wp-r-base-refactor.md` · `wp-t04-early-warning.md` (WP-4D/4M/4A) · `wp-t05-sentinelpulse.md` (WP-5D/5M/5A) · `wp-v-verification-submission.md`.

**File-ownership matrix (collision avoidance — same trick as previous rounds):**

| File / area | Owner | Others |
|---|---|---|
| Platform core: `app/frontend/main.py`, `frontend/tracks.py`, `frontend/pages/platform/`, `components/ui.py`, `components/state.py` (shell), `static/custom.css` (shell/nav blocks) + the **t03 move** (`git mv` into `app/tracks/t03_financial_health/` incl. import/test fixes) | WP-R | read-only |
| `app/tracks/t04_early_warning/**` (everything inside, incl. its `pages/`, `charts.py`, `tests/`) | WP-4D/4M/4A per wave | nobody else |
| `app/tracks/t05_fraud_intelligence/**` | WP-5D/5M/5A per wave | nobody else |
| `components/state.py` — `get_ews_engine` / `get_fraud_engine` cache wrappers (thin, guarded imports) | WP-4A / WP-5A | append-only, separate sections |
| `components/glossary.py`, jargon list in the platform smoke test | WP-4A adds its terms; WP-5A adds its terms | append-only |
| `static/custom.css` | WP-R owns shell/nav; WP-4A/5A append commented track blocks at end (only if existing classes don't suffice) | append-only |
| `app/data_gen/**` (platform substrate: profiles/latents/distributions/registry) | WP-R custodian; WP-4D may add *hooks only* if the registry needs an extension point — track generators themselves live in the track folder | changes minimal + reported |
| `app/ml/prefit.py` | WP-R makes it track-aware (guarded discovery); WP-4M/5M register their engines via the discovered hook | append-only |
| `app/tests/*` (platform tests: registry, isolation linter, smoke) | WP-R structure; 4A/5A append their pages to sweep lists | append-only |
| `Makefile`, `Dockerfile` | WP-R (structure incl. `pytest app/tests app/tracks`) then WP-V (final audit) | |
| `README.md`, `START_HERE.md`, `docs/**` | WP-V only | |

**Note for WP-4x/WP-5x agents:** the module paths written inside `wp-t04-early-warning.md` / `wp-t05-sentinelpulse.md` predate the isolation decision (they say `app/ml/ews/`, `app/data_gen/loan_book.py`, `app/backend/services/..._orchestrator.py`, `pages/6_...py`). **Translate them to the track-folder layout above** (`app/tracks/t04_early_warning/ml/`, `.../data_gen.py`, `.../service.py`, `.../pages/portfolio_overview.py`, tests inside the track). The *content* of those specs is unchanged.

## 4. Operating rules for implementation agents

1. **Read before write.** Start every WP by reading: this README, your WP file, `START_HERE.md`, and every file in your ownership row. The repo's current state ALWAYS wins over plan prose; if the plan contradicts the code, follow the code's conventions and note the divergence in your final report.
2. **Test-green increments.** `make test` (fast, no network) must pass at every WP boundary. Never delete or weaken an assertion to get green; adapt tests only where the UI they encode intentionally moved (list such changes in your report).
3. **Determinism.** All generators take/derive from the fixed seed conventions in `app/data_gen` (read `build_dataset.py` + `distributions.py` first). Same seed → identical CSVs. Tests must not depend on wall-clock.
4. **Style:** match surrounding code — docstring tone, section comments citing plan §s, type hints, naming (`cp_` session keys, `_private` helpers). New pages copy the structural skeleton of an existing page (e.g., `pages/1_Dashboard.py`) including the sys.path bootstrap.
5. **Jargon guardrail:** any user-visible string you add must pass the Simple-mode sweep on Simple pages. When in doubt, put the technical term behind `is_technical()` and add a glossary entry.
6. **Honesty:** never fabricate metric claims in UI copy. Metrics shown must be computed by the eval harness at build time or clearly labelled "illustrative".
7. **No commits** unless the driving session explicitly instructs; leave work uncommitted on the current branch.
8. **Report format:** end with: files touched, tests added/updated (+ count delta), acceptance checklist status, deviations from plan, anything the next WP must know.

## 5. Schedule (against 09 Jul)

| Day | Target |
|---|---|
| 04 Jul (eve) | WP-S spike done; Wave-1 agents launched |
| 05 Jul | Wave 1 complete (shell + both datasets); Wave 2 launched |
| 06 Jul | Wave 2 complete (both engines + evals); Wave 3 launched |
| 07 Jul | Wave 3 complete (all pages live); WP-V verification sweep |
| 08 Jul | Docs/README/demo-script; deploy; PPTs (per track); buffer |
| 09 Jul | Submission (3 tracks: PS3, PS4, PS5) |

**Global cut lines if slipping:** drop Track-04 stretch page → drop Track-05 network view → drop Track-05 entirely from *submission* (keep branch) before ever compromising PS3+PS4 quality. PS3 must not regress: its pages, tests and demo flow are the reference asset.

## 6. Global acceptance (verified in WP-V)

1. `make install && make data-gen && make test && make demo` from a clean checkout: all green; app serves with three track groups; Overview is the default page.
2. Full AppTest sweep: every page × {simple, technical} renders with 0 exceptions; Simple pages jargon-clean; deep-links (`st.switch_page`/`page_link`) work under `st.navigation`.
3. `make prefit` warms all three engines; second run of each is instant; deleting any pickle falls back to fit; version-guard rejects stale pickles (tests).
4. Docker image builds and serves all three tracks on `$PORT`.
5. T04 demo: drilldown timeline visibly shows alt-data first-alert months before the repayment-only baseline's first alert, for the flagship deteriorating borrower; eval scorecard prints lead-time/capture metrics.
6. T05 demo: fraud desk queue → open investigation → staged agentic run → case file with every evidence line citing real transaction IDs → approve/override writes an audit line; the hard-negative account is *cleared* with reasons.
7. Docs updated (README, START_HERE, architecture page, demo-script) to platform framing; `internal/issues` conventions respected.
8. **Selective-delete rehearsal:** in a scratch clone, `rm -rf app/tracks/t05_fraud_intelligence` → `make test && make demo` green with 2 track groups; repeat for t04; repeat deleting both (PS3-only variant). No code edits needed in any case.
9. **Deep links:** `/track03`, `/track04`, `/track05` each load their start page on a cold session without errors; these URLs recorded in the submission checklist as the per-PS deploy links.
