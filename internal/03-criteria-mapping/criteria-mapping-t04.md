# Criteria Mapping & Demo Script — CreditPulse Problem Statement 4 (Default Prediction Model) · pitched as Early Warning

**Status:** Multi-track WP-V · **Date:** 6 Jul 2026 · **Reads with:** [`criteria-mapping.md`](criteria-mapping.md) (Problem Statement 3 model) and [`../../docs/solution-design.md`](../../docs/solution-design.md)
Purpose: make every Problem Statement 4 judging lever *visibly* hit, using the shared CreditPulse platform. One codebase, one deploy; this track is reached at `/track04`.

> All metrics below are measured on the **synthetic** holdout by `app/tracks/t04_early_warning/ml/ews_metrics.py`. Real-default backtesting is the productionization step, stated honestly.

---

## 1. Map to IDBI's five judging criteria

| Criterion | How Problem Statement 4 scores | What the judge sees |
|---|---|---|
| **Innovation** | An **alt-data early-warning** signal that flags deterioration a **median 8 months** before a repayment-only baseline (11.5 vs 2.0 months), with **explained drivers** per borrower — not a lagging days-past-due tripwire | Portfolio radar + a watchlist row with its reasons; the lead-time gap on screen |
| **Feasibility** | Runs on data the bank already has on a booked borrower (repayment history + the same GST/UPI/EPFO/e-way alt-data footprint as Problem Statement 3); monitors the **existing book**, no new consent surface | Watchlist over live synthetic borrowers; one Streamlit deploy |
| **Scalability** | Batch portfolio scoring on a monthly panel; the engine is a pickled model loaded once (prefit baked into the image); stateless scoring | Portfolio Overview scoring the whole book; sub-second reruns |
| **Business impact** | **NPA lead-time**: acting a median 8 months earlier opens the restructure/cure window before an account slips to NPA — quantified (illustratively) in the impact model | Impact stub in [`../../docs/business-impact-model.md`](../../docs/business-impact-model.md) |
| **Technical implementation** | **Anti-leakage by construction** (entity-level split, future-window features raise, labels attached in a separate step), monotonic LightGBM + isotonic calibration, lead-time as the headline metric not accuracy, capture@decile **0.926 vs 0.519** | The lead-time scorecard + the isolation/leakage tests going green |

## 2. Avoid the bank's stated "common mistakes"

| Stated mistake | Our guard |
|---|---|
| Overly theoretical / non-implementable | A *working* deployed track at `/track04`, in the same repo as Problem Statement 3 / Problem Statement 5 |
| The **Problem Statement 4 accuracy trap** (imbalanced defaults, chasing raw accuracy) | We **headline lead-time**, not accuracy; AUC is reported but not the pitch. This is the exact trap the Problem Statement 3 doc worried about — here we answer it head-on with a time-to-signal framing |
| Silent data leakage (a classic early-warning failure) | Entity-level split + future-window features that **raise** if referenced + labels read only in a separate attach step — enforced in tests |
| Weak use of data/AI | Alt-data panel + monotonic calibrated model + a lead-time-vs-baseline evaluation |
| Ignoring scalability & compliance | Same deployable stack + explainable per-borrower drivers (defensible to an officer) |

## 3. Differentiation vs the field

Most Problem Statement 4 entries will re-skin a days-past-due bucket or ship an unvalidated black-box "risk score" that leaks the future into training. Problem Statement 4's edge: a **lead-time story measured against an explicit repayment-only baseline** (not a self-graded number), **explained drivers** per borrower so a relationship manager can act, and **leakage guards that are tested**, not asserted. It plugs into the same platform as the underwriting and fraud tracks — one book, one lens across the credit lifecycle.

## 4. The 75-second demo (slots into the platform script)

1. **(0-15s) The pain:** "The book looks fine on repayments — until suddenly it doesn't. By the time DPD moves, the cure window is gone."
2. **(15-40s) The radar + watchlist:** open **Problem Statement 4 → Portfolio Overview**, then the **Watchlist**; the flagship textile borrower is rolling over — footprint softening (GST, e-way, payroll) while repayments are still current.
3. **(40-65s) The lead-time payoff:** land the line — "the alt-data signal flags this a **median 8 months** before a repayment-only view would (11.5 vs 2.0 months); capture@decile 0.926 vs 0.519." Show the explained drivers behind the alert.
4. **(65-75s) Honesty + handoff:** "Synthetic now; real-default recalibration at pilot. Same codebase, same deploy as Tracks 03 and 05." Close.

## 5. Anticipated judge questions (prep)

- *"How do you know it's not leaking the label?"* → entity-level split; any future-window feature **raises**; labels attached in a separate step; it's tested. Show the test.
- *"Why lead-time instead of AUC?"* → for an early-warning system the value is *time to act*, not a ranking statistic; we report AUC but pitch the 8-month gap against a concrete baseline.
- *"Is the alt-data actually available on a booked borrower?"* → yes — it's the same GST/UPI/EPFO/e-way footprint Problem Statement 3 already uses, now tracked over time; AA-ready.
- *"What's the baseline you beat?"* → a repayment-only (SAJAG-style) view — deliberately the incumbent's own lens, so the gap is apples-to-apples.

## 6. Deferred to founder
- The Problem Statement 3 criteria doc's "we chose Problem Statement 3 over Problem Statement 4" line is now stale (multi-track). Left as-is; flag for a pass.
- Deploy is a single Cloud Run container (see runbook), whereas the Problem Statement 3 pitch says "AWS-native" for the stage-2 ACC sandbox. Keep the pitch's AWS framing or align to Cloud Run — founder call.
