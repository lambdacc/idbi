---
name: data-source-evaluation
description: >-
  Evaluate and prioritize electronic data sources for business/MSME profiling,
  credit-risk scoring, and fraud/authenticity detection. Use this skill whenever
  the task involves discovering, assessing, cataloging, or ranking alternative
  data sources (utilities, telecom, FASTag, e-way bills, MCA, DGFT/customs,
  property tax, licensing, POS/QR, insurance, court/insolvency, procurement,
  geospatial, and the like) — even when the user only names the obvious ones
  (GST, UPI, AA, EPFO) or asks generally to "widen the data", "find more signals",
  "justify our sources", or "build a data-source catalog". Trigger it before
  writing any synthetic-data schema or scoring design so every source is judged
  against one rubric instead of ad hoc. Also use it to decide which composite
  cross-source indicators are worth building.
---

# Data Source Evaluation

A rubric-driven procedure for turning a loose list of candidate data sources into
a **prioritized catalog** with consistent per-source records, plus a
**composite-indicator catalog** describing which sources to fuse and why.

Its whole reason to exist: without a fixed rubric, source evaluation drifts —
some sources get five attributes, some get one, "practicality" is asserted rather
than argued, and the obvious four (GST/UPI/AA/EPFO) crowd out everything else.
This skill forces the same ten-plus questions on every source and makes the
"reject" decisions visible.

## When to reach for it

- Building or expanding a data-source catalog for business/MSME profiling.
- Deciding whether a candidate source (e.g. FASTag, ESIC, property tax) earns a
  place in a production or demo pipeline.
- Designing a synthetic-data schema and needing to know which sources to model.
- Choosing which cross-source composite signals to engineer.
- Defending source choices to a reviewer/evaluator ("why these, why not those").

## Core stance

1. **The obvious four are the floor, not the answer.** Start every discovery from
   first principles: *what other systems must this business touch to operate?*
   Utilities, premises, logistics, licensing, statutory filings, commerce,
   legal/risk. Enumerate broadly, then cut with the rubric.
2. **Reject on the record.** An impractical source is fine to drop — but write the
   reason. Silent omission looks like an oversight; a recorded rejection looks
   like judgment.
3. **Manipulation resistance is a first-class axis.** For credit and fraud use,
   how hard a signal is to fake matters as much as how predictive it is. A
   self-reported number is weaker than a metered utility reading or a statutory
   filing.
4. **Value lives in combination.** Single sources are inputs; composite indicators
   are the product. Always finish with the synthesis pass.

---

## Procedure

### Step 1 — Enumerate candidates broadly

Sweep these areas at minimum; don't stop at the ones already named:

- **Core financial / statutory:** GST, UPI, Account Aggregator, non-UPI bank
  transactions, EPFO, ESIC, MCA (directors, beneficial ownership), income-tax footprint
- **Trade & logistics:** e-way bills, FASTag, commercial-vehicle / fleet data,
  DGFT, customs, import/export
- **Utilities & premises:** electricity, water, gas, commercial LPG, property tax,
  municipal records, lease registrations, telecom (mobile/broadband/fiber)
- **Licensing & compliance:** FSSAI, factory licence, Pollution Control Board,
  Shops & Establishment, sectoral licences
- **Commerce & payments:** POS, QR acceptance, marketplace/e-commerce presence
- **Risk & legal:** insurance, court records, insolvency (IBC), government
  procurement / tenders
- **Geospatial:** satellite / geospatial — flag as candidate only if genuinely practical

List every candidate before evaluating any. Breadth first, judgment second.

### Step 2 — Score each source against the rubric

Produce one record per candidate with **every** field below. If a field is
unknown, say "unknown" and drop confidence — do not leave it blank.

| Field | What to capture |
|---|---|
| **Source** | Name |
| **Description** | What the data is, in one line |
| **Owner / generator** | Who holds or produces it |
| **Electronic availability** | Is a machine-readable form real *today*? (yes / partial / no) |
| **Access model** | public · consent-based (AA) · regulated API · licensed · scraped · unavailable |
| **Update frequency** | real-time · daily · monthly · quarterly · annual · irregular |
| **Practical availability** | Realistically obtainable in production? (high / medium / low) with a one-line why |
| **Cost / integration complexity** | low / medium / high |
| **Fraud / authenticity indicators** | What it reveals about whether the business is real/operating as claimed |
| **Credit / risk indicators** | What it reveals about capacity, activity, stability |
| **Manipulation resistance** | How hard to fake (high / medium / low) |
| **Limitations** | Coverage gaps, lag, bias, legal constraints |
| **Confidence** | Your confidence in this assessment (high / medium / low) |

### Step 3 — Prioritize

Rank retained sources against this filter. A source scores well when it is:

- Electronically available today
- Realistically obtainable
- Frequently updated
- Difficult to manipulate
- A strong predictor of business activity
- Useful across multiple industries

Output three tiers — **Retain (core)**, **Retain (enrichment)**, **Reject** — and
for every Reject, one line on why. Do not optimize for source *count*; a small set
of complementary, hard-to-fake, obtainable sources beats a long disconnected list.

### Step 4 — Synthesis pass (composite indicators)

Now fuse. For each proposed composite indicator, record: the indicator, its
constituent sources, the signal it produces, and why the fusion is stronger or
harder to manipulate than any single input. Starter patterns (extend, don't
copy verbatim):

- Electricity + GST → energy intensity
- Electricity + EPFO + factory licence → estimated production capacity
- FASTag + fuel + fleet → logistics activity
- Property tax + utilities + GST address → premises verification / authenticity
- Telecom + banking + UPI → business continuity
- Utility payments + payroll → operational stability
- Import data + GST + logistics → supply-chain consistency

Prefer composites that (a) cross-check a self-reported figure against an
independent metered/statutory one, or (b) triangulate the same fact from
sources a fraudster would have to compromise simultaneously.

---

## Output format

Deliver two artifacts:

1. **Prioritized data-source catalog** — the Step 2 records, grouped by the Step 3
   tiers, with rejected sources and reasons.
2. **Composite-indicator catalog** — the Step 4 table.

Keep both as markdown tables so they can drop straight into a research summary or
design doc. Tag any figure or claim later reused for synthetic-data distributions
as either *(sourced: <citation>)* or *(assumed)*.

## Anti-patterns to avoid

- Stopping at GST/UPI/AA/EPFO because they're documented.
- Asserting "practical" or "hard to fake" without a reason.
- Blank rubric fields (use "unknown" + lower confidence instead).
- A catalog of single sources with no synthesis pass.
- Dropping a source silently instead of recording the rejection.