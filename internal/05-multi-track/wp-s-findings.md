# WP-S — Navigation spike findings

**Streamlit pinned at 1.39.0** (verified: `.venv/bin/python -c "import streamlit; print(streamlit.__version__)"` → `1.39.0`). Every claim below was proven by running headless `AppTest` and/or reading the installed source under `.venv/lib/python3.12/site-packages/streamlit/`, not from docs. Deliverable router: `app/frontend/app.py`. Legacy `Home.py` + `pages/` auto-nav entry path is untouched and still green (the 166-test suite drives it).

The one pivotal result up front: **`st.navigation` moves the app to "MPA v2", and under MPA v2 `AppTest` cannot execute file-path `st.Page` sources and `at.switch_page(...)` no longer targets the right page.** This reshapes WP-R's test migration — see Q5 and the "Changes to WP-R" section.

> ### ⚠ CRITICAL (post-spike, from live breakage) — the router MUST NOT be named `app.py`
> The spike's router file was `app/frontend/app.py`. **That name shadows the top-level `app` package.** When Streamlit runs the entrypoint it puts the entrypoint's directory (`app/frontend/`) on `sys.path`; then any `import app.backend…` / `from app.frontend…` (every page does this) resolves `app` to the router *file* `app/frontend/app.py` instead of the `app/` package directory, raising `ModuleNotFoundError: No module named 'app.backend'; 'app' is not a package`. Worse, the file's mere presence breaks **every** entrypoint in that folder — including the legacy `Home.py` / `make demo` — not just the router.
> **Binding decisions for WP-R:**
> 1. **Name the router `app/frontend/main.py`** (no collision with the `app` package; `main` is imported by nothing). Everywhere this findings note or the plan says `app.py`, read `main.py`.
> 2. **Harden the bootstrap:** insert the repo root at `sys.path[0]` *unconditionally* (`sys.path.insert(0, str(_ROOT))` without the `if not in sys.path` guard, and after removing any pre-existing entry), so the entrypoint's own directory can never win the `import app` resolution regardless of prior `sys.path` state.
> 3. `Home.py` keeps working throughout because it has no name collision; only the new entrypoint needed renaming. The spike router file has been deleted (throwaway); the 166-test suite is green.

---

## Q1 — Router shape (grouped `st.navigation`)

**Answer: works.** `app/frontend/app.py` does the Home.py sys.path bootstrap, builds a declarative dict `{section_header: [st.Page(...), ...]}`, and calls `nav = st.navigation(NAV); nav.run()`. Proven:

- `AppTest.from_file("app/frontend/app.py")` runs with **no exception**; captured the emitted `Navigation` proto:
  - `sections = ['Track 03 · Financial Health', 'Reference']` (dict keys become section headers, in insertion order);
  - 6 pages registered; `st.Page("Home.py", default=True)` → `url_path=""` (root); the rest inherit filename-derived url paths.
- `streamlit run app/frontend/app.py --server.port 8919 --server.headless true`: `/` → 200, `/_stcore/health` → `ok`, deep-link `/Dashboard` → 200, no startup errors.

Notes for WP-R:
- **Section order = dict insertion order.** Put Platform/Overview first, then Track 03/04/05, then Reference.
- `st.navigation(pages, position="sidebar", expanded=False)` are the defaults. With many pages and `expanded=False`, Streamlit adds a **"view more" button** (`stSidebarNavViewButton`, see Q3). Consider `expanded=True` to always show every group, or hide that button in CSS.
- **Filename→url_path inference strips the numeric ordering prefix**: `pages/1_Dashboard.py` → url_path `"Dashboard"` (NOT `"1_Dashboard"`); `pages/3_Financial_Health_Card.py` → `"Financial_Health_Card"`. WP-R assigns explicit `url_path=` per D11 anyway (`track03/04/05`), so don't rely on inference.

---

## Q2 — `set_page_config` placement

**Answer: `set_page_config` must live in EXACTLY ONE place per run; a second call raises.** Migration rule: **the router (or the single selected page) owns it — never both.**

