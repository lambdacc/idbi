# Data & Intel Sourcing Guide — UPI, AA, EPFO

**Status:** Phase 2 data-sourcing plan · **Date:** 28 Jun 2026 · **Owner:** Lambdac
**Purpose:** answer "where do we get intel/data on UPI, AA, EPFO" with (a) a concrete **download-and-organise checklist**, (b) **sandbox + synthetic** ways to build a demo with no real data, and (c) a **signal map** into CreditPulse features.
**Feeds:** [`solution-design.md`](solution-design.md) §3-4, [`intel-cag-gst-feature-analysis.md`](intel-cag-gst-feature-analysis.md). Grades: **[P]** primary/official · **[S]** secondary · **[U]** verify before relying.

---

## 0. The one thing to understand first — three rails, three access realities

| Rail | How a lender actually gets it | Granularity | For our demo |
|---|---|---|---|
| **Account Aggregator (AA)** | RBI consent rails; **bank deposit + GST + NPS are LIVE**. **EPF/PPF are NOT live** (only "proposed"). | Clean, structured, consent-bound | **Backbone.** Use ReBIT schemas + AA sandboxes. |
| **UPI** | No FI type of its own. Rides **inside the bank-statement narration** via AA (parse-and-infer, ~50-char string, no MCC) **or** as rich **payment-gateway** data (MCC, merchant, VPA) which is **closed/proprietary**. | AA = narration-grade; PA/PG = rich but captive | Parse narration from AA bank data + synthetic UPI CSVs. |
| **EPFO** | **Not on AA.** Via borrower self-share (UMANG/passbook/DigiLocker) or third-party UAN/EPFO verification APIs; public data is **macro-only** (no firm-level open data). | Per-borrower, consent-gated | **Mock the ECR**; calibrate from open macro datasets. |

**Strategic implication for PS3:** lean the build on **AA bank + GST** (live, schema-defined, demoable), treat **UPI** as a derived layer on top of bank data (plus optional PG data later), and treat **EPFO** as a *mocked, roadmap* signal we model credibly but don't pretend is live. This exactly matches the honesty posture in `intel-cag-gst-feature-analysis.md`.

---

## 1. Priority download checklist (what to fetch & organise)

Ordered by value. ✅ = a real file you can download; ⚠ = JS page / browse-only / verify path.

