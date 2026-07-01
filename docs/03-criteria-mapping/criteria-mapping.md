# Criteria Mapping & Demo Script — CreditPulse (PS3)

**Status:** Phase 2 · **Date:** 28 Jun 2026 · **Reads with:** [`../02-solution-design/solution-design.md`](../02-solution-design/solution-design.md)
Purpose: make sure every judging lever is *visibly* hit, and the demo lands.

---

## 1. Map to IDBI's five judging criteria

| Criterion | How CreditPulse scores | What the judge sees |
|---|---|---|
| **Innovation** | Multidimensional alt-data Health Card with the **GST-vs-bank consistency** signal + explainable reason codes — beyond a single black-box score | The Card: pillars + reasons, not just a number |
| **Feasibility** | Built on the bank's **named data** (GST/UPI/AA/EPFO) and a proven stack; consent-first AA posture; honest synthetic→real path | Working deploy link + GitHub, not slides |
| **Scalability** | **AWS-native**, API-first, stateless scoring, sub-minute; per-tenant isolation | Architecture slide + live API call |
| **Business impact** | **Onboard credit-invisible NTC/NTB MSMEs + improve portfolio quality** (PS3's own words), quantified | Impact model (`../04-financials/`) |
| **Technical implementation** | Deterministic-first features, interpretable model, **eval harness** (AUC/Gini/KS, calibration, PSI), explainability, audit trail | Eval scorecard + repo + reason codes |

## 2. Avoid the bank's stated "common mistakes"

| Stated mistake | Our guard |
|---|---|
| Overly theoretical / non-implementable | A *working* deployed prototype + repo by 9 Jul |
| Weak banking-domain understanding | GST/AA/ULI/OCEN fluency, DSCR/FOIR, CMR-style output, EPFO-on-AA nuance |
| Weak use of data/AI | Multidimensional features + interpretable model + eval rigor |
| Ignoring scalability & compliance | AWS-native + explainability/residency/human-in-loop posture |
| Incomplete technical architecture | Full C4-style architecture + IaC + eval harness |

## 3. Differentiation vs the field (and incumbents)

Most entries will ship a black-box score or a slide deck. CreditPulse's edge is the trio judges of a *bank* reward: **explainable & auditable** (deployable under RBI norms), **deployable** (AWS-native, API-first, real architecture), and **domain-deep** (GST-vs-bank consistency, alt-data breadth). Against incumbents (Perfios/CRIF/FinBox) we don't out-scale them — we match the credibility bar on a focused PS3 use case and win on transparency + a clean demo.

## 4. The 90-second demo (the whole pitch)

1. **(0-15s) The pain, in their words:** "A viable MSME with no traditional financials gets rejected. IDBI loses a good borrower; the MSME stays credit-invisible."
2. **(15-45s) The Card, live:** pull one synthetic MSME → in seconds, the Financial Health Card renders: **grade 2/10**, pillar strengths/risks, top reasons ("GST filing 11/12 on-time +", "inflows 38% below GST turnover –"), **recommended product + indicative limit**, onboarding = fast-track.
3. **(45-65s) The differentiator:** flip to a borderline case → show the **GST-vs-bank consistency flag** catch an inflated-turnover MSME the traditional process would miss → officer override + audit trail.
4. **(65-80s) Deployable:** one architecture slide — AWS-native, AA/ULI adapter, sub-minute API; call the live `/score` endpoint.
5. **(80-90s) Impact + honesty:** "Onboards X% more viable NTC/NTB MSMEs while protecting portfolio quality; real-default recalibration is the pilot step." Close.

## 5. Full demo / pitch outline (for finale, if shortlisted)

Problem & PS3 alignment → data & consent model → the five pillars → live Card walkthrough (healthy / borderline / decline) → explainability & audit → architecture & integration (AA/ULI/OCEN, AWS) → eval results + synthetic-data honesty + recalibration plan → business impact → roadmap to pilot → Q&A (anticipate: imbalance/accuracy, consent/DPDP, EPFO-on-AA, how it beats their internal model).

## 6. Anticipated judge questions (prep)

- *"Accuracy on imbalanced defaults?"* → we report Gini/KS/calibration not raw accuracy; synthetic now, real-default recalibration at pilot. (We know this trap — it's why we chose PS3 over PS4.)
- *"EPFO data — how?"* → strong signal; not yet on AA rails (NPS is), so mock/alt now, AA-ready adapter.
- *"How is this different from Perfios/CRIF?"* → explainable, focused on NTC/NTB onboarding, AA/ULI-native, deployable in your stack.
- *"Consent?"* → GST/public signals for identification; AA enrichment on consent; DPDP-aware.
