# WP-T05 — Track 05 · SentinelPulse: Fraud Intelligence (PS5, Open track)

Three sub-packages: **WP-5D** (data, Wave 1) → **WP-5M** (detection ML, Wave 2) → **WP-5A** (agentic case orchestration + frontend, Wave 3). Each is a separate agent run; read this file + README first.

**Positioning (drives every copy decision):** RBI/RBIH ships MuleHunter.AI network-level mule detection (23–26 banks; MHA directs ALL FIs to integrate by Dec 2026). SentinelPulse is the **bank-side layer above it**: explainable triage of flagged accounts, a deterministic **agentic investigation workflow** that assembles a citation-gated case file (every claim → transaction IDs), ring discovery, and a human approve/override gate with an audit trail — the FREE-AI-compliant fraud desk. PS5 rule: must be *unrelated to PS1–4* — this is transaction-fraud operations, not lending/scoring; say so on the page.

**Honesty rules:** synthetic transactions; "agentic" = orchestrated specialist stages, deterministic, human decides — disclose this in the Technical view's technique cards ("an LLM narrative layer is a pilot-step option; nothing here requires one").

---

## WP-5D — Synthetic transaction universe with mule rings (Wave 1)

### Read first
- `app/data_gen/profiles.py` (latent-variable philosophy — replicate it, do NOT modify the file), `distributions.py`, `generators/base.py` (+ one generator for style), `build_dataset.py`
- Public mule typologies for grounding (RBIH MuleHunter describes 19 behaviour patterns; implement the 8 below — cite in module docstring)

### Design (locked)
- **Universe:** ~800 accounts: ~600 retail savings + ~200 current accounts. For flavor + platform coherence, map the ~200 current accounts to existing MSME cohort entity_ids (join key only; do not touch MSME generators).
- **Latents (own module, e.g. `data_gen/fraud_profiles.py`):** per account `is_mule ∈ {0,1}` (~4% ≈ 32 accounts), `ring_id` (6 rings of 4–8 mules + 1 recruiter + 2–3 cash-out endpoints), `activity_level`, `income_band` (KYC), plus **hard negatives** (~10 accounts): genuine gig-worker/small-merchant profiles with high-velocity small credits but none of the structural mule signatures — the "explainably cleared" demo stars.
- **90 days of transactions** (`transactions.csv`): txn_id, date+time, account_id, counterparty_id, direction, amount, channel (UPI/IMPS/NEFT/ATM/POS), device_id, balance_after. Volume ~120–200k rows (keep build <10s).
- **8 typologies injected** (each a parameterized injector function; ring members express 2–4 of them):
  1. Fan-in/fan-out — many distinct small credits, rapid consolidation to few counterparties.
  2. Rapid pass-through — ≥80% of inflow leaves within 24h; balance hovers near zero.
  3. Dormancy burst — ≥60 dormant days then sudden high velocity.
  4. New-account velocity — account age <30d with disproportionate volume.
  5. KYC-income mismatch — monthly throughput ≫ declared income band.
  6. Round-amount structuring — dense round amounts just under common thresholds (e.g. ₹49,500 clusters).
  7. Odd-hours pattern — activity concentrated 00:00–05:00.
  8. Shared device/endpoint — one device_id across ≥3 accounts (ring glue).
- Legit accounts get realistic salary/merchant/utility patterns (reuse `distributions.py` helpers). Deterministic under the project seed.
- **Companion files:** `accounts.csv` (open_date, type, kyc_income_band, linked entity_id nullable), `fraud_ground_truth.csv` (is_mule, ring_id, typologies_expressed — for eval/tests ONLY; never read by the engine at score time).

### Tests (`app/tests/test_fraud_data.py`)
Schema/ranges/determinism; ring structural properties hold (each ring shares ≥1 device or dense counterparty links); hard negatives express high velocity but NOT structuring/pass-through/device-sharing; mule rate 3–5%; ground truth never imported by `app/ml/fraud` runtime modules (import-graph grep test or convention assert).

