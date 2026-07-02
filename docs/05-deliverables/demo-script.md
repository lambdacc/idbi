# CreditPulse — Manual Demo Script (Sprint-3 acceptance G4)

**Purpose:** the documented walkthrough of the full 9-stage staged-reveal flow (implementation-plan.md §6.2),
with the expected on-screen content at each stage. Run by a second person unfamiliar with the internals — the
"does a credit officer get it in 30 seconds?" UX gate. Pairs with the automated smoke test
`app/tests/test_pipeline_orchestrator.py` (acceptance b).

**All data is synthetic.** State this out loud once at the start.

---

## 0 · Launch

```bash
make demo            # → http://localhost:8080  (streamlit, binds $PORT)
# or: make docker-build && make docker-run
```

First load fits the scoring models on the synthetic cohort once (cached for the session) — a few seconds.

---

## 1 · Home — pick a business

- **Expected:** CreditPulse title, one-line value statement, a radio list of six named archetypes + "🎲 Random MSME".
  Selecting one shows its card (sector · Udyam category · declared turnover + a one-line blurb).
- **Controls:** a **Staged reveal** toggle (on = animated pipeline; off = Instant mode straight to the Health Card)
  and the **▶ Run Assessment** button.
- **Do:** leave *Staged reveal* ON, pick **Sunrise Textiles** (the clean approve), click **Run Assessment**.

## 2 · Pipeline — the 9-stage reveal (the centrepiece)

The page shows, left-to-right: the **9-stage list** (Waiting → Running → Completed chips), a **progress bar**, and a
dark **execution console** that accumulates log lines live. Below, the **current stage's detail** renders. Expected
content per stage:

| # | Stage | What appears on screen |
|---|---|---|
| 1 | **Scenario Lock-in** | Entity KPIs: sector, Udyam category, vintage, employees, declared turnover. Console: `Loading entity: …` |
| 2 | **Data Ingestion — Breadth Reveal** | A grid of **25 source tiles**; the ones carrying a live signal light green with a record count, the rest greyed "not on file". Console lists each source ✓/—. This is the deliberate "footprint breadth" moment. |
| 3 | **Data Integration** | KPIs: raw records reconciled, sources merged, **identity integrity** (GSTIN↔PAN↔Udyam↔MCA). |
| 4 | **Feature Engineering** | Five per-pillar feature counters + a composites counter; total engineered-signal count. |
| 5 | **Cross-Source Synthesis** | The differentiator: the **Turnover-Authenticity** flagship card first (its 0-100 score + manipulation-resistance note), then the 11 other composites, each naming its constituent sources. |
| 6 | **Peer Segmentation** | A Plotly scatter of the cohort coloured by peer tier, with **this MSME highlighted (navy star)**; a "Peer group: …" badge. Labelled *descriptive only — not the decision*. |
| 7 | **Scoring** | Five dimension bars + composite score + grade/band + model PD/risk KPIs. |
| 8 | **Explainability** | Top **strengths (green)** and **risks (red)** in plain language + a **SHAP** waterfall for the GBM PD path. |
| 9 | **Financial Health Card** | A hero score banner + a link to the full card. Progress bar reads *Assessment complete ✓*. |

- **Controls:** **⏩ Instant (skip)** jumps to the completed state; **↻ Replay** re-runs the animation.
- **UX gate:** the observer should be able to narrate the story back — *"it pulled 25 sources, fused them, scored, explained."*

## 3 · Financial Health Card

- **Expected:** hero (score/grade/peer group), a colour-coded **recommendation banner** (Approve / Approve-with-conditions
  / Decline + indicative limit), the **radar** of five dimensions, per-dimension scores, the **Turnover-Authenticity**
  KPI, PD, 300-900 analogue, data confidence, and the strengths/risks.
- A **"Synthetic ground truth"** expander reveals the hidden latent labels so judges can confirm the model caught what it should.

## 4 · Explainability & Architecture

- **Explainability:** reason codes (deterministic path), dimension bars, the SHAP waterfall, and all 12 composite
  rationales ("what a fraudster would need to compromise simultaneously").
- **Architecture:** the pipeline diagram, the 25-source catalog grouped by domain, the model stack, module boundaries,
  and the honest synthetic-data / deployment notes.

---

## The three-run demo arc (recommended narration)

1. **Sunrise Textiles** — clean approve. Score high, grade ~1, fast-track. *"A viable exporter onboarded on evidence."*
2. **Anand Kirana Store** — thin-file micro trader. Cautious *review* with a **Medium/Low confidence** flag rather than
   an auto-reject. *"We don't punish a thin file — we hedge it."*
3. **Precision Auto Components** — the money shot. Raw **PD looks benign**, but the **Turnover-Authenticity** composite
   drops to ~50 and the top risk reads *"Declared turnover materially exceeds settled bank inflows and goods-movement
   evidence."* Open the ground-truth expander: latent honesty = **inflated**. *"A single-document model waves this
   through; fusing independently-governed sources catches it — harder to fake than any one input."*

Finish on the **Architecture** page for the judges' technical-soundness confidence.