Mechanics (from `runtime/scriptrunner_utils/script_run_context.py:171-182`): `_set_page_config_allowed` starts `True` each rerun and flips to `False` after the first `page_config_changed` message **or** after any other delta once the script has started. So the config command must be the *first* Streamlit command of the run.

Proven with `AppTest`:
- Router calls `st.set_page_config(...)` then `nav.run()` and the page *also* calls `st.set_page_config(...)` → **raises `StreamlitSetPageConfigMustBeFirstCommandError`**: *"`set_page_config()` can only be called once per app page, and must be called as the first Streamlit command in your script."*
- Router calls **no** chrome, single page calls `set_page_config` first → **no exception** (this is exactly the shape of the minimal `app.py` in this spike: it emits no deltas before `nav.run()`, so the selected page's own `page_setup()` → `set_page_config` is still the first command and succeeds — which is why the spike router works against the un-modified pages).

**Rule for WP-R (implements README D2):** move `set_page_config` **into the router** (`ui.shell_setup()` called once at the top of `app.py`, before `nav.run()`). Then **delete `set_page_config` from every page** — `ui.page_header(title)` must NOT call it. The current `page_setup()` (which calls `set_page_config` + brand + view toggle + CSS) cannot survive being called by both router and page; split it per D2. NB: because the router will emit sidebar deltas (brand, view toggle) *before* `nav.run()`, `set_page_config` must be the router's literal first Streamlit call, ahead of the CSS/brand/toggle.

---

## Q3 — CSS + sidebar DOM under `st.navigation`

Confirmed testids present in the 1.39 frontend bundle (`static/js/*.js`) and their nesting:

```
stSidebarContent                     (flex column; children below)
├── stSidebarHeader                  (has stSidebarCollapseButton, stLogoSpacer)
├── stSidebarNav                     (rendered by st.navigation, position="sidebar")
│   ├── stSidebarNavItems            (the list)
│   │   └── stNavSectionHeader       (one per group; only when the section label is truthy)  ← NEW
│   │   └── stSidebarNavLink         (each page link; is an <a href> — `Vs=(0,Ce.A)("a")`)
│   ├── stSidebarNavSeparator
│   └── stSidebarNavViewButton       (the "view more options" toggle when expanded=False)
└── stSidebarUserContent             (everything you render via st.sidebar.* — e.g. the brand)
```

Per-question:

- **(a) brand-above-nav still holds.** The brand is `st.sidebar.markdown(...)` → lands in `stSidebarUserContent`; the nav is `stSidebarNav`; both are direct children of the flex `stSidebarContent`. The existing reorder blocks (`custom.css:112-114`) `stSidebarUserContent {order:1}` / `stSidebarNav {order:2}` **continue to apply unchanged**. WP-R: keep them; just re-verify in-browser after the shell move.
- **(b) nav-group section headers ARE styleable** — the new element is **`[data-testid="stNavSectionHeader"]`** (did not exist under auto-nav, which had no groups). WP-R adds a CSS block for it (light-on-navy, letter-spaced small caps to match `.cp-tag`). This is a **net-new selector WP-R must author.**
- **(c) `_inject_css` head-injection still prevents nav-flash.** Unchanged and still needed: it writes the stylesheet into the *top* document `<head>` keyed `#cp-head-css`, which survives reruns. Under `st.navigation` the router runs every rerun, so WP-R should call the head-injection **from the router (`shell_setup`)** once — that actually makes it *more* robust than today (today each page re-injects).

**Selector changes WP-R must make:**
1. **Add** `[data-testid="stNavSectionHeader"]` styling (new grouped-nav headers).
2. **Link base styling survives:** `stSidebarNavLink` is a real `<a>` under `stSidebarNav`, so the existing `[data-testid="stSidebarNav"] a { … }` rules (`custom.css:117-124`) keep matching. Optionally tighten to `[data-testid="stSidebarNavLink"]` for clarity.
3. **Active-link override is at risk:** the active state is applied via the styled-component's `isActive` prop (emotion class `eczjsme14`), and the nav link does **not** emit `aria-current="page"` (the only `aria-current` in the bundle is the date-picker's). So `custom.css:123-124` `a[aria-current="page"] { … }` likely will **not** match under `st.navigation`. WP-R: either accept Streamlit's built-in active highlight, or restyle via `[data-testid="stSidebarNavLink"]` (there is no stable per-link active attribute — an `:has()`/built-in approach is the fallback). **Flag: verify the active-link highlight in-browser and adjust this block.**
4. **Consider** hiding/838 or ignoring `stSidebarNavViewButton` (or set `expanded=True`) so all track groups are always visible.
5. `stSidebarCollapseButton` hide (`custom.css:110`) is unaffected.

