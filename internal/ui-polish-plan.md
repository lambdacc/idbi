# UI Polish Plan — internal/issues round 2 (03 Jul 2026)

Review + implementation plan for the six feedback items in `internal/issues`
(lines 1–15). Same working rules as `ui-humanization-plan.md`: module
boundaries hold (frontend renders only; backend orchestrates; ml computes),
Simple-mode jargon guardrail stays enforced, all 161 tests stay green (update
the ones that encode moved UI, never delete assertions), work stays
uncommitted on `feature/ui-humanization` until the user says commit.

---

## 1 · Issue review & decisions

### I1 — "First launch shows a loading screen, keeps on loading. Is it a bug?"
**Diagnosis (done — measured):** On first launch `Home.py:38` calls
`state.get_engine()`, which fits the full ScoringEngine (25-source load, WOE,
LightGBM + out-of-fold calibration, K-Means, Isolation Forest, SHAP). Measured
fresh-fit: **~7 s locally**; noticeably longer inside a resource-capped
container. So yes — something IS loading under the hood, once per process;
afterwards it's cached (`st.cache_resource`). Not an infinite loop.
Three real gaps though:
1. `app/data/engine.pkl` does not exist locally — `make prefit` exists
   (`app/ml/prefit.py`) but nothing in the local flow produces the pickle, so
   every fresh process pays the fit.
2. **Latent bug found during review:** `engine._load_prefit()` staleness check
   is mtime-vs-cohort only (`engine.py:236`). A pickle saved *before* the
   calibration/anomaly upgrade would still load "successfully" and then crash
   `score_entity` (no `self.anomaly`) or silently miss fraud fields. The
   pickle needs a code-version stamp.
3. The spinner copy ("Fitting scoring models …") doesn't tell a first-time
   user this is one-time and roughly how long.

**Decision:** ship prefit-by-default + version-guarded pickle + honest
first-launch copy (WP-F). If the user still sees an *endless* load after
this, the remaining suspect is the well-known Streamlit websocket/"Please
wait" proxy mode — diagnose then with
`--server.enableCORS=false --server.enableXsrfProtection=false` (do NOT bake
those flags in preemptively).

### I2 — Live stage output on the right; wider layout
Currently during the staged reveal the live stage detail renders *below* the
stage rail (full-width `detail_ph`, `2_Pipeline.py:74`), and the right column
exists only in Technical view (console). The ask:
- Both views: right side shows **each stage's output as it is generated**,
  animatedly — the flow visibly "streams".
- Technical view: the terminal/console **stays too**, alongside the new live
  output.
- The bottom notebook cells (per-stage record) stay as-is.
- Reduce sidebar width; more room for the pipeline section; smaller page
  margins.

**Decision:** WP-G. Two-column layout in BOTH views: left = stage rail +
progress bar (narrower); right = live stage-output pane (the existing
`render_detail` live area, moved into the column), with the console *below*
the live pane in Technical view (shorter, ~220px, still tailed). The
completed-run behaviour is unchanged: live pane clears, the 9 notebook cells
are the record. Width: raise `.block-container` max-width to ~1500px with
~2rem side padding, pin sidebar to ~15rem.

### I3 — Peer-grouping chart colors too light
Cause: `_CLUSTER_COLORS` at 0.5 opacity on a white background
(`charts.py:17,60`). **Decision:** WP-H — a deeper, still-restrained
categorical palette at opacity ≈0.75 with a hair more marker size. Keep
green/amber/red reserved for risk semantics elsewhere; peer tiers may use a
non-semantic elegant set (navy / teal / terracotta / plum / bronze family).

### I4 — Module boundaries & Deployment cards on Architecture page
Engineering-internal content, already documented in
`internal/deployment-runbook.md` and code docstrings. **Decision:** WP-I —
delete the two cards (`5_Architecture.py:84-99`). Keep the closing
"all data is synthetic" honesty note.

