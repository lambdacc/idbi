# CreditPulse — Manual Demo Script

**Purpose:** the documented walkthrough of the full 9-stage staged-reveal flow (implementation-plan.md §6.2),
with the expected on-screen content at each stage. Best run by a second person unfamiliar with the internals — the
"does a credit officer get it in 30 seconds?" test. Pairs with the automated smoke test
`app/tests/test_pipeline_orchestrator.py`.

**All data is synthetic.** State this out loud once at the start.

**Two things to point at up front (the UI-humanization pass):**
- Every page has a **View: Simple · Technical** toggle at the top right. It **defaults to Simple** — plain language, no model names — which is what a credit officer sees. Flip it to *Technical* to expose model internals (SHAP, K-Means, execution trace). Keep it on **Simple** for the narration below; there is one scripted "flip to Technical" beat in §2.
- Every headline number carries its **rationale** — either a one-line inference beside it or an **ⓘ info tooltip** (hover or keyboard-focus). Numbers are never shown bare.

---

## 0 · Launch

```bash
make demo            # → http://localhost:8080  (streamlit, binds $PORT)
# or: make docker-build && make docker-run
```

First load fits the scoring models on the synthetic cohort once (cached for the session) — a few seconds.
Run `make prefit` beforehand for instant startup (the Docker image does this at build time).

---

## 1 · Home — pick a business

- **Expected:** CreditPulse title, one-line value statement, a radio list of six named archetypes + "🎲 Random MSME".
  Selecting one shows its card (sector · Udyam category · declared turnover + a one-line blurb).
- **Controls:** a **Staged reveal** toggle (on = animated pipeline; off = Instant mode straight to the Health Card)
  and the **▶ Run Assessment** button.
- **Do:** leave *Staged reveal* ON, pick **Sunrise Textiles** (the clean approve), click **Run Assessment**.

## 2 · Pipeline — the 9-stage reveal (the centrepiece)

The page shows the **9-stage list** (Waiting → Running → Completed chips) and a **progress bar**. In *Technical* view a
dark **execution console** also accumulates the log lines live; in *Simple* view the console is hidden and the stage rail
widens. Below, the **current stage's detail** animates.

**The key change — the stages no longer vanish.** As each stage completes it drops a **persistent, expandable notebook-style
cell** into the page: the stage title + a one-line **plain-language headline**, and inside it the **findings** (tone-coded
callouts — good / caution / risk, *not* console lines) plus that stage's **plot/visual**. When the run finishes the live
animation area clears and **all 9 cells remain** (stage 9 open, the rest collapsed) — a Jupyter-notebook-style record a bank
officer can scroll and re-open, in human language. Expected content per stage:

| # | Stage | What appears on screen |
|---|---|---|
| 1 | **Scenario Lock-in** | Entity KPIs: sector, Udyam category, vintage, employees, declared turnover. Console: `Loading entity: …` |
| 2 | **Data Ingestion — Breadth Reveal** | A grid of **25 source tiles**; the ones carrying a live signal light green with a record count, the rest greyed "not on file". Console lists each source ✓/—. This is the deliberate "footprint breadth" moment. |
| 3 | **Data Integration** | KPIs: raw records reconciled, sources merged, **identity integrity** (GSTIN↔PAN↔Udyam↔MCA). |
| 4 | **Feature Engineering** | Five per-pillar feature counters + a composites counter; total engineered-signal count. |
| 5 | **Cross-Source Synthesis** | The differentiator: the **Turnover-Authenticity** flagship card first (its 0-100 score + manipulation-resistance note), then the 12 other composites, each naming its constituent sources. |
| 6 | **Peer Segmentation** | A Plotly scatter of the cohort coloured by peer tier, with **this MSME highlighted (navy star)**; a "Peer group: …" badge. Labelled *descriptive only — not the decision*. |
| 7 | **Scoring** | Five dimension bars + composite score + grade/band + model PD/risk KPIs. |
| 8 | **Explainability** | Top **strengths (green)** and **risks (red)** in plain language. In *Technical* view the cell also shows a **SHAP** waterfall for the GBM PD path; in *Simple* view that is replaced by a one-line "independent cross-check agrees" note. |
| 9 | **Financial Health Card** | A hero score banner + the **plain-language verdict** as the stage headline + a link to the full card. Progress bar reads *Assessment complete ✓*. |

- **Controls:** **⏩ Instant (skip)** jumps to the completed state; **↻ Replay** re-runs the animation. Either way the **full 9-cell record** is what remains — nothing meaningful disappears when the animation ends.
- **The live toggle beat (do this here):** with the 9 cells on screen in Simple view, open the **Explainability** cell — it reads in plain terms. Now **flip the top-right toggle to Technical**: the same cell grows its SHAP waterfall and the execution console appears. Say it out loud — *"the officer sees this in plain English; and for your risk team, every model internal is one switch away — same run, nothing recomputed."* Flip back to Simple to continue.
- **UX gate:** the observer should be able to narrate the story back — *"it pulled 25 sources, fused them, scored, explained — and I can re-open any step and read what it found in plain language."*

## 3 · Financial Health Card

- **Expected:** hero (score/grade/peer group), a colour-coded **recommendation banner** (Approve / Approve-with-conditions
  / Decline + indicative limit), then — directly under the banner — the **plain-language verdict**: 2–3 declarative
  sentences stating the call, the dominant driver, and (for the inflated case) the turnover-authenticity divergence note.
  **Read the verdict out loud** — it is the single most persuasive artifact and no longer has to be spoken for the app.
  Below: the **radar** of five dimensions, per-dimension scores (engineering names appear only in Technical view), the
  **Turnover-Authenticity** KPI, estimated default risk, 300-900 analogue, data confidence, and the strengths/risks. Each
  headline KPI has an **ⓘ tooltip** explaining the term in plain language.
- A **"Synthetic ground truth"** expander reveals the hidden true labels so judges can confirm the model caught what it should.

## 4 · Explainability & Architecture

- **Explainability:** reason codes (deterministic path), dimension bars, the SHAP waterfall, and all 13 composite
  rationales ("what a fraudster would need to compromise simultaneously").
- **Architecture:** the pipeline diagram, the 25-source catalog grouped by domain, the model stack, module boundaries,
  and the honest synthetic-data / deployment notes.

---

## The three-run demo arc (recommended narration)

1. **Sunrise Textiles** — clean approve. Score high, grade ~1, fast-track. The Health Card verdict opens *"Approve: …"* and
   names the strongest driver. *"A viable exporter onboarded on evidence."* Run this one **Staged** so the audience sees the
   9-cell notebook record build and remain.
2. **Anand Kirana Store** — thin-file micro trader. Cautious *review* with a **Medium/Low confidence** flag rather than
   an auto-reject; the verdict says so in one line, and the ingestion cell shows the thin footprint. *"We don't punish a thin
   file — we hedge it."*
3. **Precision Auto Components** — the money shot. Estimated **default risk looks benign**, but the **Turnover-Authenticity**
   composite drops to ~50, and the Health Card verdict's third sentence spells it out for you: *"…the caution comes from the
   turnover-authenticity check, which found declared sales unsupported by independent evidence. A conventional scorecard would
   likely have approved this application."* Open the ground-truth expander: true honesty = **inflated**. *"A single-document
   model waves this through; fusing independently-governed sources catches it — harder to fake than any one input."* This is
   also the natural spot for the **Simple → Technical** flip if you skipped it in §2.

Finish on the **Architecture** page (switch to **Technical** view for the full model stack) for the judges' technical-soundness confidence.
