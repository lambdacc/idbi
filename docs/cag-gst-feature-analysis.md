# Intel Analysis — CAG GST Audit Reports → CreditPulse Features

**Status:** Phase 2 feature-design input · **Date:** 28 Jun 2026 · **Owner:** Lambdac
**Sources:** CAG Report No. 7 of 2024, Ch. 4 (DORF Phase I) and Report No. 25 of 2025, Ch. 4 (DORF Phase II) — public audit reports, cag.gov.in — plus the V1/V2 risk-indicator tables published alongside them
**Feeds:** [`solution-design.md`](solution-design.md) §4 (feature engineering) and the feature-selection review in [`implementation-plan.md`](implementation-plan.md) §5.

---

## 0. Read this first — how to use this intel (and how not to)

These are **CAG audit reports that audit the GST *Department's* tax administration** — they hunt for revenue leakage and oversight failures. **We are doing the opposite job:** scoring an **MSME borrower's financial health** for IDBI. So this intel is **inspiration, not ground truth** — we mine it for *signals that distinguish a healthy, genuine business from a stressed or misrepresenting one*, and we discard everything that is purely about the tax department's internal process.

Three filters applied throughout:

1. **Re-purpose, don't copy.** A CAG "risk indicator" (e.g., GSTR-1 vs GSTR-3B liability mismatch) is reframed as a **borrower health / turnover-authenticity feature**, not a tax-evasion charge.
2. **Obsolescence lens (critical).** The GST IT system changes fluidly; GSTN has plugged many gaps these reports exploited (2A→2B auto-draft, supplier-filing-linked ITC, sequential filing, e-invoicing, automated scrutiny). Several indicators that were "deviations" in 2018-21 are now **auto-enforced by the portal**, so they no longer separate good from bad borrowers — or they survive only as a weaker behavioural signal. Each indicator below is tagged for this. **The live GST system is likely even more refined than the latest report.**
3. **Whole classes are irrelevant to us** — department-process findings (scrutiny workflow, DGARM follow-up, cancellation delays, manual MIS gaps) are about CAG auditing CBIC, not about borrower health. Noted and set aside.

## 1. What the files are (lineage)

| File | What it is | Period | Framework |
|---|---|---|---|
| `Version 1 risk indicator.xlsx` | Flat list of **18 risk indicators** + matching logic | 2018-21 set | "V1" |
| `Version 2 risk indicator and tables.pdf` | Same family, renumbered **D1–D21** (D15/D18/D19 dropped as immaterial), + the deviation results table (Table 4.3/4.4) | 2018-21 | "V2" (refined) |
| `Report-No.-7,-2024,Ch4.pdf` | **SSCA "DORF Phase I"** — Dept oversight on returns/payments; detailed audit focused on **4 risks** | 2017-18 | earlier |
| `Report-No.-25,-2025,-Ch4.pdf` | **SSCA "DORF Phase II"** — expanded; **18 centralised dimensions + 9 detailed risk parameters**; ₹21,695 cr of confirmed deviations from 2,519 of 8,106 cases | 2018-21 | later |

**Most reusable single nugget:** DORF II added **ratio-based trend parameters** for risk-scoring — these are normalized, behaviour-based, computed from a taxpayer's *own* returns, and therefore **stable against GSTN system changes**. They are the best features here (see §3).

## 2. The obsolescence lens — what GSTN has since automated

