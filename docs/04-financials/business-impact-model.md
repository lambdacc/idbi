# Business-Impact Model — CreditPulse (PS3)

**Status:** Phase 2 · **Date:** 28 Jun 2026 · **Use:** the quantified "business impact" story for the pitch.
**Health warning:** every figure here is an **illustrative planning estimate** built to size the opportunity for judges — **not an audited forecast.** Market figures are cited (see `../00-screening/research-evidence.md`); IDBI-specific numbers are placeholders to replace with bank data if shared.

---

## 1. The macro pain (cited)

- India's MSME credit gap ≈ **₹25-30 lakh crore (~$530B)**; only **~14%** of MSMEs access formal credit.
- The cause PS3 names: thin-file **NTC/NTB** MSMEs lack traditional financials → high rejection of *viable* borrowers, missed lending, weak diversification, slow inclusion.
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

*The point for judges is the shape, not the decimals: a single multidimensional, explainable card converts rejected-but-viable MSMEs into safe approvals while flagging the risky ones — growth and quality at once, exactly PS3's stated outcome.*

## 4. Strategic value to IDBI (beyond the numbers)

- Advances the bank's stated **financial-inclusion + MSME** priority (the "backbone of the economy" framing from the orientation).
- **Deployable** into IDBI's AWS/sandbox stack with an AA/ULI-ready adapter → short path from PoC to pilot.
- Explainable/auditable → **deployable under RBI digital-lending / model-risk expectations**, unlike black-box entries.

## 5. Honest caveats (say these — they build credibility)

- Synthetic data can't prove real predictive accuracy; **real-default backtesting + recalibration is the pilot step.**
- All deltas above are illustrative; the model should be re-run on IDBI's actual segment volumes, approval rates, ticket sizes, and loss rates (request at sandbox stage).
- EPFO signal is included by design but isn't yet on AA rails (mock/alt now, AA-ready later).
