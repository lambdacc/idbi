# UI Review — CreditPulse (Streamlit) · 02 Jul 2026

> **For the implementer:** every `screenshots/…` path below refers to `ui-review/screenshots/`
> at the repo root — a local, gitignored evidence folder. If it's missing, regenerate it:
> start the app (`make demo` on port 8599 or edit `BASE`), then run
> `python internal/ui-review/capture_screenshots.py` (needs `pip install playwright` +
> `playwright install chromium`). Re-run the same script after implementing fixes to
> verify against the same states/viewports. Findings are ordered by user impact;
> the finding descriptions are self-contained enough to implement without the images.

## Summary

The app is in strong shape for a demo: the nine-stage pipeline reads as a real product, the inflated-turnover case tells its story clearly (benign PD + red authenticity + the exact right first risk), reason cards and empty-state copy are good, and mobile stacking mostly works. The single highest-leverage change is fixing the **composite-vs-dimensions coherence problem**: the hero proclaims 94/100 while every visible dimension sits at 54–79, and nothing on screen explains the gap — the first sharp question any credit-domain judge will ask. Second priority is the ~820px tablet layout, which squeezes rather than adapts.

## Findings

### [P1] The composite score visibly contradicts its own dimensions
- **Where:** Financial Health Card + Dashboard, all data states; most glaring in `typical` (94/100 vs dims 54/63/62/79/76) and `thinfile` (66 vs a 27 in the list)
- **Evidence:** `screenshots/healthcard__typical__1440.png`, `screenshots/dashboard__typical__1440.png`, `screenshots/healthcard__thinfile__1440.png`
- **Problem:** The hero says **94/100, Grade 1, Approve** while the radar shows a modest mid-sized pentagon and the adjacent score list shows a red-badged 54 as the *best-available framing of the same business*. The composite is cohort-calibrated (frozen reference distribution) while the dimension scores are absolute — but the UI presents both as the same 0–100 currency, so the reader concludes the arithmetic is wrong. For a scoring product whose entire pitch is explainability, an unexplained 94-from-a-max-79 is a credibility hole, not a cosmetic one.
- **Recommendation:** Don't change the math — label the two scales. (1) Under the hero score, add a one-line subtitle: *"Cohort-calibrated composite — percentile-based, not an average of the dimensions."* (2) In the Dimension Scores header add a caption: *"Absolute dimension scores (0–100); the composite ranks this business against the full cohort."* (3) Optionally add the cohort-average pentagon as a faint second trace on the radar (`go.Scatterpolar` with dashed grey line) so the "better than peers" story becomes visible instead of contradictory. All three are copy/one-trace changes in `3_Financial_Health_Card.py`, `1_Dashboard.py`, `charts.radar`.
- **Effort:** S

### [P2] Peer-group badge reads as a verdict, and sometimes a contradictory one
- **Where:** Health Card hero + Dashboard hero, `inflated` and `thinfile` states
- **Evidence:** `screenshots/healthcard__inflated__1440.png` (badge "Growing / Stable operators" directly above **Recommendation: Decline**), `screenshots/healthcard__thinfile__1440.png` (a 6-year micro kirana on review band labelled "Established / Strong performers")
- **Problem:** In the hero, the K-Means cluster name appears as a bare pill with no qualifier. A cluster label is *descriptive* ("who this business resembles"), but placed beside grade/recommendation it reads as a second, conflicting judgment — "Growing / Stable operators… Decline?" The Dashboard's KPI card handles this correctly ("K-Means (descriptive only)"); the heroes don't.
- **Recommendation:** In both heroes, prefix the badge text: `badge("Peer group: " + hc.peer_segment, "info")`, and move it off the badge row onto the subtitle line (`… · Peer group: Established / Strong performers`). Also revisit `clustering.py`'s segment names — at k=3–5 the labels are coarse enough that a review-band kirana lands in "Established / Strong performers"; neutral names ("Peer group A — service-led micro", …) or score-band-agnostic names avoid implying a verdict.
- **Effort:** S

### [P2] ~820px gets a squeezed desktop layout, not a tablet layout
- **Where:** Health Card (and by construction every two-column page) at the 820 viewport
- **Evidence:** `screenshots/healthcard__typical__820.png`
- **Problem:** At 820px the sidebar stays expanded (Streamlit only auto-collapses below ~768px), leaving ~480px of content while every `st.columns([1,1])` pair stays side-by-side. The radar shrinks to an unreadable disc with clipped axis labels ("ess", "file", "Growth Tr"), and the score badges deform into large ovals. The page is technically responsive but cognitively broken — nothing is readable at the exact width of an iPad in portrait, a plausible judge device.
- **Recommendation:** Two Streamlit-native moves: (1) `st.set_page_config(initial_sidebar_state="collapsed")` in `ui.page_setup` — the in-body nav links already cover navigation, the demo opens cleaner, and content width roughly doubles at tablet sizes; (2) give charts a floor: `fig.update_layout(autosize=True)` plus a CSS `min-width: 320px; overflow-x: auto` on `[data-testid="stPlotlyChart"]` so the radar never collapses below legibility. If keeping the sidebar expanded matters for the demo, instead break the radar/score pair with `st.columns([1,1], gap="large")` → single column below ~900px is not natively expressible, so the sidebar collapse is the pragmatic lever.
- **Effort:** M

