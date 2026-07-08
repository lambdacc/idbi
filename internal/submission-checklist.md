# Submission Deliverables Checklist — CreditPulse Platform (Problem Statement 3 · Problem Statement 4 · Problem Statement 5)

**Status:** Multi-track WP-V · **Date:** 6 Jul 2026 · **Reads with:** [`03-criteria-mapping/`](03-criteria-mapping/) (per-track mappings) and [`deployment-runbook.md`](deployment-runbook.md)

> **Portal reality (confirmed by organiser update):** IDBI Innovate 2026 now permits **one team → multiple submissions across different problem statements**. Each submission entry requires a **Challenge/PS selection** and a **PPT** (both mandatory); **Deployment Link** and **GitHub Repository Link** are optional-but-highly-recommended. Nothing requires those two URLs to be unique per entry — so we submit the **same deploy URL and same repo URL three times**, and only the PS selection and the PPT differ.

---

## 1. Stage-1 submission (due 9 Jul 2026) — the 3-track matrix

Three submission entries, one codebase, one deploy. Owner/date to be filled by the founder.

| # | Problem statement | PS selected | PPT (mandatory, official template) | Deploy link (shared) | GitHub link (shared) | Deep link a reviewer lands on | Demo video (optional) | Owner / date |
|---|---|---|---|---|---|---|---|---|
| 1 | **Problem Statement 3 · Financial Health Score** | ☐ | ☐ `deck-t03` | ☐ *same URL* | ☐ *same URL* | `…/track03` | ☐ | |
| 2 | **Problem Statement 4 · Default Prediction Model** | ☐ | ☐ `deck-t04` | ☐ *same URL* | ☐ *same URL* | `…/track04` | ☐ | |
| 3 | **Problem Statement 5 · Open Innovation** | ☐ | ☐ `deck-t05` | ☐ *same URL* | ☐ *same URL* | `…/track05` | ☐ | |

Shared assets (produce once, reuse across all three entries):

- [ ] **Public GitHub repo** — clean README with the **PS-map table at the top** (done: which codebase serves which PS + the deep link), reproducible `make demo`, no secrets.
- [ ] **Deployment link** — single Cloud Run container serving Overview + all three tracks; smoke `/`, `/track03`, `/track04`, `/track05` on the public URL.
- [ ] Submitted via the Hack2skill submission tab (×3 entries) before the deadline.

> **Founder decision — `internal/` visibility:** the public repo carries `internal/` (decision logs, criteria mappings, this checklist). Options: (a) keep it — shows rigor; (b) move planning docs to a private branch/repo before making public; (c) prune sensitive files only. Re-raised from `01-decision/DECISION-pending.md`; **not actioned unilaterally.**

## 2. Stage-2 (if shortlisted) — refined prototype

- [ ] Refit on **IDBI mock data** in the sandbox (per shortlisted PS)
- [ ] Replace synthetic generators with real sandbox APIs where available
- [ ] Hardened deploy, deeper eval, polished surfaces + demo per track
- [ ] Prep finale assets (live Q&A)

## 3. PPT outlines — three decks (fit to IDBI's fixed template + exact slide count)

Each deck follows the same spine, swapping in that track's proof. Draw content from the per-track criteria mappings and the demo script.

**Deck-T03 (Problem Statement 3 · Financial Health)** — the existing Problem Statement 3 outline (see `03-criteria-mapping/criteria-mapping.md` §3): Health Card, 5 pillars, GST-vs-bank consistency, eval (AUC/Gini/KS + honesty), impact, roadmap.

**Deck-T04 (Problem Statement 4, Default Prediction Model · pitched as Early Warning)** — from `criteria-mapping-t04.md`:
1. Title · Problem Statement 4 — Default Prediction Model · "Early Warning" · team
2. Problem — the book looks fine on repayments until it doesn't; cure window lost
3. Solution — alt-data early-warning radar + watchlist (annotated screenshot)
4. How it works — 24-month alt-data panel → monotonic calibrated model → per-borrower drivers
5. Differentiator — **median 8-month lead-time** vs a repayment-only baseline (11.5 vs 2.0mo); capture@decile 0.926 vs 0.519
6. Why it's trustworthy — anti-leakage by construction (entity split, future-window raises, tested)
7. Architecture — shared platform, one deploy; `/track04`
8. Impact — NPA lead-time value (illustrative) + synthetic-data honesty + recalibration plan
9. Roadmap to pilot

**Deck-T05 (Problem Statement 5, Open Innovation · pitched as Fraud / Mule Detection)** — from `criteria-mapping-t05.md`:
1. Title · Problem Statement 5 — Open Innovation · "Fraud / Mule Detection" · team
2. Problem — mule rings drain in minutes; freeze too slow loses money, too eager freezes honest customers
3. Solution — fraud desk → ring expansion → citation-gated case file (annotated screenshot)
4. How it works — typology + anomaly blend → bounded-BFS ring recovery → 5-stage agentic case
5. Differentiator — **6/6 rings recovered** + **0/10 hard-negative false positives** (explainably cleared gig workers)
6. Why it's trustworthy — citation gate (uncited claim raises); ground-truth is eval-only
7. Architecture — shared platform, one deploy, no new dependency; `/track05`
8. Impact — fraud-loss averted + investigator ops-hours (illustrative) + synthetic-data honesty
9. Roadmap to pilot

## 4. Quality gates before submit

- [ ] Deploy link live & stable · [ ] repo public & reproducible (`make demo`) · [ ] README PS-map at top
- [ ] All three tracks render on the public URL (Overview + `/track03` + `/track04` + `/track05`)
- [ ] Full suite green (**301 passed**) · [ ] eval scorecards green with the synthetic caveat
- [ ] Each track's headline metric reproduces from its eval harness (verified 6 Jul: T04 8-mo gap / 0.926 vs 0.519; T05 6/6 rings / 0-of-10 hard-negative FP)
- [ ] Three PPTs, template-compliant · [ ] security review passed · [ ] 5-minute platform demo rehearsed
- [ ] `internal/` visibility decision made (founder)

## 5. Open items to confirm (portal)
- Exact PPT template + slide count; whether a demo video is required or optional.
- Whether the same deploy/GitHub URL across three entries is accepted as-is (assumed yes per organiser update; confirm on the portal).
- Any per-PS sample data at stage-1.