### I5 — Simple/Technical toggle top-right, not sidebar
**Decision:** WP-I. `page_setup()` renders a right-aligned horizontal radio
(Streamlit 1.39 has no `st.segmented_control`) in a top row on every page,
still bound to session key `cp_view_mode` — so `state.view_mode()` /
`is_technical()` and all consumers are untouched. Style it as a compact pill
via CSS. Remove the sidebar radio. Update `test_frontend_smoke.py` wherever
it drives the sidebar radio.

### I6 — Brand block on top of the sidebar
The brand HTML is already first in *our* sidebar content, but Streamlit
renders the multipage nav above all user sidebar content, so the brand sits
below the page links. With the radio gone (I5) the brand is the *only*
sidebar content. **Decision:** WP-I — CSS flex-reorder inside
`[data-testid="stSidebar"]` so the user-content block (brand) gets
`order: 0` and `[data-testid="stSidebarNav"]` gets `order: 1`. Inspect the
1.39 DOM before writing the selector; degrade gracefully (if the selector
misses, brand simply stays below — no breakage).

---

## 2 · Work packages

Wave 1 (parallel, disjoint files): **WP-F ∥ WP-H ∥ WP-I**
Wave 2 (after I, owns the pipeline layout + its CSS): **WP-G**
Wave 3: **WP-V** verification sweep.

### WP-F — First-launch startup: prefit by default, version-guarded pickle
Files: `app/ml/engine.py`, `app/ml/prefit.py` (if needed), `Makefile`,
`Dockerfile` (verify only), `app/frontend/components/state.py`,
`app/frontend/Home.py`, `app/tests/` (new test).
1. Add `STATE_VERSION` (int class attr, start at 2) to `ScoringEngine`;
   `save()` writes `{"version": STATE_VERSION, "engine": self}` (or embeds it
   in `__getstate__`); `_load_prefit()` rejects any pickle whose version ≠
   current — refit instead. This kills the stale-code-pickle crash class.
2. Make the local flow produce the pickle: `make demo` (and `make train` if
   cheap) depends on `prefit`, which itself skips when the pickle is fresh
   (mtime + version). Confirm the Dockerfile already runs prefit post
   data-gen; add if missing.
3. First-launch copy: `st.cache_resource(show_spinner=...)` text becomes
   "First launch: fitting the scoring models on the synthetic cohort — one
   time, about ten seconds. Later runs load instantly."
4. Annotate `internal/issues` line 1 with the answer (expected one-time fit +
   what we changed), same annotate-don't-overwrite convention as last round.
Tests: pickle with wrong version is rejected (unit-level on `_load_prefit`
with a tmp path); existing 161 stay green.
Acceptance: fresh checkout → `make demo` → Home paints without a multi-second
model fit; deleting `engine.pkl` still works (falls back to fit).

### WP-G — Pipeline live-output pane + wide layout
Files: `app/frontend/pages/2_Pipeline.py`, `app/frontend/components/stage.py`
(only if a helper needs a param), `app/frontend/static/custom.css` (append
new blocks only — WP-I edits other CSS sections in Wave 1).
1. Layout, both views: `left, right = st.columns([1, 1.6])`. Left: stage
   rail + progress. Right: `detail_ph = right.empty()` — the live stage
   output now animates on the right in Simple AND Technical view. Technical
   adds `console_ph = right.empty()` BELOW the live pane (height ~220px via
   a `.cp-console.short` variant; keep tail behaviour). Simple: no console.
2. Keep: ingestion breadth-reveal (`upto=` loop) now targets the right pane;
   per-stage completed cells accumulate below (unchanged); after the run the
   live pane clears and the last cell expands (unchanged); Instant/Replay
   unchanged.
3. Subtle entrance animation for the live pane content: CSS fade/slide-in on
   the live container (e.g. `.cp-live { animation: cp-in .25s ease }`),
   disabled under `prefers-reduced-motion` (extend the existing block).
4. Width/margins (page-global, in CSS): `.block-container { max-width:
   1500px; padding-left: 2rem; padding-right: 2rem; }`; sidebar pinned
   narrow: `[data-testid="stSidebar"] { min-width: 15rem; max-width: 15rem; }`
   (verify the 1.39 selector actually bites; use the section-level testid).