### Acceptance
`make data-gen` builds everything green; new + full tests green; report typology parameters chosen.

---

## WP-5M — Detection engine (Wave 2)

### Read first
- `app/ml/models/anomaly.py` (**the badness-oriented Isolation-Forest pattern + genuine-anchored excess scaling — reuse the class or the pattern**), `calibration.py`, `engine.py` (STATE_VERSION/prefit), `eval/` runner style
- WP-5D outputs + report

### Build (`app/ml/fraud/` package)
1. **`features.py`** — per-account behavioural features over the 90-day window: velocity stats, in/out ratio, median pass-through minutes, dormancy-burst score, counterparty fan-in/fan-out degree, round-amount share, threshold-hugging share (amounts in [0.9,1.0)× common thresholds), odd-hours share, device-sharing degree, account-age×volume interaction, kyc_mismatch_ratio.
2. **`typologies.py`** — the 8 named deterministic detectors, each returning `(score_0_100, evidence)` where **evidence = the concrete transaction IDs/counterparties/devices that triggered it**. This evidence structure is the backbone of citation gating downstream — design it as a small dataclass (`TypologyHit(name, score, txn_ids, counterparties, device_ids, plain_summary_inputs)`). No user-facing copy here (ml computes; backend narrates).
3. **`model.py` — `FraudEngine`:**
   - `fit(data_dir)`: fit the IF anomaly leg on legit-oriented feature space (badness-oriented, genuine-anchored excess — mirror `anomaly.py`); combine `mule_risk = 0.55·typology_max_blend + 0.45·anomaly_excess` (document the blend; tune once for sensible desk mix); bands: Alert ≥ 65, Review ≥ 45, Clear < 45.
   - `score_accounts() -> DataFrame` (account, score, band, typology hits w/ evidence, anomaly component).
   - **`expand_ring(account_id)`** — pure-python BFS over "suspicious edges" (shared device OR high-volume counterparty link between flagged accounts) returning ring membership + edge list + a **deterministic circular/bipartite layout** (x,y per node) for plotting. NO networkx (D5).
   - `save()/prefit` with `STATE_VERSION = 1` (copy ScoringEngine pattern); add to `app/ml/prefit.py` (append-only).
4. **`eval` (`app/ml/eval/fraud_metrics.py` + runner hook):** using ground truth — ring-level recall (a ring counts as caught if ≥60% members ≥ Review), account precision/recall at Alert, false-positive rate on hard negatives (headline: hard-negative FP rate — target 0), per-typology capture. Print a scorecard section.

### Tests (`app/tests/test_fraud_engine.py`)
Each typology detector fires on its injected accounts and NOT on hard negatives (per-typology capture ≥ 0.7, hard-negative typology score below Review); every `TypologyHit.txn_ids` refers to rows that exist in transactions.csv (**citation integrity at the ML layer**); ring expansion recovers ≥5 of 6 rings with ≥60% membership; blend score in [0,100]; bands deterministic; prefit round-trip + version rejection; determinism under seed.

