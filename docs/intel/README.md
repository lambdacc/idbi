# Intel Inventory — IDBI PS3 (Financial Health Score)

Raw source material for the CreditPulse build. **This is an inventory only — no analysis here.** (Analysis lives in `../02-solution-design/`: `intel-cag-gst-feature-analysis.md`, `data-and-intel-sourcing-guide.md`.)

Legend: ✅ saved in repo · ⬜ to download (open, but binary/large — grab via browser) · 🔒 gated (login/sandbox/onboarding).

## Folder structure
```
intel/
  gst/                     CAG GST audit material (source for the risk-indicator analysis)
  aa/   01_specs/          ReBIT FI-type XSD schemas
        02_schema_repo/    Sahamati OpenAPI / standards
        03_sample_payloads/ sample AA data bundles (to add)
        04_reports/        Sahamati/CGAP lending+impact reports (to add)
  upi/  01_specs/ 02_stats/ 03_sample_data/
  epfo/ 01_specs/ 02_stats/ 03_reports/
  signal_recipes/          CGAP / Plaid / arXiv feature-recipe sources (to add)
```

## Saved in repo (✅)

| File | Path | Source | Retrieved |
|---|---|---|---|
| ✅ CAG Report 25/2025 Ch.4 (DORF II) | `gst/Report-No.-25,-2025,-Ch4.pdf` | CAG (provided) | — |
| ✅ CAG Report 7/2024 Ch.4 (DORF I) | `gst/Report-No.-7,-2024,Ch4.pdf` | CAG (provided) | — |
| ✅ V1 risk indicators | `gst/Version 1 risk indicator.xlsx` | CAG (provided) | — |
| ✅ V2 risk indicators + tables | `gst/Version 2 risk indicator and tables.pdf` | CAG (provided) | — |
| ✅ AA **deposit** FI schema (XSD) | `aa/01_specs/deposit.xsd` | ReBIT `specifications.rebit.org.in/.../FISchema/deposit.xsd` | 28 Jun 2026 |
| ✅ AA **GSTR-1/3B** FI schema (XSD) | `aa/01_specs/gstr1_3b_v1.1.0.xsd` | ReBIT `.../FISchema/gstr1_3b_v1.1.0.xsd` | 28 Jun 2026 |
| ✅ AA **OpenAPI** spec (Swagger 2.0) | `aa/02_schema_repo/aa.yaml` | GitHub `Sahamati/account-aggregator-standards/specs/aa.yaml` | 28 Jun 2026 |

*These three schema files are the high-value, machine-readable artifacts — they define the AA bank + GST data shapes our feature engineering reads.*

## To download (⬜ / 🔒) — drop into the folder shown

I could not save these faithfully here (binary PDFs come back as extracted text via the web tool, not the real file; some pages are JS/gated). All are openly reachable in a browser unless marked 🔒.

### Account Aggregator
- ⬜ NBFC-AA API Specification v2.0.0 (PDF) → `aa/01_specs/` — `https://specifications.rebit.org.in/artefacts/NBFC-AA_API_Specification_v2.0.0.pdf`
- ⬜ Full schema repo (git clone) → `aa/02_schema_repo/` — `https://github.com/Sahamati/account-aggregator-standards` (XSDs + fip.yaml/fiu.yaml)
- ⬜ Other live FI XSDs if needed (term_deposit, recurring_deposit, mutual_funds, nps…) → `aa/01_specs/` — same ReBIT `/FISchema/<name>.xsd` path
- ⬜ Sahamati FI-types table (which sources are live; EPF=proposed) → `aa/04_reports/` — `https://sahamati.org.in/data-fi-types-available-on-aa/`
- ⬜ Sahamati AA lending/impact reports (MSME stats) → `aa/04_reports/` — `https://sahamati.org.in/wp-content/uploads/2025/10/Credit-Reimagined-Sahamati-Account-Aggregator-Impact-Report-H1-FY25-8.pdf`
- 🔒 Finvu sample deposit XML payload (copy from sandbox page) → `aa/03_sample_payloads/` — `https://finvu.github.io/sandbox/fip_data_api.html`
- 🔒 Setu AA sample app (mock data) → `aa/03_sample_payloads/` — `https://github.com/SetuHQ/account-aggregator-sample-app`

### UPI
- ⬜ NPCI UPI Product Booklet (PDF) → `upi/01_specs/` — `https://www.npci.org.in/PDF/npci/upi/Product-Booklet.pdf`
- ⬜ NPCI "Guideline on Usage of UPI APIs" OC-95 (PDF) → `upi/01_specs/` — `https://www.npci.org.in/PDF/npci/upi/circular/2020/OC95-GuidelineonUsageofUPIAPIs.pdf`
- ⬜ RBI Payment System Indicators (XLSX, clean stats) → `upi/02_stats/` — `https://rbi.org.in/Scripts/PSIUserView.aspx?Id=10`
- ⬜ NPCI UPI Ecosystem Statistics (P2M/P2P, decline %) → `upi/02_stats/` — `https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics`
- ⬜ Kaggle synthetic UPI sets (with running balance) → `upi/03_sample_data/` — Kaggle "UPI Transactions 2024" / Bijitda UPI dataset (login)

### EPFO
- ⬜ ECR v2 file structure (PDF — to mock the format) → `epfo/01_specs/` — `https://www.epfindia.gov.in/site_docs/PDFs/EPFOUnifiedPortal/Introduction_ECR2.0.pdf`
- ⬜ ECR v1 structure (richer template w/ sample) → `epfo/01_specs/` — `https://www.epfindia.gov.in/site_docs/PDFs/OnlineECR_PDFs/ECR_ForEmployers_FileStructure--OLD.pdf`
- ⬜ EPFO monthly payroll series (calibration) → `epfo/02_stats/` — `https://www.epfindia.gov.in/site_en/Estimate_of_Payroll.php`
- ⬜ CAG Performance Audit of EPFO, Report No. 32 of 2013 (PDF) → `epfo/03_reports/` — `https://cag.gov.in/uploads/download_audit_report/2013/Union_Performance_Ministry_Labour_and_Employment_32_2013.pdf`

### Signal recipes (feature-engineering references)
- ⬜ CGAP — Leveraging Transactional Data for MSE Lending (2024) → `signal_recipes/` — `https://www.cgap.org/research/publication/leveraging-transactional-data-for-micro-and-small-enterprise-lending`
- ⬜ Plaid — How we built LendScore (2025) → `signal_recipes/` — `https://plaid.com/blog/how-we-built-lendscore/`
- ⬜ arXiv 2510.16066 — bank-transaction cash-flow underwriting (PDF) → `signal_recipes/` — `https://arxiv.org/pdf/2510.16066`
- ⬜ RBI U.K. Sinha MSME Committee report (2019) → `signal_recipes/` — `https://www.rbi.org.in/Scripts/PublicationReportDetails.aspx?ID=924`

## Notes
- **EPF/PPF are NOT on the AA rails** (only proposed); NPS is live. Keep EPFO as a mocked/roadmap signal — see the sourcing guide.
- Why some items aren't auto-saved: the approved web tool returns parsed **text**, so XML/YAML schemas save faithfully but **PDFs/binaries don't** — those are listed above for direct download.
- `gst/~BROMIUM/` is a locked stub from the download tool — ignore it.
- Full source list + grades: `../02-solution-design/data-and-intel-sourcing-guide.md`.
