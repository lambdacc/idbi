# CreditPulse — Manual Demo Script (Platform, 5 minutes)

**Purpose:** a single cohesive five-minute walkthrough of the CreditPulse **platform** — one codebase serving
three IDBI Innovate 2026 problem statements: **PS3 Financial Health**, **PS4 Early Warning**, **PS5 Fraud
Intelligence**. Best run by a second person unfamiliar with the internals — the "does a credit officer get it in
30 seconds?" test. Pairs with the automated smoke tests under `app/tests/`.

**All data is synthetic.** State this out loud once at the start.

**Two things to point at up front (the UI-humanization pass):**
- Every page has a **View: Simple · Technical** toggle at the top right. It **defaults to Simple** — plain
  language, no model names — which is what a credit officer sees. Flip it to *Technical* to expose model internals
  (SHAP, execution trace, model stack). Keep it on **Simple** for the narration below; there is one scripted
  "flip to Technical" beat in the Track 03 segment.
- Every headline number carries its **rationale** — either a one-line inference beside it or an **ⓘ info tooltip**
  (hover or keyboard-focus). Numbers are never shown bare.

**Timing spine (5:00):** Overview 0:20 · Track 03 2:00 · Track 04 1:15 · Track 05 1:15 · Close 0:10.

---

## 0 · Launch

```bash
make demo            # → http://localhost:8080  (streamlit, binds $PORT)
# or: make docker-build && make docker-run
```

First load fits the scoring models on the synthetic cohort once (cached for the session) — a few seconds.
Run `make prefit` beforehand for instant startup (the Docker image does this at build time). The app opens on the
**Overview** landing page; the three tracks are grouped in the sidebar. Deep links: `/` Overview, `/track03`,
`/track04` (+`/watchlist`), `/track05` (+`/case_investigation`), `/architecture`.

---

## 1 · Overview — one codebase, three problem statements (0:20)

- **Expected:** the Overview landing page with three **track cards** — Financial Health (PS3), Early Warning (PS4),
  Fraud Intelligence (PS5).
- **Say:** *"This is one deployment, one codebase, answering three of the Innovate 2026 problem statements. Same
  25-source data foundation, same explainability spine — three lenses on the same MSME. Everything you'll see is
  synthetic data."*
- **Do:** point at the three cards, then click into **Financial Health**.

## 2 · Track 03 · Financial Health — the 9-stage assessment (2:00)

**Pick a business.** The page offers named archetypes + "🎲 Random MSME". Leave *Staged reveal* **ON** and pick
**Precision Auto Components** — the money shot — then click **▶ Run Assessment**.

**The 9-stage reveal (the centrepiece).** The stages don't vanish: as each completes it drops a **persistent,
expandable notebook-style cell** — the stage title, a one-line plain-language headline, and inside it the findings
(tone-coded good / caution / risk callouts) plus that stage's visual. When the run finishes, **all 9 cells remain**
(stage 9 open, the rest collapsed) — a record a bank officer can scroll and re-open in human language. Narrate the
arc fast:

| # | Stage | What appears on screen |
|---|---|---|
| 1 | **Scenario Lock-in** | Entity KPIs: sector, Udyam category, vintage, employees, declared turnover. |
| 2 | **Data Ingestion — Breadth Reveal** | A grid of **25 source tiles**; live-signal ones light green with a record count, the rest greyed "not on file". The deliberate "footprint breadth" moment. |
| 3 | **Data Integration** | Raw records reconciled, sources merged, **identity integrity** (GSTIN↔PAN↔Udyam↔MCA). |
| 4 | **Feature Engineering** | Five per-pillar feature counters + composites; total engineered-signal count. |
| 5 | **Cross-Source Synthesis** | The differentiator: the **Turnover-Authenticity** flagship card (0-100 + manipulation-resistance note), then the 12 other composites, each naming its constituent sources. |
| 6 | **Peer Segmentation** | A scatter of the cohort coloured by peer tier, **this MSME highlighted**. Labelled *descriptive only — not the decision*. |
| 7 | **Scoring** | Five dimension bars + composite score + grade/band + risk KPIs. |
| 8 | **Explainability** | Top **strengths (green)** and **risks (red)** in plain language. |
| 9 | **Financial Health Card** | Hero score banner + plain-language **verdict** + link to the full card. |