### Acceptance
Full suite green; eval scorecard prints (ring recall high, hard-negative FPs = 0 ideally — tune until so, it's synthetic); prefit warms all three engines; report numbers + API shapes for WP-5A.

---

## WP-5A — Agentic case orchestration + frontend (Wave 3; needs WP-R + WP-5M)

### Read first
- `app/backend/services/pipeline_orchestrator.py` (Stage/findings/technique/verdict machinery — REUSE it), WP-R report (`_drive()`, link conventions), `components/stage.py` (staged pipeline rendering), `pages/2_Pipeline.py` (staged-reveal loop pattern), WP-5M report

### Backend (`app/backend/services/case_orchestrator.py`)
`investigate(fraud_engine, account_id) -> CaseFile`, decomposed into **five agent stages** (reuse the Stage dataclass so the existing pipeline renderer works unmodified; each stage has headline, findings (tone-tagged), technique disclosure (plain/algorithm/benefit — algorithm Technical-only), log lines, structured data):
1. **Triage agent** — pulls score/band/components; states why the account was queued.
2. **Evidence agent** — per fired typology: plain-language finding + the citing transaction table (from `TypologyHit`). **Citation gate: every finding must carry ≥1 txn_id; the orchestrator raises/degrades to "insufficient evidence" rather than emit an uncited claim** (mirror ReconWise's citation-gating stance; say so in the technique card).
3. **Network agent** — `expand_ring`; findings on ring size, shared devices, cash-out endpoints; layout payload for the chart.
4. **Adjudication agent** — deterministic decision table over evidence strength → recommendation ∈ {Freeze + file STR draft, Enhanced monitoring, Clear with note}; composes the rationale paragraph. Hard negatives must route to *Clear* with the explanation ("high velocity is consistent with declared gig income; no structuring, no pass-through, no device sharing").
5. **Case-file compiler** — STR-style structured draft: grounds of suspicion (each with citations), account/ring annexure, txn annexure, recommendation — awaiting human decision.
Also `desk_snapshot(fraud_engine)`: queue rows (account, score, band, typology names, est. exposure), KPIs (accounts monitored, alerts, rings, blocked-value estimate — computed, labelled "illustrative"), typology distribution. **All copy composed here.**

### Frontend
**`pages/8_Fraud_Desk.py`** — KPI row; alert queue table (band colors; typology chips); typology distribution bar; select account → `st.switch_page` to Case Investigation (store `cp_case_account` in session); a "Why this track" card (MuleHunter/MHA/FREE-AI hooks, 3 lines, from backend constants); honesty caption. Default-select a juicy ring mule; also surface one hard negative prominently.
**`pages/9_Case_Investigation.py`** — the showpiece: staged agentic run rendered with the EXISTING pipeline components (stage rail left, live output right, notebook cells below — same layout contract as `2_Pipeline.py`; instant mode honored via `cp_instant`); then the **case file**: grounds with citation-expanders (transaction tables), ring diagram (plotly scatter using the layout payload; nodes colored by role — mule/recruiter/cash-out/this-account; RED reserved for confirmed-band), recommendation card, **Approve / Override buttons** appending to a session audit trail (`cp_case_audit`: timestamp-free ordinal entries, rendered as an audit table — no wall-clock in tests' way).
**Charts (append `# --- Track 05 charts ---`):** `ring_network(...)`, `typology_bar(...)`.
**State (append):** `get_fraud_engine()` cache_resource; `cp_case_account`, `cp_case_audit` session keys.
**Glossary/jargon:** mule account → "account rented out to move stolen money", STR → "suspicious-transaction report", typology, pass-through, structuring… Simple pages jargon-clean; extend banned list with Technical-only terms you introduce.
**CSS:** append `/* --- Track 05 --- */` block only if needed.

### Tests
- `test_case_orchestrator.py`: CaseFile stage count/order; **citation gate holds** (every ground's txn_ids exist in transactions.csv; constructing a finding without citations raises); hard-negative account adjudicates to Clear; ring stage payload has ≥3 nodes for a ring mule; all narrative strings originate in backend.
- Smoke: both pages × both modes render 0 exceptions (seed `cp_case_account` in `_drive`-style setup); jargon sweep on Simple.
- Audit trail: approve then override → two ordered entries.

### Demo (append raw Track-05 section to `docs/demo-script.md`)
~90s: Desk ("31 alerts across 6 suspected rings") → open the ring mule → agent stages stream (triage → evidence with cited txns → ring of 7 sharing one device → adjudication: Freeze + STR draft) → approve → flip to the gig-worker hard negative → agents CLEAR it with reasons → close: "explainable both ways — that's what FREE-AI requires and rules can't do."

### Acceptance
Both pages live both modes; staged run + case file + ring chart render; citation gate enforced by test; suite green; cut lines: network chart → replace with a table (first cut); the desk typology bar (second); never cut the hard-negative clear flow (it is the differentiator).