### [P2] Radar axis labels clip at narrow widths
- **Where:** Health Card + Dashboard radar, 390 and 820 viewports
- **Evidence:** `screenshots/healthcard__typical__390.png` ("rthiness", "Re" cut at both edges), `screenshots/healthcard__typical__820.png`
- **Problem:** Plotly polar charts don't automargin angular labels; "Creditworthiness" and "Repayment Capacity" run off the plot area, so on a phone the radar loses exactly the dimension names it exists to show.
- **Recommendation:** Pass short labels to the radar only — `{"Repayment Capacity": "Repayment", "Growth Trajectory": "Growth", "Creditworthiness": "Credit", "Risk Profile": "Risk", "Stability & Vintage": "Stability"}` in `charts.radar` — the full names already live in the adjacent Dimension Scores list, so nothing is lost; and bump `margin=dict(l=40, r=40)` for the radar specifically.
- **Effort:** S

### [P2] Model PD renders as "0.0%"
- **Where:** Dashboard risk KPI + Health Card KPI row, `typical` state
- **Evidence:** `screenshots/dashboard__typical__1440.png` ("Model PD 0.0% · score 784/900")
- **Problem:** No real credit model outputs a zero default probability; "0.0%" reads as a bug or an overfit model to exactly the audience this demo targets. It's a formatting artifact (`{pd:.1%}` on 0.0004).
- **Recommendation:** Floor the display, not the value: `f"<0.1%" if out['pd'] < 0.001 else f"{out['pd']:.1%}"` — one helper in `ui.py`, used in the three PD renderings (Dashboard, Health Card, Pipeline scoring stage).
- **Effort:** S

### [P2] Body nav links intercept each other's clicks
- **Where:** Health Card / Dashboard / Explainability bottom nav rows (`st.columns` of `st.page_link`)
- **Evidence:** reproduced mechanically — Playwright could not click "Why this score (Explainability)" because the adjacent Dashboard link's `stColumn` subtree intercepts pointer events (see audit log; required `force=True`). Not a screenshot-visible defect, but a real hit-target overlap at 1440.
- **Problem:** The long label "🔍 Why this score (Explainability)" extends under the neighbouring column, so part of its visible text is unclickable — users clicking the right half of the label get the wrong page or nothing.
- **Recommendation:** Shorten the label to "🔍 Explainability" (labels should be short and parallel anyway: Pipeline · Health Card · Explainability · New Assessment), and add `gap="medium"` to the nav `st.columns`. Verify with a plain click (no force) after the change.
- **Effort:** S

### [P3] Mid-run stage detail lags the stage list by one stage
- **Where:** Pipeline page during the staged reveal
- **Evidence:** `screenshots/pipeline-mid__typical__1440.png` — stage list shows "4 · Feature Engineering — RUNNING" while the detail panel still shows "Stage 3 · Data Integration"
- **Problem:** For the several seconds a stage's console lines are printing, the header/list says stage N while the big detail panel shows stage N-1 — a small but noticeable "is it broken?" flicker in the one view judges watch most closely.
- **Recommendation:** In `2_Pipeline.py`'s play loop, render a lightweight detail header (`#### Stage {s.index} · {s.title}` + caption only) into `detail_ph` *before* printing the stage's log lines, then the full `render_detail(s)` after — the panel then always names the running stage.
- **Effort:** S

### [P3] Small polish set
- **Instant vs Replay have identical visual weight** (`pipeline-complete__typical__1440.png`) — make Replay secondary: `st.button("↻ Replay", type="secondary")` and style `.stButton > button[kind="secondary"]` as an outline button.
- **SHAP label casing is inconsistent** (`explainability__inflated__1440.png`: "epfo total wage bill" beside "Operational Stability") — in `stage.feature_label`, title-case the fallback: `fname.replace("_", " ").title()` with acronym fix-ups (GST, EPFO, UPI, DSCR).
- **Plotly modebar appears on hover** (camera/zoom icons in `explainability__inflated__1440.png`) — pass `config={"displayModeBar": False}` to every `st.plotly_chart` for a product feel.
- **Empty states are a bare info bar on a blank page** (`healthcard__empty__1440.png`) — the copy is right, the placement isn't: in `state.require_assessment`, render the page title first and add `st.page_link("Home.py", label="Go to Home")` before `st.stop()`.
- **Peer-segment KPI card breaks the row rhythm** (`dashboard__typical__1440.png`) — its two-line value makes one card taller than its row; render long segment names at a smaller value size (a `.cp-kpi .val.small` variant) or put the segment in the `sub` slot.

## Quick wins

- PD floor display ("<0.1%") — one helper, three call sites
- Short radar axis labels + wider polar margins
- "Peer group:" prefix on the hero badge
- `config={"displayModeBar": False}` on all Plotly charts
- Shorten nav link labels + `gap="medium"` (also fixes the click interception)
- Empty-state: title + Home link before `st.stop()`
- Replay as secondary button
- Title-cased SHAP fallback labels

## What's already good (no action)

Mobile (390px) stacking is genuinely clean — pipeline stages, reason cards, and the scenario picker all read well (`pipeline-complete__typical__390.png`, `home__fresh__390.png`, `explainability__typical__390.png`). The inflated-case storytelling is exactly right: benign PD, red Turnover-Authenticity, and the correct flagship risk sentence first (`explainability__inflated__1440.png`). The execution console + stage list carry the "live pipeline" feel without gimmicks, and the sidebar collapse control survives on mobile after the header fix.