| GST change (approx.) | What it auto-enforces now | Indicators it weakens/kills as a "deviation" |
|---|---|---|
| **Rule 36(4)** provisional-ITC cap (20%→10%→5%→0, 2019-21) | ITC restricted toward only what's reflected from suppliers | D1 (2A vs 3B ITC mismatch) |
| **GSTR-2B** auto-drafted (Aug 2020) + **§16(2)(aa)** (Jan 2022) | ITC allowed only if supplier filed & invoice in 2B | D1, D2 (ITC without supplier remitting) — now largely system-blocked |
| **§16(5)** retro window to 30 Nov 2021 for FY17-21 (Finance Act 2024) | legalises late ITC for those years | **D3 (ITC after cut-off) — effectively nullified** for 2018-20 |
| **Sequential filing / Rule 59(6)** (can't file later returns if prior unfiled) | reduces 3B-not-filed-but-1-filed gaps | D20 weakened |
| **E-invoicing** (turnover > ₹5 cr, expanding) | invoice-level truth source; turnover harder to misstate | strengthens turnover-authenticity signals generally |
| **ARSM** + **CBIC→GSTN Back-Office** (2023-24) | automated scrutiny + non-filer MIS | most *department-oversight* findings (not our concern) |

**Implication:** indicators that depended on a *system gap* (auto-reconciliation absent) are fading. Indicators that capture **genuine business behaviour or cross-source consistency** survive — those are what we keep.

## 3. The gold — reusable signal classes (stable, borrower-centric)

These translate cleanly into CreditPulse features and are robust to GST system changes because they're derived from the borrower's own filings/behaviour:

**A. Ratio-based trend features (from DORF II) — highest value, GSTN-stable, no consent needed (GST-only):**
- **ITC availed ÷ tax paid** — abnormally high → thin margins / possible inflated ITC; trend = working-capital signal.
- **IGST ÷ (CGST+SGST)** — inter-state vs intra-state mix → market reach, supply-chain geography, concentration risk.
- **Exempted (or nil-rated) ÷ taxable turnover** — business model & effective-tax profile; sudden shifts = anomaly.
- **Credit notes ÷ tax paid (or ÷ turnover)** — sales returns / cancellations / channel stuffing → revenue-quality signal.
- **Risk-prone HSN/SAC flag** — sector-level risk overlay (some sectors carry higher default/fraud base rates).

**B. Turnover-authenticity / consistency cross-checks (our ReconWise DNA — strong differentiator):**
- **GST turnover vs bank/UPI inflows** (needs AA bank data) — the signature integrity check.
- **GSTR-1 vs GSTR-3B liability** consistency (declared vs paid).
- **GSTR-3B vs e-way-bill** value (movement of goods vs declared supply).
- **GSTR-3B vs TDS/TCS (GSTR-2A Table 9 / GSTR-8)** — third-party-reported receipts vs declared.
- **GSTR-9C unbilled-revenue movement / book-vs-return** reconciliation (larger MSMEs with audits).

**C. Behavioural / discipline features (going-concern & reliability):**
- **Filing regularity & timeliness** (on-time GSTR-3B/GSTR-1 over 12-24 months) — discipline proxy.
- **Late/after-cut-off filing frequency**, **interest-non-payment** behaviour.
- **GSTR-3B filed vs GSTR-1 filed** gap (operating-without-paying pattern) — *weaker now, still a tail signal*.
- **Turnover level, trend & volatility, seasonality** from GSTR-3B months.

**D. Supplier-base reliability (forward-looking, even post-automation):**
- Even though the portal now blocks ITC from non-filing suppliers, an MSME whose **ITC eligibility is repeatedly clipped because its suppliers don't file** has a **fragile supply chain / working-capital drag** — a genuine health signal, not just a tax issue. (Derived from 2B vs purchase behaviour.)

## 4. Full mapping — each CAG dimension → our use

Legend: **Live** = still a useful borrower signal · **Ratio** = obsolete as deviation but the derived ratio/behaviour is useful · **Weak** = mostly auto-enforced now, tail signal only · **Skip** = not relevant to borrower health.

| CAG dim (V1 #/V2 D#) | Original audit intent | CreditPulse reinterpretation | Pillar | Status |
|---|---|---|---|---|
| ITC mismatch 2A vs 3B (1/D1) | ITC over-claim | Supplier-base reliability; working-capital drag | Consistency / Cash-flow | **Weak** |
| ITC without supplier remitting (2/D2) | leakage | Supply-chain fragility | Consistency | **Weak** |
| ITC after cut-off (3/D3) | time-barred ITC | — (legalised by §16(5)) | — | **Skip** |
| Incorrect ISD credit (4/D4) | ISD misuse | Only for multi-GSTIN groups; complexity flag | Stability | **Skip/edge** |
| RCM short-payment (5/D5) | RCM under-pay | Compliance discipline (minor) | Discipline | **Weak** |
| ITC: 9C books vs returns (6/D6), expenses recon (7/D7) | book mismatch | Book-vs-return integrity (audited MSMEs) | Consistency | **Live (>₹5cr)** |
| TRAN-1 transition excess (8/D8) | legacy over-credit | — one-off, 2017 | — | **Skip** |
| Unsettled liability 1/9 vs 3B (9/D9) | declared-not-paid | Liability-payment consistency; stress | Consistency / Obligations | **Live** |
| E-way-bill vs 3B (10/D10) | suppressed sales | Turnover authenticity (goods movement) | Consistency | **Live** |
| Tax paid books vs returns 9R (11/D11) | under-pay | Book-vs-return integrity | Consistency | **Live (>₹5cr)** |
| TDS/TCS vs 3B (12/D12) | under-declared receipts | Third-party-confirmed revenue cross-check | Consistency | **Live** |
| Unbilled-revenue movement 9C (13/D13) | turnover suppression | Revenue-recognition anomaly | Revenue quality | **Live (>₹5cr)** |
| Taxable-turnover mismatch 7G (14/D14) | turnover suppression | Turnover authenticity | Revenue quality | **Live (>₹5cr)** |
| Ineligible composition / threshold cross (15-16/D16) | wrong scheme | **Growth signal**: crossing ₹1-1.5cr = scaling MSME (lead/upsell) | Revenue quality | **Live (re-purposed)** |
| Composition + e-commerce (17/D17) | scheme misuse | Channel mix (sells online) — business-model signal | Revenue quality | **Live (re-purposed)** |
| 3B not filed but 1 filed (18/D20) | business w/o paying | Operating-stress / non-payment pattern | Discipline | **Weak** |
| Short interest (D21) | interest evasion | Payment discipline (minor) | Discipline | **Weak** |
| **Ratio trends** (DORF II) | composite risk score | ITC/tax-paid, IGST/CGST+SGST, exempt/taxable, credit-notes/tax-paid | Revenue quality / Cash-flow | **Live ⭐** |
| **Risk-prone HSN/SAC** (DORF II) | sector risk | Sector-risk overlay feature | Revenue quality | **Live ⭐** |
| Dept oversight: scrutiny, DGARM, cancellation, MIS | admin failures | — auditing CBIC, not borrowers | — | **Skip** |

## 5. Concrete features to ADD to CreditPulse (feature backlog)

Grouped by our five pillars (`solution-design.md` §4); marked **[GST-only]** (computable without consent — fits PS3's low-friction identification) or **[+bank/AA]** / **[+9C]** (needs richer data, stage-2).

**Revenue quality & GST discipline**
- Turnover level, YoY & MoM trend, volatility, seasonality from GSTR-3B `[GST-only]`
- On-time filing rate (GSTR-1 & 3B), late-filing frequency, interest-paid behaviour `[GST-only]`
- **Exempted/nil ÷ taxable turnover** ratio & shift `[GST-only]`
- **Credit-notes ÷ turnover** ratio (returns/cancellations) `[GST-only]`
- **IGST ÷ (CGST+SGST)** mix (geographic reach / concentration) `[GST-only]`
- **Risk-prone HSN/SAC** sector overlay `[GST-only]`
- Composition-threshold-crossing & e-commerce presence = **growth/scaling flags** `[GST-only]`

**Cash-flow health**
- **ITC availed ÷ tax paid** ratio & trend (margin/working-capital proxy) `[GST-only]`
- Cash vs ITC share of tax paid (liquidity proxy) `[GST-only]`
- Avg balance, volatility, low-balance frequency, net-flow trend `[+bank/AA]`

**Consistency & integrity (turnover-authenticity sub-module — the differentiator)**
- **GST turnover vs bank/UPI inflows** gap `[+bank/AA]`
- **GSTR-1 vs GSTR-3B** liability consistency `[GST-only]`
- **GSTR-3B vs e-way-bill** value gap `[GST-only/EWB]`
- **GSTR-3B vs TDS/TCS-reported** receipts `[GST-only]`
- Book-vs-return reconciliation (9C tables) `[+9C, >₹5cr]`

**Obligations & leverage / Stability** (mostly from bank+bureau+EPFO, per solution design) — CAG intel adds: unsettled-liability stress flag, multi-GSTIN complexity flag.

## 6. Proposed "Turnover-Authenticity Score" sub-module (high differentiation)

Bundle the consistency cross-checks (GST↔bank, GSTR-1↔3B, 3B↔e-way-bill, 3B↔TDS/TCS) into a single **authenticity/integrity sub-score** inside the Health Card. This is straight from Lambdac's ReconWise reconciliation DNA, directly answers a bank's #1 fear with thin-file MSMEs ("is the declared turnover real?"), and is something generic entrants won't build. It also gracefully degrades: GST-only checks run pre-consent; bank checks switch on with AA consent.

## 7. What NOT to use (cautions)

- **Don't import obsolete deviations as risk flags.** D3 (legalised), TRAN-1, pure 2A-vs-3B ITC catches are weak/dead post-automation — using them would flag healthy borrowers and signal stale domain knowledge to judges.
- **Don't replicate CAG's enforcement framing.** We assess borrower *health/eligibility*, not tax guilt. A mismatch is a *data/quality/authenticity* signal feeding a score with reasons — never an accusation.
- **Mind the data-quality caveat.** The reports themselves show the GST/EWB systems once carried absurd unvalidated values (₹71 lakh-crore EWB deviations). Treat raw cross-source gaps with **robust outlier handling and tolerance bands** (again, ReconWise practice) — don't let dirty data dominate the score.
- **Period mismatch.** These cover 2018-21; thresholds (₹1cr/₹1.5cr composition, etc.) and rules have moved. Use the *shape* of the signal, not the 2018-21 constants.
- **All of this is feature *inspiration*** — validate predictive value in the eval harness; keep only features that earn their place.

## 8. How this plugs into the build
- Fold the §5 backlog into `solution-design.md` §4 pillars — each feature is implemented as a deterministic, auditable computation and kept only if it earns its place in the eval harness.
- The GST-only features are computable on our **synthetic GST data at stage-1** (no consent), reinforcing PS3's low-friction identification angle.
- The Turnover-Authenticity sub-module (§6) becomes a headline demo moment.

## 9. Sources
The two CAG chapters plus the V1/V2 risk-indicator tables (public CAG publications, cag.gov.in). GST system-change context (Rule 36(4), GSTR-2B, §16(2)(aa)/§16(5), sequential filing, e-invoicing, ARSM, GSTN BO migration) corroborated by the report text and standard GST law; verify exact effective dates if cited externally.
