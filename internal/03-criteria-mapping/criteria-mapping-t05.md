# Criteria Mapping & Demo Script — CreditPulse Track 05 (PS5 · Fraud / Mule Detection)

**Status:** Multi-track WP-V · **Date:** 6 Jul 2026 · **Reads with:** [`criteria-mapping.md`](criteria-mapping.md) (PS3 model) and [`../../docs/solution-design.md`](../../docs/solution-design.md)
Purpose: make every PS5 judging lever *visibly* hit, using the shared CreditPulse platform. One codebase, one deploy; this track is reached at `/track05`.

> All metrics below are measured on the **synthetic** holdout by `app/tracks/t05_fraud_intelligence/ml/eval/fraud_metrics.py`. The labels file (`fraud_ground_truth.csv`) is **eval-only** — never read at score time.

---

## 1. Map to IDBI's five judging criteria

| Criterion | How Track 05 scores | What the judge sees |
|---|---|---|
| **Innovation** | An **agentic, citation-gated case file**: a suspicious account is expanded into its ring across the transaction graph, and every claim in the case is constructed **only if it carries the transaction IDs behind it** — an uncited claim *raises* rather than renders | The 5-stage case investigation; each finding shows its evidence transactions |
| **Feasibility** | Runs on **transaction data the bank already holds** (accounts + transfers); no new data source, no external graph database | Fraud Desk scoring live synthetic accounts; one Streamlit deploy |
| **Scalability** | Typology + anomaly scoring is per-account; ring expansion is a **bounded pure-Python BFS** over the transfer graph (no heavyweight graph engine, no new dependency) | Ring diagram assembling on demand; sub-second |
| **Business impact** | **Fraud loss averted** by catching mule rings before cash-out **plus investigator ops-hours saved** because the case file auto-assembles the evidence — quantified (illustratively) in the impact model | Impact stub in [`../../docs/business-impact-model.md`](../../docs/business-impact-model.md) |
| **Technical implementation** | Typology detectors + Isolation-Forest anomaly blend; **6/6 rings recovered** (ring_recall 1.0), recall@alert **1.0**; and the differentiator — **0/10 false positives** on hard-negative legitimate gig workers (precision@alert 0.744, but precision_ring@alert **1.0**: the non-mule alerts are all ring-associated infrastructure) | The fraud scorecard + the case's citation gate |

## 2. Avoid the bank's stated "common mistakes"

| Stated mistake | Our guard |
|---|---|
| Overly theoretical / non-implementable | A *working* deployed track at `/track05`, in the same repo as PS3/PS4 |
| The **PS5 false-positive trap** (freezing a legitimate customer's account) | The **hard-negative gig workers**: high-velocity but honest accounts that a naive model flags — Track 05 gets **0/10** wrong, and shows *why* each was cleared |
| Black-box fraud score no one can act on or defend | The **citation gate** — no finding is shown without the transactions that justify it; the case file is an audit trail, not a verdict |
| Label leakage inflating results | `fraud_ground_truth.csv` is **eval-only**, never read by the engine or the pages at score time — enforced structurally |
| Ignoring scalability & compliance | Pure-Python bounded ring expansion (no new dependency); human-in-the-loop case review |

## 3. Differentiation vs the field

Most PS5 entries will ship an anomaly score and a threshold — which either misses coordinated rings (each account looks individually fine) or freezes honest high-velocity customers. Track 05's edge: **ring-level recovery** (it catches the *structure*, 6/6), a **citation-gated case file** an investigator can defend line-by-line, and a **measured false-positive discipline** on the exact population that gets wrongly frozen in production (0/10 hard negatives). It shares the platform with the underwriting and early-warning tracks — the same bank, protected across the lifecycle.

## 4. The 75-second demo (slots into the platform script)

1. **(0-15s) The pain:** "A mule ring drains an account in minutes. Freeze too slow and the money's gone; freeze too eagerly and you lock out an honest customer."
2. **(15-40s) The desk → the ring:** open **Track 05 → Fraud Desk**, pick a flagged account, **expand it into its ring** across the transaction graph — accounts that each look fine alone, coordinated together.
3. **(40-60s) The citation-gated case:** open **Case Investigation** — the 5-stage case file, every claim carrying its **transaction IDs**; "the case cannot even be constructed without its evidence — an uncited claim raises."
4. **(60-75s) The clear + honesty:** show a **hard-negative gig worker** the system *cleared*, explained — "0 of 10 wrongly frozen; 6 of 6 rings caught. Synthetic now, recalibrated at pilot. Same codebase as Tracks 03 and 04." Close.

## 5. Anticipated judge questions (prep)

- *"How do you avoid freezing legitimate customers?"* → the hard-negative set: honest high-velocity accounts; 0/10 false positives, each cleared with a reason. That discipline is the headline, not raw recall.
- *"Aren't your results leaking the labels?"* → `fraud_ground_truth.csv` is eval-only; the engine and pages never read it at score time. Show where the boundary is enforced.
- *"Why not a graph database / GNN?"* → bounded BFS over the transfer graph recovers 6/6 rings with **no new dependency** and stays explainable; a GNN would trade away the auditability a bank needs.
- *"What does 'ring recovered' mean exactly?"* → a ring counts as caught if **≥60% of its members** are flagged; on the holdout all six clear that bar (ring_recall 1.0). We state the threshold, not a vague "100%".
- *"Precision is 0.744 — false alarms?"* → the non-mule alerts are **ring-associated infrastructure** (recruiters/cash-outs), so precision_ring@alert is 1.0; every alert is genuinely part of fraud activity.

## 6. Deferred to founder
- Deploy is a single Cloud Run container; PS3 pitch says "AWS-native" for the stage-2 ACC sandbox — align or keep, founder call (same note as T04).
