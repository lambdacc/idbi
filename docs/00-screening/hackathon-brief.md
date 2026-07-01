# IDBI Innovate 2026 — Extracted Brief (facts only)

**Purpose:** Single source of truth for the hackathon facts used in screening. **Updated 28 Jun 2026 from the IDBI first orientation session (primary source)** — this supersedes the earlier secondary-source reconstruction. Primary-source items are marked **[orientation]**.

**Organizer:** IDBI Bank (national, India) · **Platform:** Hack2skill · **Theme:** *Build. Integrate. Transform.*
**Listing:** https://hack2skill.com/event/idbinnovate · **Partners [orientation]:** AWS (cloud + knowledge partner), Hack2skill (platform), Applied Cloud Computing/ACC (sandbox, stage 2).

---

## Problem statements (5) — corrected to the orientation [orientation]

The bank's own framing differs from earlier secondary sources. **The "financial health scorecard" wording belongs to PS4 (default prediction), not a standalone score track.**

| PS | Official title / framing | Notes |
|---|---|---|
| **PS1** | **Digital Wealth Management** — avatar-based app giving liability customers a 360° view of savings/investments/spend + AI advisory at bank scale. | Consumer wealth. |
| **PS2** | **Identify Prospective Customers (lead-gen)** — from the bank's **existing liability** customers, detect needs (home/auto/consumer-durable loans) and pitch matched products. Later extendable to non-customers. | Retail cross-sell. |
| **PS3** | **Financial Health Score** — AI/ML **MSME Financial Health Card** (official text below). | **Best fit for Lambdac ⭐.** Onboarding credit-invisible MSMEs. |
| **PS4** | **Default Prediction** — early-warning on **existing** MSME loans; predict default **12 months ahead** (current internal model only ~3 months, low accuracy); structured + unstructured data. *(Prashant verbally also called this a "financial health scorecard" — don't confuse with PS3.)* | Accuracy contest vs. their incumbent model on mock data. **Avoid.** |
| **PS5** | **Novel / Open track** — any banking idea **unrelated to PS1–4**; reviewed by IDBI senior management. | Wildcard. |

**PS3 — official problem-statement text (verbatim):**
> *"Bank's MSME credit evaluation relies on traditional financial documents, which many New-to-Credit (NTC) and New-to-Bank (NTB) enterprises lack or maintain inadequately. Despite availability of rich alternate data (GST, UPI, AA, EPFO, etc.), absence of a unified assessment framework leads to high rejection rates, missed viable borrowers, limited portfolio diversification, and slower financial inclusion progress.*
> *Expected outcome: design an AI/ML-driven MSME Financial Health Card that aggregates alternate data (GST, UPI, AA, EPFO, etc.), computes a multidimensional financial health score, visualizes strengths and risks, integrates with ULI/OCEN/AA ecosystems, enables near real-time credit assessment, and expands onboarding of credit-invisible MSMEs while improving portfolio quality."*

Bank's stated goal: **scalable, production-ready** prototypes deployable at bank scale, via co-creation, aiming at a **long-term association**. AI/ML adoption in IDBI lending is currently limited and being scaled up.

**Rule [orientation]: one team → one problem statement only.** Multi-track entry is not allowed.

## Evaluation criteria (as published)

Solutions are assessed on: **Innovation · Feasibility · Scalability · Business impact · Technical implementation.**
"Common mistakes to avoid" explicitly name: overly theoretical / non-implementable ideas, weak banking-domain understanding, weak use of data/AI, ignoring scalability & compliance, and incomplete technical architecture.

## Timeline [orientation]

| Milestone | Date |
|---|---|
| Problem-statement deep-dive / AMA session | **30 Jun 2026** |
| Registration + **working prototype** (deployment link + GitHub repo + fixed PPT) due | **9 Jul 2026** |
| Shortlisting | **21 Jul 2026** |
| Refined-prototype submission window (sandbox/mock data + AWS + ACC unlocked) | **22–31 Jul 2026** |
| Finalist announcement | **13 Aug 2026** |
| Demo day + winner announcement; pilot-deployment exploration | **21 Aug 2026** |

**Stage-1 (≤9 Jul) is built on the team's OWN synthetic data** — IDBI mock data and the ACC/AWS sandbox come only **after** shortlisting.

## Prizes

- **Total pool ₹15,00,000.** Problem-statement tracks (01–04): one winner + one runner-up each. Novel track (05): standalone top prize (reported ~₹1 lakh).
- Beyond cash: **PoC pathway inside IDBI Bank's sandbox** for high-performing teams, plus visibility and collaboration with the bank.

## Eligibility

Open to startups, FinTech companies, technology professionals, developers/data scientists, innovation teams, and individuals (solo allowed; teams **1–4**). The bank leans toward deployable solutions and long-term partners over students. **A *working prototype* (deployment link + public GitHub + fixed PPT) IS required at the 9 Jul submission [orientation]** — note this contradicts earlier "no MVP at registration" secondary sources; the bank says idea/approach is weighted most at stage 1, but the platform mechanically requires the prototype links, so plan to ship one on our own synthetic data.

## What shortlisted teams receive [orientation]

- **Sandbox environment via ACC (Applied Cloud Computing)** + **AWS** cloud — unlocked **only at stage 2 (post-21 Jul shortlist).**
- **Mock/synthetic data only — there is no real data at any stage.** The mock datasets are generated *after* shortlisting, scoped to whatever the chosen solution needs ("once solutions are shortlisted... we'll see what data sets are required and generate the synthetic data"). So stage-1 prototypes run on the **team's own synthetic data.**
- **Reference architecture / API docs** and **mentorship** (incl. AWS as knowledge partner).
- **Submission mechanics:** mandatory **fixed PPT template** (exact slide count, no edits) + **deployment link** + **public GitHub repo**.

## Process (staged pipeline) [orientation]

Register → **9 Jul working-prototype submission (own synthetic data)** → **21 Jul shortlisting** (ACC/AWS sandbox + mock data unlock) → **22–31 Jul refined-prototype** in sandbox → **13 Aug finalists** → **21 Aug demo day + winners** → **pilot-deployment exploration** at the bank.

---

## GST data availability (important for the Track 03 angle)

- **A bank does not natively hold a customer's GST returns.** Since **Nov 2022, RBI made GSTN a Financial Information Provider (FIP)** under the **Account Aggregator** framework, so banks/lenders can pull GST data **consent-based** via AA: completed returns for the **last ~18 months** — **GSTR-1 (Table 4, outward supplies)** and **GSTR-3B (summary)**, plus filing history and basic profile. Also reachable via **ULI** (Unified Lending Interface) and **OCEN**.
- **Implication for the hackathon:** all data is mock; the realistic build is to design a **GSTN-via-AA / ULI adapter** and demo on our own synthetic GST returns — exactly the ecosystem PS3 names.
- **EPFO nuance:** PS3 explicitly lists **EPFO** as an alt-data source. Useful signal (workforce size / PF-contribution stability = MSME-health proxy), but **EPF/PPF are not yet live on the AA rails** (NPS is). Include an EPFO signal via mock/alternate ingestion now, AA-ready later — and surface the nuance as domain credibility.

## Resolved by the orientation
- **Shortlist date = 21 Jul 2026.** Multi-track entry = **not allowed** (one PS per team). Team size **1–4**. Working prototype **required** at 9 Jul. Data is **mock-only**, generated post-shortlist. Partners = AWS / Hack2skill / ACC.

## Still open (resolve at 30 Jun session / on portal)
- **Stage-1 evaluation weighting** — idea/approach vs working demo (mixed signals; bank says approach-first, platform requires prototype).
- **Criteria weights** for Innovation/Feasibility/Scalability/Business-impact/Technical-implementation.
- **IP / ownership terms** for a fintech-company entrant; pilot-deployment pathway specifics; whether ₹15L is cash vs PoC value.
- **Mock-dataset contents** for PS3 (GST/AA/UPI/EPFO/bureau?) and whether any sample is available at stage 1.
- Expected **score output convention** and any required explainability/auditability standard.
