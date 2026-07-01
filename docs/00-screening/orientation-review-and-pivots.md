# Orientation Review & Recommended Adjustments — IDBI Innovate 2026

**Prepared for:** Lambdac Computing — founders · **Date:** 28 Jun 2026
**Sources:** IDBI first orientation session (verbatim transcript, `hackathon-resources/idbi-first-orientation-mmeting-transcript.txt`) **+ the official PS3 problem-statement text** (provided by founder). Both are primary; they supersede our earlier secondary-source reconstruction.
**Question answered:** Is our approach / track / solution still ideal, or are pivots needed?

---

## 0. Verdict (BLUF)

**Track and solution: confirmed correct — no pivot.** The official PS3 is titled **"Financial Health Score,"** and its text describes an **AI/ML MSME Financial Health Card aggregating GST/UPI/AA/EPFO, computing a multidimensional health score, visualizing strengths/risks, integrating with ULI/OCEN/AA, for near-real-time assessment to onboard credit-invisible MSMEs** — i.e., our exact concept, almost verbatim. Our screening pick and deep-dive were right.

> **Self-correction note:** an interim read of the *transcript alone* tempted a re-label, because Prashant verbally called PS3 "MSME business loan identification" and used the words "financial health scorecard" while describing **PS4** (default prediction). The **official PS3 text resolves it**: PS3 *is* "Financial Health Score" and is our target. PS4 (default prediction) remains the one to avoid. I've corrected the brief accordingly.

**So the real adjustments are operational and framing — not a change of track or solution:**

1. **Timeline is tighter than we assumed** — a *working* prototype (deployment link + public GitHub + fixed PPT) is due **9 Jul**, on our **own synthetic data**. Sandbox/mock data + AWS + ACC come only after shortlisting (21 Jul). Start the agentic build now.
2. **Commit to ONE problem statement (PS3)** — multi-track entry is disallowed; retire the FHS/Default/Novel hedge.
3. **Align our language to PS3's stated outcome** — onboard NTC/NTB credit-invisible MSMEs, cut high rejection rates, improve portfolio quality/diversification, advance financial inclusion. (All already in our concept.)
4. **Keep EPFO in the data-source set** (the bank explicitly lists GST/UPI/AA/EPFO) — while noting the integration reality that EPFO isn't yet live on AA rails.
5. **Lean AWS-native; sell production-readiness + a long-term partnership** — exactly what the bank said it wants.
6. **Operational must-dos:** mandatory PPT template, deploy link + GitHub, and **attend the 30 Jun PS deep-dive**.

Net: our thesis holds and is reinforced; what changes is urgency, focus, and framing.

---

## 1. What the orientation confirms (our analysis holds — and strengthens)

- **PS3 = "Financial Health Score" is officially our concept.** Official expected outcome: *"an AI/ML-driven MSME Financial Health Card that aggregates alternate data (GST, UPI, AA, EPFO, etc.), computes a multidimensional financial health score, visualizes strengths and risks, integrates with ULI/OCEN/AA ecosystems, enables near real-time credit assessment, and expands onboarding of credit-invisible MSMEs while improving portfolio quality."* This is the CreditPulse concept verbatim — our deep-dive was built around exactly this.
- **The pain is the bank's stated pain.** Official PS3 names it: MSME credit evaluation relies on traditional documents that **NTC/NTB** firms lack; despite rich alternate data, the **absence of a unified assessment framework → high rejection rates, missed viable borrowers, limited diversification, slow inclusion.** That is precisely the gap our explainable alt-data engine fills.
- **Our GST/AA moat is their data thesis.** Prashant named GST + AA as the inputs; the official text lists GST/UPI/AA/EPFO. Our wedge is endorsed by the brief.
- **Compete on approach/explainability/deployability, not raw accuracy** — confirmed: **all data is mock/synthetic, even in the sandbox.** Vindicates our synthetic-data-ceiling finding.
- **AWS is cloud + knowledge partner** — our AWS/Bedrock ap-south-1 stack is on-target.
- **Serious, professional-friendly field** — solo professionals and startups eligible; bank leans toward deployable solutions and long-term partners over students. Favourable for Lambdac.

## 2. Corrected problem-statement map (official + orientation)

| PS | Official / orientation framing | Fit |
|---|---|---|
| PS1 | **Digital Wealth Management** — avatar-based 360° advisory for liability customers | Low |
| PS2 | **Identify Prospective Customers** — retail cross-sell (home/auto/consumer loans) to existing customers | Low–Med |
| **PS3** | **Financial Health Score** — MSME Financial Health Card on GST/UPI/AA/EPFO; multidimensional score; visualize; integrate ULI/OCEN/AA; near-real-time; **onboard credit-invisible NTC/NTB MSMEs + improve portfolio quality** | **High ⭐ (our target)** |
| PS4 | **Default Prediction / "financial health scorecard"** — early-warning on existing loans, predict default **12 months ahead**, beat low-accuracy internal model | **Avoid** |
| PS5 | **Novel / Open** — unrelated to PS1–4 | Wildcard |

