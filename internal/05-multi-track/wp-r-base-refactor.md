# WP-R — Base-layer refactor: one platform shell, three track groups (Wave 1)

**Goal:** convert the app from a single-track PS3 demo into the **CreditPulse Platform** shell with grouped navigation, a platform Overview landing page, shell-owned chrome, and the **track-isolation layout of README §1a** — WITHOUT changing any PS3 behaviour. Track 04/05 groups appear with placeholder pages that WP-4A/WP-5A will replace.

**README §1a is binding for this WP:** PS3 code moves into `app/tracks/t03_financial_health/` (git mv + import fixes; run the suite after each move batch); the registry auto-detects installed tracks; `rm -rf` of any track folder must leave a working app. The R-task list below predates §1a in a few path spellings — §1a wins.

## Read first
- `internal/05-multi-track/README.md` (all) and `wp-s-findings.md` (follow it; it supersedes assumptions here)
- `app/frontend/Home.py`, all of `app/frontend/pages/`, `components/ui.py`, `components/state.py`, `static/custom.css`
- `app/tests/test_frontend_smoke.py`, `app/tests/conftest.py`
- `Makefile`, `Dockerfile`, `docs/demo-script.md` (grep for page references)

## Tasks

### R1 — Track registry (`app/frontend/tracks.py`)
Declarative single source of truth consumed by the router and the Overview page:
```python
# Each entry: group label, track badge, list of (path, title, icon, default?)
TRACKS = [
    Track(id="platform", label="Platform",
          pages=[P("pages/0_Overview.py", "Overview", default=True)]),
    Track(id="t03", label="Track 03 · Financial Health", badge="PS3",
          pages=[P("Home.py", "Run Assessment"),
                 P("pages/1_Dashboard.py", "Dashboard"),
                 P("pages/2_Pipeline.py", "Assessment Pipeline"),
                 P("pages/3_Financial_Health_Card.py", "Financial Health Card"),
                 P("pages/4_Explainability.py", "Explainability")]),
    Track(id="t04", label="Track 04 · Early Warning", badge="PS4",
          pages=[P("pages/6_Portfolio_Overview.py", "Portfolio Overview"),
                 P("pages/7_Watchlist.py", "Watchlist & Cases")]),
    Track(id="t05", label="Track 05 · Fraud Intelligence", badge="PS5",
          pages=[P("pages/8_Fraud_Desk.py", "Fraud Desk"),
                 P("pages/9_Case_Investigation.py", "Case Investigation")]),
    Track(id="ref", label="Reference",
          pages=[P("pages/5_Architecture.py", "Architecture")]),
]
```
(Use whatever tiny dataclass/tuple shape reads cleanest; exact icons/labels may be polished.)

**§1a overrides to this sketch:**
- Page files live under track folders: `app/tracks/t03_financial_health/pages/run_assessment.py` (the moved Home.py) etc.; platform pages under `app/frontend/pages/platform/overview.py`. `st.Page` accepts arbitrary paths — the registry is the only place that knows them.
- **Auto-detection:** each registry entry declares its track folder; build the nav only from folders that exist (`Path(app/tracks/<id>).exists()`), so deleting a track folder silently removes its group, its Overview card, its prefit warm, and its tests. Platform + Reference groups always present.
- **Stable URLs (D11):** `st.Page(..., url_path=...)` — Overview default (root), `track03` on Run Assessment, `track04` on Portfolio Overview, `track05` on Fraud Desk. Cold-session deep-link into each must render (T03 pages already guard via `require_assessment`; verify the start pages specifically).
- **Isolation linter test** (platform tests): walk `app/tracks/*/**.py` ASTs/imports — fail on any `app.tracks.<other>` import. Also: `app/frontend`, `app/ml`, `app/data_gen`, `app/backend` core must not import from `app.tracks.*` **except** via the registry's guarded discovery points (registry, prefit, state engine wrappers).
- **Makefile:** `test:` runs `pytest app/tests app/tracks`; each track carries its own `tests/` so deletion removes them.

### R2 — Router (`app/frontend/app.py`)
- sys.path bootstrap (same pattern as Home.py).
- `ui.shell_setup()` (see R3) BEFORE `st.navigation`.
- Build `st.navigation({t.label: [st.Page(p.path, title=p.title, ...) for p in t.pages] for t in TRACKS}, position="sidebar")`, run it.
- Per wp-s-findings: `st.set_page_config` lives here only.

