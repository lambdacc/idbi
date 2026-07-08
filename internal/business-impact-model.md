# Business-Impact Model — CreditPulse (Problem Statement 3)

**Status:** Phase 2 · **Date:** 28 Jun 2026 · **Use:** the quantified "business impact" story for the pitch.
**Health warning:** every figure here is an **illustrative planning estimate** built to size the opportunity for judges — **not an audited forecast.** Market figures come from public sources (RBI U.K. Sinha Committee 2019; SIDBI-CRISIL 2025; Sahamati AA impact reports); IDBI-specific numbers are placeholders to replace with bank data if shared.

---

## 1. The macro pain (cited)

- India's MSME credit gap ≈ **₹25-30 lakh crore (~$530B)**; only **~14%** of MSMEs access formal credit.
- The cause Problem Statement 3 names: thin-file **NTC/NTB** MSMEs lack traditional financials → high rejection of *viable* borrowers, missed lending, weak diversification, slow inclusion.
- Account-Aggregator penetration in **MSME** lending is still low (~1% range vs ~10%+ for personal loans) — genuine white space, not a crowded race.

## 2. Where CreditPulse creates value (the levers)

1. **Onboard viable credit-invisible MSMEs** the traditional process rejects (top-line growth + inclusion).
2. **Protect portfolio quality** — catch inflated-turnover / stressed cases via GST-vs-bank consistency and cash-flow flags (lower NPA leakage).
3. **Faster turnaround (TAT)** — near-real-time score vs manual document collection/underwriting.
4. **Lower cost-to-serve** — alt-data automation vs manual underwriting (cited industry costs: ~$70-200 doc collection, ~$350+ manual underwriting per case).

## 3. Illustrative impact model (replace placeholders with IDBI data)

**Assumptions (illustrative):** IDBI screens **10,000** MSME loan applications/year in the target segment; traditional process approves **~35%**; of the **65% rejected**, a meaningful share are *viable but thin-file*. Avg ticket **₹10 lakh**; net interest margin **~3.5%**; incremental credit cost on the new cohort held **≤2%** via better selection.

| Lever | Traditional | With CreditPulse | Illustrative delta |
|---|---|---|---|
| Approval rate (segment) | 35% | 42% (recover viable thin-file) | **+700 loans/yr** |
| Incremental disbursement | — | 700 × ₹10L | **₹70 cr/yr** |
| Incremental net margin | — | 3.5% of ₹70 cr | **~₹2.45 cr/yr** |
| Bad-loan leakage avoided | baseline | consistency/cash-flow flags catch inflated cases | **risk-cost reduction** (size with bank data) |
| TAT | days (manual) | **<1 min** score → faster decisions | throughput + experience |
| Cost-to-serve | manual underwriting | automated first-pass | **per-case cost ↓** |

*The point for judges is the shape, not the decimals: a single multidimensional, explainable card converts rejected-but-viable MSMEs into safe approvals while flagging the risky ones — growth and quality at once, exactly Problem Statement 3's stated outcome.*

## 4. Strategic value to IDBI (beyond the numbers)

- Advances the bank's stated **financial-inclusion + MSME** priority (the "backbone of the economy" framing from the orientation).
- **Deployable** into IDBI's AWS/sandbox stack with an AA/ULI-ready adapter → short path from PoC to pilot.
- Explainable/auditable → **deployable under RBI digital-lending / model-risk expectations**, unlike black-box entries.

## 5. Honest caveats (say these — they build credibility)

- Synthetic data can't prove real predictive accuracy; **real-default backtesting + recalibration is the pilot step.**
- All deltas above are illustrative; the model should be re-run on IDBI's actual segment volumes, approval rates, ticket sizes, and loss rates (request at sandbox stage).
- EPFO signal is included by design but isn't yet on AA rails (mock/alt now, AA-ready later).

---

## Problem Statement 4 (Default Prediction Model) — pitched as Early Warning: impact

**Health warning (same as above):** the rupee/percentage figures in this section are an **illustrative planning estimate** to size the opportunity — **not an audited forecast or a measured outcome.** The only *measured* numbers here are the model-eval metrics explicitly flagged "(verified)"; everything financial is an assumption to re-run on IDBI data.

### The value lever: NPA lead-time

The mechanism is time, not a new score. An Early Warning signal that flags a deteriorating account **earlier** hands the relationship/collections team a longer runway to act — restructure, top-up, tighten limits, or cure — *before* the account crosses into NPA. Later detection means the only remaining tool is provisioning and recovery; earlier detection keeps cure on the table.