---

## Q4 — In-app links (`st.switch_page` / `st.page_link`)

**Answer: path-string links keep working IF the target page is registered by FILE PATH; they FAIL if it is registered as a callable — in which case you must pass the `StreamlitPage` object.**

Proven:
- Router registers `pipeline = st.Page("pages/2_Pipeline.py", ...)` (file path). A page then calls `st.page_link("pages/2_Pipeline.py")` **and** `st.switch_page("pages/2_Pipeline.py")` → **no exception, resolves correctly.** (`st.switch_page` source: it `realpath`-joins the string against the entrypoint dir and matches a registered page's `script_path`; file-path `st.Page`s populate `script_path`.)
- Same path-string against a **callable-registered** page → **`StreamlitPageNotFoundError`**: *"Could not find page: `pages/2_Pipeline.py`. … Only pages previously defined by `st.Page` and passed to `st.navigation` are allowed."* (callable pages have empty `script_path`, so string matching can't find them).

**Path convention:** strings are **relative to the entrypoint file** (`app/frontend/app.py`), same base dir as today's `Home.py`, so *existing* strings like `st.switch_page("pages/2_Pipeline.py")` and `st.page_link("Home.py")` keep working **as long as those exact files stay registered by path**. Once WP-R `git mv`s the pages into `app/tracks/t03_financial_health/pages/…`, every in-app link string must change to the new entrypoint-relative path.

**Recommendation (ties into Q5):** because AppTest can only render **callable** pages (Q5), and callable pages break path-string links, WP-R should **link by `StreamlitPage` object**, not by string — `st.page_link(registry.PIPELINE)` where `registry` is `tracks.py`. Object links match on `_script_hash` and work for *both* file- and callable-registered pages, and survive the t03 folder move with no string edits. Define a small accessor in `tracks.py` (e.g. `PAGES["t03.pipeline"]`).

---

## Q5 — AppTest port (**critical, changes WP-R**)

Two hard limits of `AppTest` under `st.navigation` (MPA v2) in 1.39, both proven and both traced to source:

### 5a. `AppTest` cannot execute **file-path** `st.Page` sources — the page renders BLANK (no elements, no exception)
- Booting `app.py` (file-path registry) and running the default page produced **0 markdown / 0 titles / 0 radios / no exception** — the page body never executed.
- Root cause: `AppTest.run()` builds `PagesManager(self._script_path, setup_watcher=False)` **without a `script_cache`** (`testing/v1/app_test.py:328`). `StreamlitPage.run()` fetches the page body via `pages_manager.get_page_script_byte_code(path)`, which returns `""` when `_script_cache is None` (`runtime/pages_manager.py:326-330`). So `exec("", module.__dict__)` runs nothing. This affects **file-path pages only.**
- **Callable** `st.Page(fn, ...)` pages execute fine under AppTest (the callable is invoked directly, no bytecode cache involved) — verified: callable Home renders "Choose a business", view toggle appears once.

### 5b. `at.switch_page(path)` does NOT navigate under `st.navigation`
- `AppTest.switch_page` sets `self._page_hash = calc_md5(<resolved FILE path>)` (`app_test.py:416`). But a `StreamlitPage`'s hash is `calc_md5(<url_path>)` (`navigation/page.py:307`). These never match, so navigation falls back to the **default** page. Proven: after `at.switch_page("pages/1_Dashboard.py")` the app stayed on the default page.
- The working lever is to set the page hash to the **url_path** hash directly:
  `at._page_hash = calc_md5(page.url_path); at.run()` → navigates correctly (verified: landed on Dashboard, "Five dimensions"/"What drove this"; landed on the nested page for Q7).

### The AppTest port recipe WP-R should adopt

Make `tracks.py` register pages as **callables with explicit `url_path=`** (a thin wrapper is enough — proven working:

```python
def _page_callable(file_path: str, fn_name: str):
    def _run():
        code = compile(Path(file_path).read_text(), file_path, "exec")
        exec(code, {"__name__": "__page__", "__file__": file_path})
    _run.__name__ = fn_name
    return _run
# st.Page(_page_callable(".../pipeline.py", "pipeline"), title="Pipeline", url_path="track03")
```
…or, cleaner, refactor each page file to expose a `render()` function and register `st.Page(render, url_path=...)`.

Then the smoke test becomes:

```python
from streamlit.util import calc_md5
_APP = str(_ROOT / "app" / "frontend" / "app.py")

def _drive(mode, assessment, url_path):
    at = AppTest.from_file(_APP, default_timeout=90)
    at.session_state["cp_view_mode"] = mode          # seed keys INDIVIDUALLY (SafeSessionState, no .update())
    at.session_state["cp_assessment"] = assessment
    at.session_state["cp_pipeline_played"] = True
    at.session_state["cp_instant"] = True
    at.run()                                          # default page (Overview/root)
    at._page_hash = calc_md5(url_path)                # NAVIGATE by url_path hash (NOT at.switch_page)
    at.run()
    return at
# pages addressed by their D11 url_path: "track03" (T03 start), "Dashboard"/… etc.
```

Confirmed with this recipe: session_state seeding still works; the **view-toggle radio appears exactly once** and is found by `key="cp_view_mode"` (never by index); pages render with 0 exceptions.

**Important corollaries for WP-R:**
- **`at.switch_page(...)` is dead under `st.navigation`.** Provide a test helper `def _goto(at, url_path): at._page_hash = calc_md5(url_path); at.run()` and use it everywhere.
- **Address pages by `url_path`, not by file path** — this is exactly why D11's stable `url_path`s (`track03/04/05`) are the right test handles, and it cleanly solves "pages that live OUTSIDE `pages/`" (e.g. `tracks/t03/pages/foo.py`): the test never names the file at all, only the `url_path`, so a page's on-disk location is irrelevant to the test (proven in Q7).
- The **existing 166-test suite is unaffected** and stays green: it boots `Home.py` (MPA v1 auto-nav, not `st.navigation`) and uses `at.switch_page` — which is the mode `at.switch_page` was built for. WP-R migrates the smoke test to `app.py` + the recipe above **at the same time** it moves the pages; do it as one atomic change so the suite is never red.

---

## Q6 — Radio / widget indices

**Answer: find by `key`, never by index; the router-owned toggle appears exactly once.** In every AppTest run above, `[r for r in at.radio if r.key == "cp_view_mode"]` returned **exactly one** element on the default page and after navigating. When WP-R moves the toggle into `shell_setup()` (router), it renders once per rerun before `nav.run()`; pages must NOT re-render it. Continue to locate it by `key="cp_view_mode"` (the CSS anchor is `.st-key-cp_view_mode`). The Home page's scenario picker is a separate `st.radio` with a different (auto) key, so key-based lookup unambiguously separates them — do not use `at.radio[0]`.

---

## Q7 — `url_path` + arbitrary page locations (deep links)

**Answer: a page file may live in ANY nested directory outside `pages/`; `url_path` is an independent, FLAT string. Both proven in 1.39.**

- `st.Page("_spk_nested/pages/foo.py", url_path="track03")` — a page file in a nested dir outside `pages/` — was **accepted** (the only check is file existence: `navigation/page.py:187`). The file location and the `url_path` are fully decoupled.
- A **cold hit on the url_path routes correctly**: first-run `at._page_hash = calc_md5("track03cb"); at.run()` landed directly on that nested page (title "NESTED FOO" rendered), no exception — this is the "cold browser hit on `/track03`" case. Live server confirmed the analogous `/Dashboard` deep link returns 200.
- **Constraint — `url_path` must be flat (no `/`).** Source (`navigation/page.py:224-228`) strips slashes and raises *"The URL path cannot contain a nested path (e.g. foo/bar)."* So `url_path="track03"` ✓ but `url_path="tracks/t03"` ✗. The *file* path may be nested; the *url* path may not. D11's flat `track03/04/05` are exactly right.
- `url_path=""` is rejected unless `default=True`; the default page always has `url_path=""` (root) and its `url_path=` is ignored.
- **URL uniqueness:** two pages with the same effective `url_path` raise *"Multiple Pages specified with URL pathname … must be unique"* (`commands/navigation.py:204-211`). The page hash is `calc_md5(url_path)`, so url_path collisions == hash collisions. WP-R must keep every `url_path` unique across all tracks.

**No CRITICAL blocker found for Q7** — nested locations + custom url_paths behave exactly as D11 assumes. The only "gotcha" is the flat-url_path rule, which D11 already respects.

---

## Changes to WP-R's task list (flagged)

1. **Test migration is bigger than a path swap.** `at.switch_page(...)` is unusable under `st.navigation`; replace it with `at._page_hash = calc_md5(url_path); at.run()` (helper `_goto`). Address pages by **`url_path`**, not file path. (Q5)
2. **Pages must be registered as CALLABLES (or `render()` functions), not bare file paths**, or the AppTest smoke sweep renders blank pages and silently passes. This is the single most important structural decision for `tracks.py`. If WP-R wants file-path registration for the real app, it still needs a callable/`render()` path for tests — recommend callables everywhere for one code path. (Q5)
3. **In-app navigation should link by `StreamlitPage` object, not by path string** (`st.page_link(registry.X)`), because (a) callable-registered pages reject path strings and (b) object links survive the t03 folder move with zero string edits. Add a page-object accessor to `tracks.py`. (Q4)
4. **New CSS selector required:** style `[data-testid="stNavSectionHeader"]` for the group headers. Re-verify the **active-link** highlight — `a[aria-current="page"]` likely no longer matches; restyle via `[data-testid="stSidebarNavLink"]` or accept the built-in. Keep the brand-above-nav order rules (they still apply). Decide `expanded=True` vs. hiding `stSidebarNavViewButton`. (Q3)
5. **`set_page_config` moves into the router as its literal first Streamlit call** and is **removed from all pages**; split `page_setup()` → `shell_setup()` (router) + `page_header(title)` (page) per D2. Do the head-CSS injection once from `shell_setup()`. (Q2/Q3)
6. **Migrate the smoke test atomically with the page move** so the 166-test suite is never red (it currently drives MPA v1 via `Home.py`, which is orthogonal to `st.navigation` and stays green until the switch). (Q5)
7. Assign **explicit, unique, flat `url_path`s** per D11 (`track03/04/05`); don't rely on filename inference (it strips numeric prefixes and would collide/confuse). (Q1/Q7)

## Environment / method notes for the next agent
- Tests: `.venv/bin/python -m pytest app/tests -q` (166 green pre/post spike). `.venv/bin/streamlit run app/frontend/app.py` serves the grouped nav.
- `AppTest` gotchas reconfirmed: `at.session_state` is `SafeSessionState` (no `.update()`); seed keys individually. Locate widgets by `key=`.
- The spike's throwaway experiment scripts live under the scratchpad; nothing was committed and no test files were added. Working tree after the spike: only `app/frontend/app.py` and `internal/05-multi-track/wp-s-findings.md` are new.