- **The live toggle beat (do this here):** open the **Explainability** cell — it reads in plain terms. Now **flip
  the top-right toggle to Technical**: the same cell grows its SHAP waterfall and the execution console appears.
  Say it: *"the officer sees this in plain English; for your risk team, every model internal is one switch away —
  same run, nothing recomputed."* Flip back to Simple.
- **The Health Card + cross-check (the payoff).** Scroll to the **Financial Health Card**: hero (score/grade/peer
  group), a colour-coded **recommendation banner**, and directly under it the **plain-language verdict** — *read it
  out loud*. Here estimated **default risk looks benign**, but the **Turnover-Authenticity** composite drops to ~50,
  and the verdict spells it out: *"…the caution comes from the turnover-authenticity check, which found declared
  sales unsupported by independent evidence. A conventional scorecard would likely have approved this."* Open the
  **"Synthetic ground truth"** expander: true honesty = **inflated**. *"A single-document model waves this through;
  fusing independently-governed sources catches it — harder to fake than any one input."* The **reason codes** below
  give the deterministic, auditable path.

## 3 · Track 04 · Early Warning — the deterioration radar (1:15)

- **Do:** back to the sidebar, open **Early Warning** (`/track04`).
- **Expected:** a portfolio-deterioration **radar** — the whole book scored for stress, worst-first, not one
  application at a time.
- **Say:** *"PS3 decides who to onboard. PS4 watches the book you already have — it's a deterioration radar across
  the live portfolio, ranked by who's sliding toward trouble."*
- **Do:** open the **watchlist** (`/watchlist`) and click into the flagship borrower — the one whose repayments are
  still on time but who is **rolling over**: refinancing, stretching payables, alt-data (utilities, GST filing
  cadence, footfall) all bending the wrong way while the EMI clock still looks clean.
- **Land the lead-time line:** *"A repayment-only view — the kind most early-warning systems still run — only sees
  this once the borrower actually misses. On our synthetic panel, fusing the alt-data signals flags stress a
  **median 8 months earlier** than that repayment-only baseline, and it concentrates the true stress cases far more
  tightly at the top of the list."* (Verified on the synthetic cohort: median lead-time 11.5 vs 2.0 months;
  capture in the top decile 0.926 vs 0.519. All synthetic.)

## 4 · Track 05 · Fraud Intelligence — the citation-gated case file (1:15)

- **Do:** sidebar → **Fraud Intelligence** (`/track05`).
- **Expected:** a **fraud desk** that scores accounts for fraud-ring involvement, worst-first.
- **Say:** *"Third lens: not credit risk, but coordinated fraud. The desk scores every account and surfaces the
  suspicious ones."*
- **Do:** expand a high-scoring suspicious account into its **ring** — the desk pivots from one account to the
  cluster it's wired into (mules, a recruiter, a cash-out node), showing the shared-infrastructure links.
- **Do:** open the **case file** (`/case_investigation`). The point: it's **citation-gated** — every claim on the
  page carries the **transaction IDs** that back it. *"Nothing here is an unsupported assertion; each line cites the
  transactions it's built on, so an investigator can act on it — and, if it went to a tribunal, defend it."*
- **The counter-example (do this):** point out the **"explainably cleared"** gig worker — an account that *looks*
  structurally like a mule (many small inflows, rapid outflows) but is exonerated, with the reasons cited.
- **Land it:** *"On the synthetic eval, **6 of 6 fraud rings recovered** — each with at least 60% of its members
  flagged — and **zero false positives on the hard-negative gig workers**. We catch the rings without burning the
  honest hustler. Again, synthetic data throughout."*

## 5 · Close (0:10)

*"One codebase, one deploy — onboarding, monitoring, and fraud on the same 25-source foundation, explainable
end-to-end: plain language for the officer, model internals one switch away for the risk team. Everything you saw
was synthetic."* Optionally finish on the **Architecture** page (flip to **Technical**) for the full model stack and
the honest synthetic-data / deployment notes.

---

## Appendix · Track 03 alternate archetypes (if you have extra time)

The Precision Auto Components run above is the headline. Two other archetypes make good contrast runs:

1. **Sunrise Textiles** — clean approve. Score high, grade ~1, fast-track. Verdict opens *"Approve: …"* and names
   the strongest driver. *"A viable exporter onboarded on evidence."* Good to show the 9-cell notebook build cleanly.
2. **Anand Kirana Store** — thin-file micro trader. Cautious *review* with a **Medium/Low confidence** flag rather
   than an auto-reject; the ingestion cell shows the thin footprint. *"We don't punish a thin file — we hedge it."*