**Why still avoid PS4:** it is an accuracy-improvement contest against the bank's own incumbent model, on mock data, on an imbalanced portfolio (a participant flagged that "raw accuracy can be misleading"; the bank's metric guidance was vague). PS3 rewards exactly our strengths — alt-data breadth, explainability, integration, deployability, onboarding/inclusion impact.

## 3. The adjustments, in detail

**A. Operational/timeline — build now.** Working prototype (deploy link + GitHub + PPT) due **9 Jul** on our **own synthetic data**; stage 2 (post-21 Jul shortlist) refines on IDBI mock data in the ACC/AWS sandbox. ~11 days to a live prototype → the agent-led, human-gated build (per `feasibility-deep-dive.md` §7) should start the day PS3 is confirmed (≤30 Jun).

**B. Commit to PS3 only.** One team → one PS. Drop hedging across tracks.

**C. Reframe to PS3's stated outcome.** Make the demo narrative speak the bank's words: a **Financial Health Card** that turns credit-invisible NTC/NTB MSMEs into assessable, onboardable borrowers; quantify **reduced rejection of viable borrowers** and **improved portfolio quality**, not just a score. Keep our differentiators — explainable reason codes, GST-vs-bank consistency, AA/ULI integration adapter, AWS-native deployment.

**D. Handle EPFO deliberately.** The bank lists EPFO as an alt-data source, so include an **EPFO signal** (workforce size/PF-contribution stability is a strong MSME-health proxy). But note in the architecture that **EPF/PPF aren't live on AA yet** (NPS is) — so model it via mock/alternate ingestion now, AA-ready later. Surfacing this nuance is a credibility signal, not a gotcha.

**E. AWS-native + partnership posture.** Pitch deployable-at-bank-scale AWS architecture and Lambdac's company credibility / appetite for a long-term association — the bank explicitly values this over a one-off clever demo.

**F. Operational must-dos.** Use the **mandatory PPT template exactly**; submit deploy link + public GitHub + PPT; team 1–4; **attend 30 Jun** and confirm PS3 scope + ask §5 questions.

## 4. Refined solution concept for PS3 (one paragraph)

A **MSME Financial Health Card**: ingest GST returns + AA-shaped bank/UPI cash-flow + bureau-style + EPFO signals → engineer alt-data health features (turnover trend & filing discipline, GST-vs-bank consistency, cash-flow stability, vintage, leverage, workforce stability, growth) → compute a **transparent multidimensional health score** with **plain-language strengths/risks and reason codes**, an indicative eligibility/limit, and the matched loan product → **visualize the card** for an RM and expose a **near-real-time scoring API with an AA/ULI/OCEN integration adapter**, on an **AWS-native, audit-ready** deployment. Headline outcome: **onboard more credit-invisible NTC/NTB MSMEs while protecting portfolio quality.** Demonstrated on our synthetic data at stage 1; refined on IDBI mock data in the sandbox at stage 2.

## 5. Open questions for the 30 Jun session

- PS3 scope precision: is the deliverable the **Health Card + score + onboarding decision**, or also downstream origination workflow? How is PS3 bounded vs PS2?
- Stage-1 evaluation weighting: idea/approach vs a working demo? (Bank said approach-first; Hack2skill said working prototype required — reconcile.)
- Which alt-data points will the **mock dataset** include (GST, AA bank, UPI, EPFO, bureau)? Any sample at stage 1, or strictly stage 2?
- Expected **score output convention** (e.g., a 1–10 / 300–900 analogue) and any required **explainability/auditability** standard.
- IP/ownership terms for a fintech-company entrant and the pilot-deployment pathway.

## 6. What I updated in the kit
- `hackathon-brief.md` — corrected to primary source: real PS1–5 map (**PS3 = Financial Health Score**, official outcome text included; PS4 = Default Prediction), 9 Jul **working-prototype** requirement, 30 Jun session, 21 Jul shortlist, 22–31 Jul refined window, 13 Aug finalists, AWS/ACC partners, one-track rule, mock-data-only, PPT template, EPFO-on-AA nuance.
- `screening-assessment.md`, `feasibility-deep-dive.md` — added confirmation notes (**PS3 = Financial Health Score officially validated**; new operational facts) — verdicts unchanged.
- `README.md` index — updated decision line.
