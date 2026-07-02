# Submission Deliverables Checklist — CreditPulse (PS3)

**Status:** Phase 2 · **Date:** 28 Jun 2026 · **Reads with:** [`../02-solution-design/agentic-execution-plan.md`](../02-solution-design/agentic-execution-plan.md)

---

## 1. Stage-1 submission (due 9 Jul 2026) — what the platform requires

- [ ] **Registration** complete; team created (1-4; solo allowed)
- [ ] **Problem statement selected = PS3 (Financial Health Score)** — one only
- [ ] **PPT** using IDBI's **mandatory fixed template** (exact slide count, no edits — see §3)
- [ ] **Deployment link** (publicly reachable working prototype)
- [ ] **Public GitHub repo** (clean README, reproducible `make demo`, no secrets)
- [ ] (Optional but recommended) **demo recording** of the 90-second flow
- [ ] Submitted via the Hack2skill submission tab before the deadline

> Reconcile at the 30 Jun session: bank says idea/approach weighted most at stage-1, but the platform mechanically needs the deploy + GitHub links. **Plan: ship the working prototype regardless.**

## 2. Stage-2 (if shortlisted 21 Jul) — refined prototype (22-31 Jul)

- [ ] Refit on **IDBI mock data** in the **ACC/AWS sandbox**
- [ ] Replace mock adapter with **real sandbox APIs**
- [ ] Hardened deploy, deeper eval, polished Card + demo
- [ ] Prep finale assets (13 Aug finalists → 21 Aug demo day + live Q&A)

## 3. PPT outline (fit to IDBI's fixed template — adapt to their exact slide count)

1. **Title** — CreditPulse · PS3 Financial Health Score · team
2. **Problem** — NTC/NTB MSMEs rejected despite viability (PS3's words) + the credit gap
3. **Solution** — the MSME Financial Health Card (one annotated screenshot)
4. **How it works** — 5 pillars + alt-data (GST/UPI/AA/EPFO) → multidimensional score
5. **Differentiator** — explainable reason codes + GST-vs-bank consistency
6. **Architecture** — AWS-native, AA/ULI/OCEN adapter, sub-minute API (C4 diagram)
7. **Evaluation** — AUC/Gini/KS, calibration, PSI + synthetic-data honesty + recalibration plan
8. **Business impact** — onboarding uplift + portfolio quality (from `../04-financials/`)
9. **Compliance & trust** — explainability, human-in-loop, residency, RBI alignment
10. **Roadmap to pilot** — stage-2 sandbox → production (real AA/bureau, backtesting)
11. **Team & why us** — Lambdac's GST/eval/AWS track record (ReconWise)

## 4. Quality gates before submit (from the execution plan)

- [ ] Deploy link live & stable · [ ] repo public & reproducible · [ ] eval scorecard green (with caveat)
- [ ] Card renders score + pillars + reasons + recommendation · [ ] `/score` API works
- [ ] AA/ULI mock adapter demonstrated · [ ] security review passed · [ ] PPT template-compliant
- [ ] 90-sec demo rehearsed

## 5. Open items to confirm (30 Jun / portal)
- Exact PPT template + slide count; whether a demo video is required or optional.
- Stage-1 evaluation weighting (idea vs working demo).
- Any PS3 sample data at stage-1.