- **Verified (model eval, synthetic panel):** EWS flags stress a **median 8.0 months earlier** than a repayment-only baseline (median lead-time **11.5 vs 2.0 months**), and concentrates true stress far better — **capture@top-decile 0.926 vs 0.519**. These are eval-harness measurements, *not* a claim about IDBI's live book.
- The business question the lead-time answers: *does the extra runway convert accounts that would have gone NPA into cured/restructured ones?* That conversion rate is the value, and it is a **planning assumption** until backtested.

### Illustrative planning calculation (replace placeholders with IDBI data)

**Assumptions (illustrative):** a target MSME sub-portfolio of **10,000** live accounts; an annualised **slippage rate to NPA of ~4%** → **~400 accounts/yr** at risk; avg outstanding exposure **₹10 lakh** → **~₹40 cr/yr** of exposure entering stress. Suppose the 8-month earlier warning lets the bank **cure an incremental 15%** of otherwise-slipping accounts (a **planning assumption**, not a result), and that curing avoids a loss-given-default of **~40%** of exposure on those accounts.

| Lever | Basis (illustrative) | Illustrative delta |
|---|---|---|
| Accounts slipping to NPA (baseline) | 4% of 10,000 | ~400/yr |
| Exposure entering stress | 400 × ₹10L | **~₹40 cr/yr** |
| Incremental cure from earlier action | 15% cure uplift (assumption) × 400 | **~60 accounts/yr cured** |
| Loss averted on cured accounts | 60 × ₹10L × 40% LGD (assumption) | **~₹2.4 cr/yr** (illustrative) |
| Provisioning relief / recovery cost saved | earlier action vs recovery | **size with bank data** |

*The shape, not the decimals: the verified result is **8 months of extra runway**; the rupee figure above is a caveated illustration of what that runway is worth **if** it converts stress to cure at the assumed rate. Re-run on IDBI's real slippage rate, exposures, cure rates, and LGD at the sandbox stage.*

---

## Problem Statement 5 (Open Innovation) — pitched as Fraud Intelligence: impact

**Health warning (same as above):** every rupee/hour figure here is an **illustrative planning estimate** — **not an audited forecast or a measured outcome.** Only the model-eval metrics flagged "(verified)" are measured; all financial numbers are assumptions to replace with IDBI data.

### Lever 1 — fraud-loss averted (catch mule rings before cash-out)

The value is timing again: flagging a **mule ring while funds are still in-network** — before the cash-out leg — is the difference between blocking a transfer and chasing an unrecoverable loss. Recovery after cash-out is near-zero, so averted loss ≈ exposure held in the ring at flag time.

- **Verified (model eval, synthetic):** **6/6 rings recovered** (each with ≥60% of members flagged) with **0 of 10 hard-negative false positives** (the "explainably cleared" gig-worker stayed clear). Alert-level **recall 1.0, precision 0.744** — and the precision "misses" are themselves ring-associated infrastructure (mule/recruiter/cash-out), so **ring-level precision is 1.0**. Eval-harness numbers on synthetic data, *not* a claim about IDBI traffic.

### Lever 2 — investigator ops-hours saved (citation-gated case file)

Because the case file is **citation-gated** — every claim assembles its own supporting evidence automatically — the investigator opens a pre-built, sourced dossier instead of hand-collecting statements, links, and transaction trails. The saving is analyst time per case, multiplied across the alert queue.

### Illustrative planning calculation (replace placeholders with IDBI data)

**Assumptions (illustrative):** the system surfaces **~50 confirmed ring cases/yr** in the target segment; avg exposure held in-ring at flag time **₹8 lakh**; earlier-than-cash-out interception averts a **planning-assumption 50%** of that exposure. Separately, assume manual evidence assembly takes **~6 hours/case** and the citation-gated file removes **~70%** of it (**assumptions**), at a loaded analyst cost of **₹800/hr**.

| Lever | Basis (illustrative) | Illustrative delta |
|---|---|---|
| Fraud exposure intercepted in-network | 50 rings × ₹8L | **~₹4 cr/yr** flagged pre-cash-out |
| Loss averted | 50% interception (assumption) of ₹4 cr | **~₹2 cr/yr** (illustrative) |
| Investigator hours saved | 50 cases × 6 hr × 70% (assumptions) | **~210 hrs/yr** |
| Ops cost saved | 210 hr × ₹800/hr (assumption) | **~₹1.7 lakh/yr** (illustrative) |

*The shape, not the decimals: the verified results are **6/6 rings caught with zero hard-negative false positives** and an **auto-assembled, sourced case file**; the rupee/hour figures are caveated illustrations of what catching-before-cash-out and analyst-time-saved are worth **if** the assumed interception and time-saving rates hold. Re-run on IDBI's real alert volumes, exposures, recovery rates, and analyst costs at the sandbox stage.*