### R3 — Chrome split (`components/ui.py`)
- `shell_setup()`: set_page_config, CSS injection (both first-paint markdown + `_inject_css` head copy), sidebar brand block, the top-right Simple/Technical toggle (unchanged semantics, key `cp_view_mode`), any engine-warm spinner copy.
- `page_header(title, caption=None)`: renders the page h1/caption (extract the current per-page pattern).
- Remove the per-page `page_setup(...)` calls from Home.py + pages 1–5, replacing with `page_header(...)`. If wp-s-findings recommends keeping a no-op-ish `page_setup` shim for a smaller diff, do that and note it.
- The view toggle must render exactly once per rerun (router), positioned as today (top-right). Verify no duplicate-widget-key errors on page switches.

### R4 — Overview landing (`pages/0_Overview.py`)
Platform pitch page, default. Content (Simple/Technical aware, all static copy — no computation):
- Brandmark h1 + caption: "One platform, three problem statements · IDBI Innovate 2026 · all data synthetic".
- One-paragraph platform story: *underwrite the credit-invisible (T03) → monitor the book (T04) → protect the rails (T05)* — same engines, same explainability discipline.
- Three track cards (reuse `.cp-card` styling): each with badge, 2-line description, headline capability list, and `st.page_link` to the track's first page.
- The architecture one-liner + link to Reference→Architecture.
- Honesty note (`st.info`) mirroring the README's synthetic-data statement.

### R5 — Placeholder pages for T04/T05
Create the four new page files as minimal "coming online" stubs with correct `page_header`, one-sentence track description, and `st.page_link` back to Overview — just enough for nav + smoke tests until WP-4A/5A replace them. Skeleton-copy an existing page (bootstrap block included).

### R6 — Link + copy sweep
- Update every `st.switch_page`/`st.page_link` target if wp-s-findings requires a different path form (grep list: Home.py:80,82; state.py:55; stage.py:301; pages/1:89–92; pages/3:112–114; pages/4:81–83; re-grep to be exhaustive).
- Home.py: retitle to its Track-03 role ("Run Assessment") — keep ALL existing content/behaviour; adjust the h1 if it duplicates Overview's brandmark treatment (Overview owns the brandmark hero now; Home keeps a normal page header).
- Grep pages/docs for copy that says "Home" navigation ("New assessment" links can stay pointing at Home.py).
- Architecture page: extend the diagram/copy minimally to mention three tracks sharing one stack (full doc rewrite is WP-V's).

### R7 — CSS (shell/nav sections — WP-R owns these blocks)
- Style nav group headers (`st.navigation` renders section labels — selector per wp-s-findings) to the Ledger look: small caps/letter-spacing, muted ink, spacing above groups.
- Track badges styling for Overview cards (`.cp-track-badge`).
- Verify brand-above-nav ordering still holds under the new DOM; fix selectors if needed.
- Respect `prefers-reduced-motion` for anything animated. Keep the brace-balance discipline (count `{`/`}` before/after).

### R8 — Test migration (structural edits — WP-R owns)
- `test_frontend_smoke.py`: `_HOME` → `_APP = app/frontend/app.py`; `_drive()` boots app.py, seeds session keys individually (SafeSessionState has no `.update`), then `at.switch_page(rel_page)` per wp-s-findings convention. `_PAGES` list gains `pages/0_Overview.py` and the four placeholders (render-only assertion for placeholders at this stage).
- Keep every existing assertion (verdict on Health Card, SHAP in technical explainability, jargon sweep pages 1–4 + Overview; Architecture stays exempt).
- Any other test referencing Home.py as entrypoint: grep `AppTest|Home.py` across `app/tests` and update.
- Add `test_tracks_registry.py`: every registry path exists on disk; titles unique; exactly one default page; every `pages/*.py` file is registered (no orphans).

### R9 — Makefile/Dockerfile
- `demo:` target now runs `streamlit run app/frontend/app.py ...` (keep flags/port identical).
- Dockerfile CMD likewise. Nothing else changes in this WP.

## Acceptance
- **Isolation proof:** in a scratch copy, `rm -rf app/tracks/t04_early_warning app/tracks/t05_fraud_intelligence` → `make test` green and `make demo` boots a PS3-only platform (Overview shows one track card). Restore and re-verify full app. Isolation-linter test green.
- **Deep links:** `/track03` (and root) load cold; `/track04`, `/track05` load their placeholders cold.
- `make demo`: app opens on Overview; sidebar shows 5 groups; all Track-03 flows work exactly as before (run assessment → pipeline animation → health card → explainability, both view modes, staged AND instant).
- `make test` green: full suite, count ≥ previous (166) + new registry tests; no assertion deletions.
- No FOUC regression on nav clicks (the head-CSS injection still applies; check by rapid page switching).
- View toggle appears once, top-right, on every page including new placeholders; `cp_view_mode` persists across switches.
- Report: exact switch_page/page_link convention used, selector changes made, and the final `_drive()` recipe — WP-4A/5A will copy it.
