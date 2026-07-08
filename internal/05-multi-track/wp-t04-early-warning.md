# WP-T04 — Track 04 · Portfolio Early Warning (PS4)

Three sub-packages run in successive waves: **WP-4D** (data, Wave 1) → **WP-4M** (ML+eval, Wave 2) → **WP-4A** (backend+frontend, Wave 3). Each is a separate agent run; each reads this whole file plus the README first.

**The thesis this track must make visible** (encode it in data, measure it in eval, show it in UI):
> Repayment behaviour is a *lagging* indicator — by the time EMIs bounce, the account is ~2–3 months from NPA (that is all a repayment-only model like the bank's internal SAJAG-style system can see). The MSME's **alt-data footprint is a leading indicator**: GST filings slip and declared turnover sags, UPI/bank inflows shrink, EPFO headcount falls — 6–12 months before default. CreditPulse already ingests that footprint for onboarding (Track 03); Track 04 re-scores it monthly to warn 12 months out, with plain-language reasons and recommended actions.

**Honesty framing everywhere:** synthetic data encodes this thesis *by construction*; on-screen copy claims the *mechanism* ("alt-data deteriorates first — here is which signals and when"), never a real-world accuracy claim. Real-default recalibration = pilot step.

---

## WP-4D — Loan book & monthly panel data (Wave 1)

### Read first
- `app/data_gen/profiles.py` (latent variables: `true_scale_turnover`, `true_health`, `true_honesty`; archetype pinning), `build_dataset.py`, `distributions.py`, `generators/base.py` (registry + schema-test pattern), one core + one enrichment generator for style
- `app/tests/test_schema.py` (how generator schemas are asserted)

### Design (locked)
- **Borrower subset:** ~60% of the existing cohort (deterministic selection by seeded hash of entity_id) becomes the "existing MSME loan book". The six demo archetypes with a loan: include the healthy flagship AND one deteriorating showcase borrower (pick the distressed archetype; it becomes the demo star).
- **Panel horizon:** 24 monthly snapshots per borrower (months indexed -23..0 relative to "today").
- **Health trajectory:** per borrower, `health_t = clip(true_health + drift(t))`. Non-defaulters: mild noise/seasonality. Defaulters (bottom ~12–15% by `true_health`, deterministically): a deterioration ramp starting at `t_default - lead_alt` where `lead_alt ~ U(8, 14)` months (seeded), steepening over time.
- **Signal lag structure (the core trick):** alt-data series respond to `health_t` immediately; repayment series respond to `health_{t-Δ}` with `Δ ~ 5–9` months (i.e., repayment stress only materializes in the last few months before default). Concretely: DPD>0 and bounces appear only when the ramp has progressed far; GST/UPI/EPFO sag from ramp start.
- **Default event:** first month with DPD ≥ 90 ⇒ `default_month`; target rate ≈ 12–15% of the book, distributed so ~⅓ default inside the panel (observed events for eval) and ~⅔ of distress cases are "live deteriorating" (for the watchlist demo).

### Outputs (CSV, in the same data dir convention as existing sources)
1. `loan_book.csv` — entity_id, loan_id, product (term/CC/OD), sanction_month, tenor_months, sanctioned_limit (derive from scale latent), interest_rate, status (regular/watch/npa/closed).
2. `repayment_history.csv` — entity_id, month (-23..0), emi_due, emi_paid, dpd, bounce_flag, utilization_pct (CC/OD), overdue_amount.
3. `altdata_monthly.csv` — entity_id, month, gst_turnover_declared, gst_filed_on_time (0/1), bank_inflows, upi_txn_count, epfo_employee_count, energy_units. Derive levels from the SAME latents the cross-sectional generators use, so Track 03 and Track 04 numbers are mutually consistent for a given entity (spot-check the flagship archetypes).
4. Registered via the existing generator registry + `build_dataset.py` so `make data-gen` produces everything. Deterministic under the fixed seed.

### Tests (new `app/tests/test_loan_book.py`)
- Schema/dtype/range checks per CSV (pattern-match `test_schema.py`).
- Determinism: two builds byte-identical.
- **Thesis encoded:** for defaulted borrowers, mean(first month where alt-data z-drop exceeds threshold) precedes mean(first month with dpd>0) by ≥ 4 months.
- Default rate within 10–18%; no defaults among top-quartile `true_health`.
- Track-03 consistency: for a sampled entity, `altdata_monthly` recent-12m GST turnover within tolerance of the cross-sectional GST generator's annual figure.

### Acceptance
`make data-gen` green incl. new CSVs; new tests + full suite green; a short "data card" section appended to `internal/appendix-b-synthetic-data-plan.md` is **deferred to WP-V** (note it in your report instead).

---

## WP-4M — EWS model, baseline, eval (Wave 2)

### Read first
- `app/ml/engine.py` (ScoringEngine end-to-end: fit, STATE_VERSION pickle pattern, `_load_prefit`), `models/gbm.py` (monotonic constraints + calibration wiring), `models/calibration.py`, `explainability/reason_codes.py`, `eval/` (metrics + runner style), `prefit.py`, `app/tests/test_engine_prefit.py`
- WP-4D's outputs + tests

### Build (`app/ml/ews/` package)
1. **`features.py`** — snapshot builder: `build_snapshots(loan_book, repayments, altdata, as_of_months) -> DataFrame` producing per (entity, month) features using ONLY months ≤ snapshot month:
   - Repayment: dpd_current, dpd_max_3m, bounce_cnt_6m, utilization_now, utilization_slope_6m, months_on_book.
   - Alt-data deltas: gst_turnover_slope_6m, gst_missed_filings_6m, inflow_slope_6m, inflow_vs_gst_gap (reuse the authenticity idea), upi_count_slope_6m, epfo_headcount_delta_6m, energy_slope_6m.
   - Static: sector, grade_at_onboarding (join from ScoringEngine output if cheaply available, else omit — do not create a cross-engine dependency).
   - Document a monotone direction table for every feature (comment block), used for GBM constraints.
2. **Labels:** `default_within_12m` (and `default_within_3m` for the baseline) from `default_month`. Snapshots after default are excluded.
3. **`model.py` — `EWSEngine`** mirroring ScoringEngine's shape:
   - `fit(data_dir)`: builds snapshots, **entity-level train/holdout split** (no entity straddles), monotonic LightGBM + `PostHocCalibrator` (reuse), reason codes (reuse the native sign-aware approach on EWS features), band thresholds pinned on calibrated PD: Red ≥ 0.30, Amber ≥ 0.12 (tune once to give a sensible demo mix ~5% Red / ~12% Amber; document chosen values).
   - **`baseline` sub-model:** same pipeline but repayment-features-only + `default_within_3m` label — the "internal-model stand-in". Store per-entity *first-alert month* for both models on the panel (walk snapshots chronologically; first month band=Red). This drives the drilldown comparison chart.
   - `portfolio_snapshot()`: latest-month scores/bands/reasons for every live loan + book-level aggregates.
   - `entity_timeline(entity_id)`: monthly series (alt-data levels, dpd, both models' PD trajectory, first-alert markers, default_month if any) — pure data, no copy.
   - `save()/__getstate__` with `STATE_VERSION = 1`; `_load_prefit()` with mtime + version checks (copy the ScoringEngine pattern precisely).
4. **`eval` additions (`app/ml/eval/ews_metrics.py` + runner hook):** holdout AUC (report, don't headline), **capture@top-decile**, alert precision/recall at Red, **lead-time distribution** (months from first Red to default; report median/p25/p75) for EWS vs baseline, false-alert rate on non-defaulters. Print a scorecard section like the existing eval runner.
5. **`prefit.py`:** add EWS warm (own pickle, skip-if-fresh) behind the same CLI.

### Leakage discipline (agents get this wrong — hard rules)
- Feature builder must raise if asked for a feature window extending past the snapshot month (test this).
- Entity-level split only; assert empty intersection.
- No label-derived fields in features (grep-proof: `default` appears nowhere in feature columns).

### Tests (`app/tests/test_ews.py`)
- Feature builder: future-window raises; snapshot at month m uses only ≤ m data (construct a poisoned future row and prove it's ignored).
- Split hygiene: train∩holdout entities = ∅.
- **Thesis measured:** median lead-time(EWS) − median lead-time(baseline) ≥ 4 months on holdout defaulters; capture@decile(EWS) > capture@decile(baseline).
- Calibration object present; PD in [0,1]; bands cover ~expected mix.
- Prefit round-trip + STATE_VERSION rejection (mirror `test_engine_prefit.py`).
- Determinism of fit outputs under fixed seed.

### Acceptance
Full suite green; eval runner prints the EWS scorecard with plausible numbers (no NaNs, lead-time gap positive); `python -m app.ml.prefit` warms both PS3 + EWS pickles; report the headline numbers for WP-4A to render.

---

## WP-4A — Backend orchestration + frontend pages (Wave 3; needs WP-R + WP-4M)

### Read first
- `app/backend/services/pipeline_orchestrator.py` (Stage dataclass, findings/verdict/technique patterns, tone tags), `scoring_service.py`
- WP-R's report (`_drive()` recipe, link conventions), `wp-s-findings.md`
- `components/` (state, ui, charts, stage, glossary), `pages/1_Dashboard.py` + `pages/3_Financial_Health_Card.py` as skeletons
- WP-4M's report (metric numbers, band thresholds, API shapes)

### Backend (`app/backend/services/ews_orchestrator.py`)
All copy/labels composed HERE (frontend renders only):
- `run_monitoring(ews_engine) -> MonitoringRun`: typed result with book KPIs (loans, exposure, Red/Amber/Green counts, median lead-time + capture from the engine's stored eval summary), watchlist rows (entity, name, sector, band, pd_12m, top-3 plain-language reasons, recommended action, exposure), and band-migration counts vs prior month.
- **Action vocabulary** (RBI EWS red-flag idiom, plain language): Red → "Review limit · site visit · restructure dialogue"; Amber → "Enhanced monitoring · request GST/bank refresh"; Green → "Routine annual review". Compose one-line rationale per borrower from reason codes (reuse the tone-tag helpers pattern).
- `case_detail(ews_engine, entity_id) -> CaseDetail`: timeline series + first-alert markers + default marker + narrative verdict paragraph (template + computed values, e.g. *"Filings slipped in Nov; inflows are down 34% over six months while payroll shrank from 12 to 8 — this account moved to Red ten months before any EMI was missed."*). Simple/Technical variants of stage/technique disclosures (Technical adds model/calibration/constraint detail).

### Frontend
**`pages/6_Portfolio_Overview.py`** — KPI row (kpi component + glossary tips): book size, exposure, Red/Amber counts, median early-warning lead (with "vs 3-month repayment-only baseline" delta), capture@decile. Band distribution bar; migration summary; top-movers table; honesty caption. Both view modes (Technical adds the eval scorecard expander).
**`pages/7_Watchlist.py`** — ranked watchlist table (band-colored, semantic GREEN/AMBER/RED constants); `st.selectbox` (or table + select) → **case drilldown**: the money chart = multi-series timeline (GST declared turnover, bank inflows, EPFO headcount left-axis normalized; DPD bars right axis) with three vertical markers: `EWS first alert`, `Baseline first alert`, `Default`; reason-code list; recommended-action card; narrative verdict callout. Default-select the flagship deteriorating borrower so the demo opens on the money shot.
**Charts (`components/charts.py`, append `# --- Track 04 charts ---`):** `ews_timeline(...)` (marker conventions above; palette: navy/teal series, RED/AMBER markers reserved semantically), `band_bar(...)`, optional migration chart (stretch). Follow existing plotly config (displayModeBar off etc.).
**State (`components/state.py`, append):** `get_ews_engine()` `@st.cache_resource` with honest first-fit spinner copy; `get_monitoring_run()` session-cached (`cp_monitoring_run`).
**Glossary/jargon:** add EWS terms (DPD → "days late", NPA → "loan gone bad (90+ days late)", lead time, capture rate…); extend the banned list in the smoke test with Technical-only terms you introduce (e.g., "capture@decile", "calibrated PD") and keep Simple copies clean.
**CSS:** append a `/* --- Track 04 --- */` block only if needed (prefer existing classes).

### Tests
- Extend smoke `_PAGES` (both modes) — replace placeholder-render assertions with real ones: Portfolio shows "loans" KPI text; Watchlist shows the flagship borrower and the phrase "first alert".
- Jargon sweep covers both new pages in Simple mode.
- `test_ews_orchestrator.py`: MonitoringRun shape; every watchlist row has ≥1 reason + an action; case_detail markers ordered (EWS alert ≤ baseline alert ≤ default) for defaulted holdout entities; all user-facing strings come from backend (spot-check: pages contain no f-string composition of narrative — code-review level, note in report).

### Demo (append a Track-04 section to `internal/demo-script.md` — coordinate: WP-V owns final doc polish, you add the raw section)
90-second flow: Portfolio Overview ("240 loans, 11 Red — median warning 10 months before default; the repayment-only baseline gives 2") → Watchlist → flagship drilldown (walk the timeline markers) → reasons in plain language → action card → close on the platform line ("same rails that onboarded them now protect the book").

### Acceptance
Both pages live in both modes, 0 exceptions; the drilldown chart visibly separates the two alert markers; suite green; no module-boundary violations; cut line honored (migration chart is the first thing dropped if slipping).