Tests: `test_frontend_smoke.py` still passes both modes; no orchestrator
changes at all.
Acceptance: during a staged run, every stage's headline/findings/viz appears
on the right as it generates, in both views; Technical also shows the
scrolling console; nothing renders below-left of the rail except the notebook
cells; noticeably wider content area, slimmer sidebar.

### WP-H — Peer-grouping palette
Files: `app/frontend/components/charts.py` only.
Replace `_CLUSTER_COLORS` with a deeper elegant categorical set — e.g.
`["#0b3d75", "#0e7c66", "#b3541e", "#6b4fa1", "#8f5c13"]` — marker opacity
0.75, size 8, `line=dict(width=0.5, color="#ffffff")`. Check the actual tier
labels at runtime: if tiers are ordered risk bands, order the palette
cool→warm accordingly (never neon). Entity star stays navy.
Acceptance: groups clearly distinguishable on a white background at a glance;
still "banking-elegant" (no saturation spikes); Explainability + Pipeline
clustering charts both pick it up (shared function).

### WP-I — Chrome: top-right toggle, sidebar brand first, Architecture trim
Files: `app/frontend/components/ui.py`, `app/frontend/static/custom.css`
(sidebar/toggle sections), `app/frontend/pages/5_Architecture.py`,
`app/tests/test_frontend_smoke.py` (adapt toggle driving).
1. `page_setup()`: drop the sidebar radio; render a top-right control row
   before returning: `_, c = st.columns([5, 1.4])` → horizontal
   `st.radio(..., options=["simple","technical"], key="cp_view_mode",
   horizontal=True, label_visibility="collapsed")`, styled as a compact pill
   (CSS on that radio's container; keep the keyboard focus ring). Session-key
   contract (`cp_view_mode` = "simple"/"technical") unchanged.
2. Sidebar: brand block stays (only sidebar content now); CSS flex-reorder so
   it sits ABOVE the page nav (inspect DOM: `stSidebarContent` children;
   nav `order:1`, user block `order:0`). Fallback-safe.
3. Architecture: delete the Module-boundaries + Deployment cards; keep the
   graphviz flow, sources, model stack, composites, and the synthetic-data
   honesty note. The Simple-view banner copy "switch to **Technical** view in
   the sidebar" must be updated (it's now top-right) — grep all pages/docs
   for the phrase "in the sidebar".
4. Update `docs/demo-script.md` if it references the sidebar toggle.
Tests: smoke tests updated to drive the relocated radio; jargon sweep
unchanged; glossary test unchanged.
Acceptance: toggle visible top-right on all 6 pages and persists across page
switches; brand on top of sidebar above nav; Architecture shows no
module/deployment engineering cards in either view.

### WP-V — Verification sweep (after Waves 1–2)
1. `pytest app/tests` → all green (count will be ≥162 with WP-F's new test).
2. AppTest both-modes sweep (pattern of `verify_union.py`): every page
   renders 0 exceptions in Simple + Technical; jargon-clean Simple copy.
3. Manual: `make demo`, confirm first-launch feel, staged reveal on the
   right, palette, toggle position, sidebar brand.
4. Annotate `internal/issues` per item (append `→ done: …` notes, don't
   rewrite the user's text).

---

## 3 · Guardrails (unchanged from round 1, plus)
- G1 Frontend renders only — no computation or copy generation moves into
  pages/components.
- G2 Banned-jargon list still enforced on all Simple-mode copy; the
  `cp_view_mode` contract must not change shape.
- G3 No new dependencies; Streamlit is pinned 1.39 (no `st.segmented_control`).
- G4 Any new motion respects `prefers-reduced-motion`.
- G5 CSS ownership: Wave 1 (WP-I) touches sidebar/toggle sections; Wave 2
  (WP-G) appends layout/live-pane/console blocks. No overlapping edits.
- G6 Do not commit; leave everything on `feature/ui-humanization`.
