# WP-S — Navigation spike (Wave 0, serial, ~half day)

**Goal:** de-risk the `st.navigation` migration BEFORE the full refactor. Produce working proof + a short findings note that WP-R will follow. This WP is throwaway-friendly: prefer the smallest change that answers the questions.

## Read first
- `internal/05-multi-track/README.md` (§2 D1–D2)
- `app/frontend/Home.py` (entrypoint today), `app/frontend/components/ui.py` (`page_setup`, `_inject_css`), `app/frontend/components/state.py`
- `app/tests/test_frontend_smoke.py` (how AppTest drives pages today: boots `Home.py`, `at.switch_page("pages/1_Dashboard.py")`)
- `app/frontend/static/custom.css` — sidebar blocks: brand ordering (`stSidebarUserContent` / `stSidebarNav` flex order), collapse-control hiding, nav link styling

## Questions this spike must answer (each → a bullet in the findings note)

1. **Router shape.** Create `app/frontend/app.py`: sys.path bootstrap (copy from Home.py), then `st.navigation({...groups...})` registering `Home.py` + the five existing pages with groups ("Track 03 · Financial Health" etc. — final labels in WP-R), `nav.run()`. Confirm `streamlit run app/frontend/app.py` shows grouped sidebar nav with 1.39.
2. **set_page_config placement.** Today every page calls `page_setup()` → `st.set_page_config`. Under `st.navigation` the router runs first on every rerun: establish whether `set_page_config` should live ONLY in the router (expected) and what happens if a page also calls it (expected: exception or warning). Decide the migration rule.
3. **CSS + sidebar DOM.** With `st.navigation`, inspect the sidebar DOM (testids). Verify: (a) brand-above-nav still holds or needs a selector update; (b) nav-group section headers get a styleable element; (c) the `_inject_css` head-injection still prevents nav-flash. Note any selector changes needed.
4. **In-app links.** Confirm `st.switch_page("pages/2_Pipeline.py")` and `st.page_link("Home.py", ...)` still work when those pages are registered via `st.navigation` (path-string form). If they require `st.Page` objects, define the pattern (import the registry from `tracks.py` and link by object or by path constant).
5. **AppTest.** Port ONE smoke test locally (do not commit changes to the suite in this WP): `AppTest.from_file(app.py)` → default page renders → `at.switch_page("pages/1_Dashboard.py")` → renders. Confirm: switch_page path convention under st.navigation, session_state seeding still works, and the view-toggle radio still appears once per page. If `AppTest.from_file(app.py)` has issues with `nav.run()`, document the workaround (e.g., driving pages via `at.switch_page` immediately after first run).
6. **Radio/widget indices.** The smoke suite and verify scripts rely on widget iteration (e.g., view toggle = `radio` with `key="cp_view_mode"`). Confirm the router-owned toggle appears exactly once and is discoverable by key (never by index).
7. **url_path + arbitrary page locations.** Confirm `st.Page("some/nested/dir/file.py", url_path="track03")` works in 1.39 (pages outside `pages/`, e.g. a `tracks/t03/pages/` folder), that the URL bar shows the custom path, and that a cold browser hit on `/track03` routes correctly. Also confirm how `at.switch_page` addresses such pages (path string relative to entrypoint? the registered path?) — WP-R's test migration depends on the answer.

## Deliverables
- `app/frontend/app.py` (minimal working router — WP-R will finish it)
- `internal/05-multi-track/wp-s-findings.md` — numbered answers to the six questions, incl. exact selector/API notes and the AppTest port recipe; flag anything that changes WP-R's task list
- Existing test suite still green (`make test`) — the old `Home.py` entry path must keep working until WP-R lands (pages/ dir still exists, so the legacy auto-nav app still runs; do not delete anything)

## Acceptance
- Grouped nav demonstrably works in the browser (screenshot or precise text description in findings)
- The one-off AppTest port runs green locally
- `make test` still 166 green
- Findings note complete enough that WP-R needs no further research