### A. Account Aggregator — schemas & specs (HIGHEST PRIORITY — these define our feature set)
- ✅ **Bank deposit XSD** (the core schema): `https://specifications.rebit.org.in/api_schema/account_aggregator/FISchema/deposit.xsd` [P]
- ✅ **NBFC-AA API Specification v2.0.0** (consent artefact, flows): `https://specifications.rebit.org.in/artefacts/NBFC-AA_API_Specification_v2.0.0.pdf` [P]
- ⚠ **GST (GSTR-1/3B) XSD**: `https://specifications.rebit.org.in/api_schema/account_aggregator/FISchema/gstr1_3b_v1.1.0.xsd` (path inferred — confirm) [U]; docs HTML: `.../documentation/gstr1_3b_v1.1.0.html` [P]
- ✅ **Canonical schema repo (git clone)**: `https://github.com/Sahamati/account-aggregator-standards` (XSDs + OpenAPI `aa.yaml/fip.yaml/fiu.yaml`) [P]
- ✅ **FI-types live/proposed table** (proof of what's available; EPF=proposed): `https://sahamati.org.in/data-fi-types-available-on-aa/` [P]
- ⚠ **AA ecosystem dashboard** (adoption stats for the pitch): `https://sahamati.org.in/aa-dashboard/` [P]
- ✅ **Sahamati AA lending/impact reports** (MSME numbers for business case): `https://sahamati.org.in/wp-content/uploads/2025/10/Credit-Reimagined-Sahamati-Account-Aggregator-Impact-Report-H1-FY25-8.pdf` and `.../AA-Lending-Report-Abridged.pdf` [P]

### B. UPI — specs, fields & stats
- ✅ **NPCI UPI Product Booklet** (txn types, ecosystem): `https://www.npci.org.in/PDF/npci/upi/Product-Booklet.pdf` [P]
- ✅ **NPCI "Guideline on Usage of UPI APIs" OC-95**: `https://www.npci.org.in/PDF/npci/upi/circular/2020/OC95-GuidelineonUsageofUPIAPIs.pdf` [P]
- ✅ **RBI Payment System Indicators** (clean XLSX time-series — best machine-readable stats): page `https://rbi.org.in/Scripts/PSIUserView.aspx?Id=10` [P]
- ⚠ **NPCI UPI Ecosystem Statistics** (P2M/P2P split, decline %): `https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics` (on-page, scrape) [P]
- **Field reference** (since the full NPCI API spec is members-only): Setu deeplink/callback doc `https://docs.setu.co/payments/upi-deeplinks/notifications` [S] — gives VPA, amount, RRN/UTR, MCC, status/decline codes.
- ✅ **RBI Payment Aggregator Directions 2025** (why PG data carries MCC/merchant ID): `https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=12896` [P]

### C. EPFO — structures, stats & the accessibility truth
- ✅ **ECR v2 file structure** (11-field `#~#` format — to mock it): `https://www.epfindia.gov.in/site_docs/PDFs/EPFOUnifiedPortal/Introduction_ECR2.0.pdf` [P]
- ✅ **ECR v1 structure** (richer 25-field template w/ sample): `https://www.epfindia.gov.in/site_docs/PDFs/OnlineECR_PDFs/ECR_ForEmployers_FileStructure--OLD.pdf` [P]
- ⚠ **EPFO monthly payroll series** (net-new-subscriber, for calibration): `https://www.epfindia.gov.in/site_en/Estimate_of_Payroll.php` (PDF tables, scrape exact hrefs) [P]
- ✅ **CAG Performance Audit of EPFO — Report No. 32 of 2013** (the CAG-method analogue; arrears/coverage findings): `https://cag.gov.in/uploads/download_audit_report/2013/Union_Performance_Ministry_Labour_and_Employment_32_2013.pdf` [P]
- ✅ **Establishment Search** (public per-employer record, links entities by PAN): `https://unifiedportal-emp.epfindia.gov.in/publicPortal/no-auth/misReport/home/loadEstSearchHome` [P]

### D. Cross-cutting "signal recipe" sources (how practitioners turn this data into features)
- ✅ **CGAP — Leveraging Transactional Data for MSE Lending (2024)**, Indian case studies: `https://www.cgap.org/research/publication/leveraging-transactional-data-for-micro-and-small-enterprise-lending` [P]
- ✅ **Plaid — How we built LendScore (2025)** (cash-flow feature engineering + SHAP): `https://plaid.com/blog/how-we-built-lendscore/` [P]
- ✅ **arXiv 2510.16066** — bank-transaction cash-flow underwriting for MSMEs (closest methodological peer): `https://arxiv.org/pdf/2510.16066` [P]
- ✅ **RBI U.K. Sinha MSME Committee (2019)** (cash-flow lending mandate, credit gap): RBI landing `https://www.rbi.org.in/Scripts/PublicationReportDetails.aspx?ID=924` [P]

## 2. Sandboxes & sample data (build the demo with zero real data)

- **Setu AA sandbox** — mock data for all FI types, end-to-end consent flow; sample app `https://github.com/SetuHQ/account-aggregator-sample-app`; docs `https://docs.setu.co/data/account-aggregator/overview` [P]
- **Finvu sandbox** — inject your own test accounts/txns; **ready copy-paste deposit XML payload** on the page: `https://finvu.github.io/sandbox/fip_data_api.html` [P]
- **OneMoney / SahamatiNet** developer sandboxes (FIP-simulator with scenarios) [P]
- **Razorpay test mode** for a *live* UPI-capture demo path (`success@razorpay` / `failure@razorpay`) [P]
- Open synthetic transaction CSVs (offline feature-engineering today): Kaggle "UPI Transactions 2024" and the **Bijitda UPI set with running balance** (closest to bank-statement shape); `Sparkov` generator + `faker-ind` for Indian-realistic volume [S]

## 3. Synthetic-data plan (the highest-leverage "other way to build intel")

Because real data is gated until the IDBI sandbox (stage-2), the fastest path is to **generate our own realistic cohort** from the public schemas and calibrate it from open macro data:

1. **Shape from schemas:** drive a generator (e.g. `json-schema-faker`) off the **ReBIT deposit XSD + GST schema** (and the Finvu sample payload) → valid AA-shaped bank + GST bundles.
2. **UPI layer:** synthesize UPI rows *inside* the bank narration (CR/DR, VPA-like strings, P2M vs P2P), so our parser/feature code is exercised on production-shaped narration — plus optional clean PG-style records (with MCC) for the "richer data" story.
3. **EPFO layer:** generate **ECR v2** files (`#~#`, 11 fields; EE 12%, ER 8.33% EPS + 3.67% EPF, ₹15k EPS ceiling) → derive headcount/wage/contribution-regularity signals.
4. **Calibrate realism from open datasets** so the cohort isn't toy data:
   - **ASI** (factory employment & wages) `https://microdata.gov.in/NADA/index.php/catalog/ASI`, **Udyam/MSME** counts `https://dashboard.msme.gov.in/`, **PLFS** wages, **EPFO payroll series**, **RBI PSI** for payment volumes. [P]
5. **Inject health/fraud profiles** (healthy / stressed / inflated-turnover) with known labels so the eval harness (G1 gate) and the Turnover-Authenticity sub-module have ground truth — same discipline as ReconWise golden datasets.

This gives us a labelled, schema-valid, India-calibrated synthetic cohort for stage-1 — and the same generators plug into IDBI mock data at stage-2.

## 4. Signal map → CreditPulse pillars (what each rail contributes)

- **AA bank deposit** → cash-flow health (balance level/volatility, low-balance frequency), obligations (EMI/NACH bounce, OD/CC utilisation), inflow structure (counterparty concentration), and the **GST-vs-bank consistency** check. *(Richest, live, schema-defined.)*
- **GST (via AA)** → revenue quality & discipline + the GSTN-stable ratio features from the CAG analysis (ITC/tax-paid, IGST/CGST+SGST, exempt/taxable, credit-notes/turnover).
- **UPI** (from bank narration; PG later) → inflow velocity, P2M vs P2P mix, customer breadth/concentration, recurring inflows, seasonality, refund patterns.
- **EPFO** (mocked) → workforce size & trend, contribution regularity, wage-bill trend, attrition — going-concern/scale proxy; **arrears = strongest distress marker** (statutory first charge + IBC carve-out).

## 5. CAG-relevant note (your domain advantage)
- The CAG-mining method that worked for GST **transfers**: for EPFO there's a real analogue — **CAG Performance Audit of EPFO, Report No. 32 of 2013** (arrears, coverage-control failures) — useful for distress-signal logic and credibility. [P]
- **No standalone CAG report on UPI / digital payments exists** (checked) — don't promise one; the authoritative UPI intel is RBI/NPCI/BIS/World-Bank + CGAP/Plaid for signal recipes. [P/U]
- Adjacent: **CAG Report No. 13 of 2020 audits NPS** (not EPFO) — flagged, not central.

## 6. Proposed `intel/` folder structure (for what you download)
```
intel/
  gst/                      # existing CAG GST material
  aa/
    01_specs/               deposit.xsd, gstr1_3b.xsd, NBFC-AA_API_Spec_v2.0.0.pdf
    02_schema_repo/         git clone Sahamati/account-aggregator-standards
    03_sample_payloads/     Finvu/Setu sample XML+JSON
    04_reports/             Sahamati lending/impact PDFs, CGAP
  upi/
    01_specs/               NPCI Product Booklet, OC-95, Setu field doc
    02_stats/               RBI PSI XLSX, NPCI ecosystem stats
    03_sample_data/         Kaggle CSVs, Sparkov output
  epfo/
    01_specs/               ECR v2 + v1 structure PDFs
    02_stats/               EPFO payroll series, ASI/Udyam/PLFS extracts
    03_reports/             CAG No.32/2013, EPFO annual report
  signal_recipes/           CGAP, Plaid, arXiv 2510.16066, U.K. Sinha report
```

## 7. What would help most from you (prioritised asks)
1. **AA schemas** (deposit.xsd, GST xsd) + the **Sahamati FI-types table** — these directly define our feature engineering. *(I can also pull these via the schema repo if you'd rather I fetch.)*
2. **CAG EPFO Report No. 32/2013** + **ECR v2 structure PDF** — for the EPFO signal/mock layer.
3. **CGAP (2024)** + **Plaid LendScore** + **arXiv 2510.16066** — the feature-recipe trio I'll mine into a signal dictionary (a CAG-style analysis doc, like we did for GST).
4. Anything you can get on **IDBI's expected PS3 data fields** from the 30 Jun session — that trumps all of the above.

## 8. Caveats / verify-before-relying
- Re-confirm the **GST XSD path** and the **deposit schema version your FIP returns** (1.2 vs 2.0.0). [U]
- NPCI stat pages and the EPFO payroll page are **JS/scrape** — grab exact file hrefs. [U]
- Vendor signal claims (FinBox "500+ predictors", thresholds) are **self-reported** [S] — validate in our eval harness.
- **EPF-via-AA is not live** — keep it mocked/roadmap. NPS is the only AA pension signal. [P]
- No India peer-reviewed AA-MSME default-model paper found; the Malaysia arXiv is the closest — present EPFO/UPI signals as **well-reasoned proxies**, validated in-harness, not proven.
