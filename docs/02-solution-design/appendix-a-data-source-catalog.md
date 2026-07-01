# Appendix A — Prioritized Data-Source Catalog & Composite Indicators

**Status:** Phase 1 research deliverable · **Date:** 01 Jul 2026 · **Owner:** Lambdac
**Reads with:** [`solution-design.md`](solution-design.md) (existing 4-source spec — GST, Bank/UPI, AA, EPFO, Bureau), [`data-and-intel-sourcing-guide.md`](data-and-intel-sourcing-guide.md) (access-reality detail for GST/AA/UPI/EPFO), [`implementation-plan.md`](implementation-plan.md) (consumes this catalog for the build), [`appendix-b-synthetic-data-plan.md`](appendix-b-synthetic-data-plan.md) (per-source generator spec for every Retain-tier source below), [`../../.claude/skills/idbi-hackathon/SKILL.md`](../../.claude/skills/idbi-hackathon/SKILL.md) (the rubric this catalog follows)

---

## 0. Why this appendix exists

IDBI Innovate 2026's second orientation session was explicit: **GST, UPI, Account Aggregator (AA), and EPFO are the starting point, not the answer.** A strong PS3 submission has to (a) name additional electronic data sources beyond the obvious four, (b) be honest about which of them are *actually* obtainable today versus merely plausible-sounding, and (c) show how combining sources produces signals that are harder to manipulate than any single input.

This appendix answers that bar directly. It evaluates **34 candidate data sources** — the 5 already-established core sources (GST, UPI, AA bank/deposit, EPFO, Credit Bureau) plus a widened 29-candidate sweep across statutory, trade/logistics, utilities/premises, licensing, commerce, and risk/legal domains — against the `idbi-hackathon` SKILL's fixed 12-field rubric, tiers every one of them into **Retain (core)** / **Retain (enrichment)** / **Reject** (with a documented reason for every reject), and closes with a **composite-indicator catalog**: 13 cross-source signals, each naming its constituent sources, the fused signal it produces, and — the crux of the "harder to manipulate" argument — exactly which independently-governed systems a fraudster would have to compromise *simultaneously* to fake it.

**Research method.** For the 12 candidates flagged as needing verification (MCA21, ESIC, ITR/AIS/26AS, e-way bill, FASTag/IHMCL, DGFT/ICEGATE, DISCOM electricity, property tax, telecom, ONDC, GeM, e-commerce marketplaces), findings below are grounded in web research as of mid-2026, with citations collected in §7. The remaining 22 candidates are assessed from domain knowledge, per the skill's discipline of stating "unknown" rather than leaving a field blank — none required that here, but confidence is marked accordingly per source.

**Honesty discipline.** Where the user's first-pass tier guess and this appendix's research disagree, the appendix overrides the guess and says why (§1). Where a source is rejected, one documented reason is given, not a silent drop (§4). Where a mandated composite's named constituent (e.g., telecom in "business continuity") turns out not to clear this catalog's access bar, that gap is stated plainly rather than papered over (§5).

---

## 1. Tier overrides from the first-pass guesses

Eight candidates land in a different tier than the seed list's first-pass guess, all driven by the web research in §7:

| Source | First-pass guess | This appendix's tier | Why the override |
|---|---|---|---|
| MCA21 | Core | **Enrichment** | Only covers registered companies/LLPs — the majority-proprietorship MSME base is entirely outside its scope — and access is via paid commercial resellers (Probe42, Tofler, Zauba Corp), not an official lender-facing API. |
| Electricity (DISCOM) | Core | **Enrichment** | Today's access is fragmented across 40+ DISCOMs with no unified API; no electricity/utility FI type exists on the AA framework; BBPS gives bill-due-amount only, not consumption history. Still central to two composite indicators (§5), so retained prominently — just not "core" by the access-reality bar. |
| DGFT/IEC + ICEGATE | Core | **Enrichment** | ICEGATE's own CSP (Customs Service Provider) API terms explicitly **prohibit** using its data for "financial product selling"; narrow applicability (exporters/importers only). Real access route is self-share or the exporter's own AD-bank relationship. |
| ONDC seller/network data | Core | **Reject** | As of the latest count, only ~9 network participants and 3 lenders (Aditya Birla Finance, DMI Finance, Karnataka Bank) are live since Jan 2024 pilots; no standalone seller-transaction API exists. Pilot/roadmap-stage, not a 2026 production signal — revisit as the network matures. |
| Commercial LPG | Enrichment | **Reject** | No electronic access path exists at all — not even a public bill-lookup portal comparable to what electricity or property tax have; OMC distributor records are entirely internal. |
| Telecom (mobile/broadband) | Enrichment | **Reject** | The credit-relevant tenure/usage signal is locked inside telcos' own closed-loop NBFC lending arms (Jio Financial Services, Airtel's own NBFC licence Feb 2026); only KYC-grade fraud-screening (MNRL/MNV) is externally accessible, which is a KYC control, not a credit/alt-data signal. |
| ESIC contributions | Enrichment | **Reject** | No API or consent path exists — weaker access than its close cousin EPFO — and where a contribution figure is obtainable at all (via self-shared challans) it is redundant with EPFO's workforce signal for the segment where both apply. |
| E-way bill | Core | Core *(confirmed, no override)* | A genuine, real-time, GSP-mediated API with proven consent-sharing lending products (Vayana Network, CredAvenue/Yubi) already exist on top of it — the strongest logistics-side confirmation of GST turnover available today. |

All other first-pass guesses held up under research or reasoning and are retained as originally tagged.

---

## 2. Retain — Core (8 sources)

These are electronically available today, realistically obtainable at low-to-medium integration cost, updated frequently, hard to manipulate, and useful across most MSME sectors — the backbone CreditPulse builds on.

#### 2.1 GST (GSTR-1 / GSTR-3B)

| Field | Value |
|---|---|
| Description | Monthly/quarterly outward-supply return (GSTR-1) and self-assessed summary tax return (GSTR-3B) — the primary declared-turnover record for any GST-registered MSME. |
| Owner / generator | GSTN, filed by the taxpayer. |
| Electronic availability | Yes — mature, structured, today. |
| Access model | Consent-based/AA (GSTN is a live AA FI type) or regulated API via GST Suvidha Providers (GSPs) with taxpayer authorization. |
| Update frequency | Monthly (GSTR-3B/1), or quarterly under the QRMP scheme. |
| Practical availability | High — live AA FI type, standardized ReBIT XSD, mature GSP ecosystem. |
| Cost / integration complexity | Low-medium. |
| Fraud / authenticity indicators | GSTR-1-vs-3B mismatch; return-filing gaps/defaults; sudden deregistration; HSN-code inconsistency with claimed business line. |
| Credit / risk indicators | Turnover level & trend, seasonality, customer concentration (from invoice counterparties), filing regularity/timeliness, ITC-to-tax-paid ratio. |
| Manipulation resistance | Medium-high — statutory filing cross-validated by GSTN's own 2A/2B auto-population; self-declared turnover can still be shaded before triggering audit flags. |
| Limitations | Excludes unregistered/very-small MSMEs; composition-scheme filers give coarser detail; lags real-time by weeks; misses the cash economy. |
| Confidence | High. |

#### 2.2 Account Aggregator — bank / deposit data

| Field | Value |
|---|---|
| Description | Consent-based flow of a business's bank-account statement (balances, transactions) via the RBI-regulated AA network (Sahamati ecosystem). |
| Owner / generator | Banks (as FIPs), aggregated via licensed NBFC-AAs. |
| Electronic availability | Yes — live, ReBIT `deposit.xsd`-standardized. |
| Access model | Consent-based/AA — RBI-regulated, borrower approves a signed consent artefact. |
| Update frequency | Real-time/on-demand pull, typically covering a trailing ~6-18 months. |
| Practical availability | High — an already-mainstream digital-lending flow in India. |
| Cost / integration complexity | Medium (well-trodden path via Setu/Finvu/OneMoney SDKs). |
| Fraud / authenticity indicators | Bounced cheques/NACH failures, circular fund transfers, pre-application balance "window dressing." |
| Credit / risk indicators | Average balance, balance volatility, inflow/outflow trend, overdraft utilization, EMI/obligation detection. |
| Manipulation resistance | High — sourced directly from the bank of record under a signed consent artefact, not self-reported; still gameable via short-term related-party balance top-ups just before a data pull. |
| Limitations | Only covers accounts the borrower consents to share; requires the bank to be a live FIP (most large banks are, some cooperative/regional banks aren't yet). |
| Confidence | High. |

#### 2.3 UPI (via AA bank narration + optional payment-gateway data)

| Field | Value |
|---|---|
| Description | Digital-payment transaction trail — either narration-embedded inside AA bank-statement data (~50-char string, CR/DR, no MCC) or richer payment-gateway (PG)/POS data with MCC, VPA, merchant ID (proprietary). |
| Owner / generator | NPCI (rails), banks (statements), payment aggregators (PG data). |
| Electronic availability | Partial — narration form is live via AA bank data; rich PG form exists but is closed/proprietary to the PA/PG holding the merchant relationship. |
| Access model | Consent-based/AA (narration) or licensed/commercial (PG data — needs a data-sharing deal with a PA like Razorpay/Cashfree, or merchant self-export). |
| Update frequency | Real-time to daily (transaction-level). |
| Practical availability | High for the narration form (rides free on AA bank data); low-medium for MCC-level PG data (needs a separate commercial relationship). |
| Cost / integration complexity | Low (narration) to high (PG partnership integration). |
| Fraud / authenticity indicators | Receipt velocity/frequency (real operating-footfall proxy), P2M-vs-P2P mix, refund/reversal-rate spikes (circular-transaction fraud). |
| Credit / risk indicators | Inflow velocity & regularity, customer breadth/concentration, seasonality. |
| Manipulation resistance | Medium — narration strings can be gamed by round-tripping money between related accounts, though the GST-vs-bank cross-check partly catches this. |
| Limitations | Narration form has no MCC/merchant category; hard to separate personal vs business inflows on a mixed-use proprietor account; rich PG data isn't accessible without a partnership. |
| Confidence | High. |

#### 2.4 EPFO (ECR)

| Field | Value |
|---|---|
| Description | Monthly Electronic Challan cum Return filed by employers — per-employee UAN, wages, PF/EPS/EDLI contributions. |
| Owner / generator | EPFO, filed by the employer establishment. |
| Electronic availability | Yes, but **not on AA** — accessible via the EPFO Unified Portal/employer login; "Establishment Search" is a public per-employer lookup. |
| Access model | Consent-based self-share (portal/passbook/UMANG) or third-party UAN-verification APIs; EPF/PPF is only "proposed," not live, on AA. |
| Update frequency | Monthly. |
| Practical availability | Medium — public macro data is available; firm-level detail requires borrower cooperation since no open bulk API exists. |
| Cost / integration complexity | Medium (manual/consent-share flow today). |
| Fraud / authenticity indicators | Sudden mass employee entries/exits, arrears (statutory first-charge — one of the strongest distress markers), ghost-employee patterns. |
| Credit / risk indicators | Headcount trend, wage-bill trend, contribution regularity — a going-concern/scale proxy. |
| Manipulation resistance | Medium — statutory filing with penalties, but headcount/wages can be shaped short-term; arrears are hard to fake away. |
| Limitations | Only covers formal-sector employees above the applicability threshold; many small MSMEs are exempt or under-report headcount; clunky integration since it isn't on AA rails. |
| Confidence | High. |

#### 2.5 Credit Bureau (CIBIL / CRIF MSME)

| Field | Value |
|---|---|
| Description | Consolidated credit history — existing loans, repayment/delinquency track record, enquiry footprint, MSME-specific rank/score. |
| Owner / generator | CIBIL (TransUnion), CRIF High Mark, Experian, Equifax — RBI-regulated Credit Information Companies. |
| Electronic availability | Yes — mature regulated API product. |
| Access model | Regulated API — bureau membership required, borrower consent for the specific pull. |
| Update frequency | Monthly (bureau refresh from member reporting). |
| Practical availability | High for an existing formal-credit borrower; **low/zero for a genuinely NTC MSME** — precisely the segment PS3 targets. |
| Cost / integration complexity | Low-medium (mature bureau-API integration pattern). |
| Fraud / authenticity indicators | Identity mismatch, enquiry-velocity spikes (loan-shopping/stacking), settled/written-off flags. |
| Credit / risk indicators | DPD history, current exposure & utilization, vintage of oldest credit line, MSME rank. |
| Manipulation resistance | High — third-party regulated record, cannot be self-altered. |
| Limitations | Structurally thin/blank for credit-invisible MSMEs — valuable as a cross-check, not a primary signal for the NTC/NTB target segment. |
| Confidence | High. |

#### 2.6 Udyam Registration

| Field | Value |
|---|---|
| Description | Mandatory self-declared MSME registration — enterprise category (micro/small/medium), investment & turnover, activity/NIC code, linked PAN/GSTIN. |
| Owner / generator | Ministry of MSME (Udyam portal); self-filed, auto-validated against PAN/GST data since the 2021 revamp. |
| Electronic availability | Yes. |
| Access model | Public — the Udyam portal's "Verify Udyam Registration" lookup by URN is free and open. |
| Update frequency | Irregular (edited by the enterprise on change; turnover/investment now auto-pulled from linked PAN/GSTIN at renewal). |
| Practical availability | High — near-universal MSME-scheme prerequisite, free public verification, low integration friction. |
| Cost / integration complexity | Low. |
| Fraud / authenticity indicators | Category-mismatch fraud (declaring "micro" to access subsidized schemes despite higher actual turnover), URN-PAN mismatch. |
| Credit / risk indicators | Formal MSME status (scheme/collateral-free eligibility), declared investment/turnover band, activity/NIC sector-risk overlay, registration vintage. |
| Manipulation resistance | Medium — post-2021 auto-pull from linked PAN/GSTIN reduces (doesn't eliminate) misdeclaration. |
| Limitations | A registration-status snapshot, not a transaction feed — near-zero ongoing signal after initial registration. |
| Confidence | High. |

#### 2.7 PAN / GSTIN verification (Protean/NSDL)

| Field | Value |
|---|---|
| Description | Real-time identity/existence verification — confirms a PAN or GSTIN is genuine, active, and matches the declared legal name. |
| Owner / generator | Protean eGov Technologies (formerly NSDL e-Gov) for PAN; GSTN for GSTIN status. |
| Electronic availability | Yes. |
| Access model | Regulated API — Protean/NSDL's paid PAN-verification API (already standard in bank/NBFC KYC stacks); GSTN's "Search Taxpayer" GSTIN lookup is public. |
| Update frequency | Real-time. |
| Practical availability | High — already a standard KYC building block for every regulated Indian lender. |
| Cost / integration complexity | Low. |
| Fraud / authenticity indicators | This *is* the fraud/authenticity check — catches fake/cancelled/inoperative PAN, name mismatches, cancelled/suspended GSTIN. |
| Credit / risk indicators | Minimal directly — a gatekeeping/identity layer; GSTIN status (active/suspended/cancelled) is itself a going-concern flag. |
| Manipulation resistance | High — authoritative government-source lookup, not self-reported. |
| Limitations | A binary existence/status check, not a behavioral or financial signal. |
| Confidence | High. |

#### 2.8 E-way bill (NIC/GSTN EWB system)

| Field | Value |
|---|---|
| Description | Mandatory electronic waybill for goods movement above value/distance thresholds — origin/destination, value, HSN, transporter/vehicle ID, validity window. |
| Owner / generator | GSTN (E-Way Bill portal/API — `ewaybillgst.gov.in`), same GSP ecosystem as GST returns. |
| Electronic availability | Yes — a real, documented API (GSTN E-Way Bill API Developer Portal). |
| Access model | Regulated/licensed API — restricted to the GSTIN-holding taxpayer/transporter, self-registered or via an empanelled GSP (Masters India, IRIS GST, Cygnet, TCS, Deloitte, EY); a lender needs the borrower's GSTIN/OTP consent shared through an ASP/GSP — the same pattern already used by supply-chain/invoice-financing platforms (Vayana Network, CredAvenue/Yubi, IRIS GST).[^ewb] |
| Update frequency | Real-time (per shipment/dispatch). |
| Practical availability | Medium — a real API with proven consent-sharing lending products already live, though each pull needs active borrower credential/OTP cooperation rather than a standing AA-style consent artefact. |
| Cost / integration complexity | Medium (GSP integration + per-pull consent flow). |
| Fraud / authenticity indicators | E-way-bill-vs-GSTR-1/3B reconciliation (goods actually moved vs turnover declared — catches invoice-only/no-movement fraud), destination-concentration anomalies. |
| Credit / risk indicators | Shipment volume/value trend and frequency (real-time activity proxy ahead of the monthly GST cycle), counterparty/geographic spread. |
| Manipulation resistance | High — generated at the moment of goods movement and cross-validated against GST returns by GSTN itself. |
| Limitations | Only applies to goods movement above the threshold — irrelevant for services-only MSMEs; requires GSP/consent integration, not free/public. |
| Confidence | High. |

---

## 3. Retain — Enrichment (18 sources)

Valuable, complementary, and retained — but narrower in sector applicability, weaker access model, or lower update frequency than the core set. Grouped by domain.

### Statutory

#### 3.1 MCA21 (directors, beneficial ownership, charges)

| Field | Value |
|---|---|
| Description | Corporate registry — director identity/DIN, Significant Beneficial Owner (SBO) filings, charges/mortgages registered against company assets (Form CHG), annual filings (AOC-4, MGT-7). |
| Owner / generator | Ministry of Corporate Affairs (MCA21 V3 portal). |
| Electronic availability | Partial — basic company/director master data is public/free (MCA21 V3 + `data.gov.in` "Company Master Data" bulk CSV); full filings (financials, charges, SBO) require paid per-document purchase, no official bulk feed. |
| Access model | Public (master data) + licensed (full filings via commercial resellers — Probe42, Tofler, Zauba Corp, Karza/Signzy, CorpDataLibrary — who aggregate via bulk document pulls, not an MCA-sanctioned lender API).[^mca21] |
| Update frequency | Irregular/event-driven (charges within 30 days of creation; annual filings once a year). |
| Practical availability | Medium — director/charge data realistically obtainable via paid resellers already embedded in many bank/NBFC loan-origination systems, but no official real-time or cheap bulk API. |
| Cost / integration complexity | Medium (per-document/reseller-subscription cost). |
| Fraud / authenticity indicators | Undisclosed charges/liens against company assets (double-financing red flag), director disqualification, SBO mismatches vs claimed ownership. |
| Credit / risk indicators | Existing secured-debt footprint (a real cross-check against declared borrowings), director track record across other companies, filing-compliance timeliness. |
| Manipulation resistance | High — third-party statutory registry; charges especially hard to hide since they must be filed to be legally enforceable. |
| Limitations | Only applies to registered companies/LLPs — excludes proprietorships and partnerships, a large share of MSMEs; no official bulk/real-time lender API; reseller data quality varies. |
| Confidence | High. |

#### 3.2 ITR / AIS / Form 26AS (consent-based)

| Field | Value |
|---|---|
| Description | Income-tax return, Annual Information Statement (comprehensive taxpayer financial-transaction summary), and Form 26AS (tax-credit statement) for the business/proprietor. |
| Owner / generator | Income Tax Department/CBDT (e-filing portal). |
| Electronic availability | Yes at source (taxpayer's own e-filing portal), but **not live via AA**. |
| Access model | Consent-based self-share only — Sahamati's live FI-types registry lists only RBI/SEBI/IRDAI/PFRDA regulator families plus GSTN as live; no CBDT/ITR FI-type exists despite 2022-23 pilot chatter.[^itraa] Today a lender only gets this via the borrower downloading ITR-V/26AS/AIS and uploading, parsed by TSPs (Perfios, Karza) via OCR — not a data pull. |
| Update frequency | Annual (ITR) to near-continuous at source (AIS/26AS), but not accessible at that cadence by a lender. |
| Practical availability | Low — document-upload/OCR workflow only, no structured API/consent-artefact flow. |
| Cost / integration complexity | Medium (OCR/document-parsing integration, borrower friction of manual download+upload). |
| Fraud / authenticity indicators | ITR-vs-GST-turnover reconciliation (a strong cross-check when both are available), AIS-reported high-value transactions vs claimed profile. |
| Credit / risk indicators | Declared income/profit trend, tax-paid history (a genuine-profitability proxy beyond GST's turnover-only view), TDS-credit trail. |
| Manipulation resistance | Medium — statutory filing with penalties, but purely self-declared profit is easier to shape pre-filing than GST turnover (which has e-way-bill/2A-2B cross-validation). |
| Limitations | Not on AA rails; document-based collection is exactly the friction PS3 is trying to move past; annual cadence is coarser than GST/bank. |
| Confidence | High. |

### Trade & logistics

#### 3.3 FASTag / NHAI toll data (via IHMCL/NETC)

| Field | Value |
|---|---|
| Description | Electronic toll-transaction records tied to a vehicle's FASTag/RFID tag crossing NHAI/state toll plazas — a movement/logistics-activity trail for vehicle-owning MSMEs. |
| Owner / generator | NPCI (NETC — National Electronic Toll Collection), IHMCL (issuer/plaza governance), the vehicle's issuing bank. |
| Electronic availability | Yes — ~11 crore tags, 1,100+ plazas, all electronic at source. |
| Access model | Regulated/licensed — raw transaction data sits with NPCI-member issuer banks under NDA; consumer-facing aggregators (Setu, ZuelPay) offer consent-based recharge/balance/history APIs but need a fresh commercial/legal agreement; no open API and no lending-specific underwriting product exists today.[^fastag] |
| Update frequency | Near real-time per crossing; bank/NETC settlement reconciled daily. |
| Practical availability | Low — technically pullable via a bank/aggregator partnership, but no ready-made underwriting integration exists; would require new partnership-building. |
| Cost / integration complexity | High (new NDA/partnership needed). |
| Fraud / authenticity indicators | Toll-crossing pattern vs claimed operating routes/fleet size; tag-sharing/misuse anomalies. |
| Credit / risk indicators | Crossing frequency/route diversity as a logistics-activity proxy, fleet-utilization trend. |
| Manipulation resistance | High — third-party (bank/NPCI) metered record, cannot be self-reported or altered. |
| Limitations | Relevant only to vehicle-owning logistics/transport/distribution MSMEs; no productized lender API exists yet — a real gap versus the e-way-bill/GSP ecosystem. |
| Confidence | High. |

#### 3.4 Vahan / Parivahan vehicle registration

| Field | Value |
|---|---|
| Description | Vehicle registration database — RC details, ownership, fitness/permit/insurance validity, vehicle class — for commercial vehicles owned by an MSME. |
| Owner / generator | MoRTH / state transport departments, via the VAHAN national register. |
| Electronic availability | Yes. |
| Access model | Public — Parivahan/Vahan's "know your vehicle details" search API is public (registration number → owner, class, fitness/insurance/PUC validity); bulk API access is available to registered entities (already used operationally by vehicle-loan lenders for hypothecation/NOC checks). |
| Update frequency | Near real-time (updated on each RTO transaction). |
| Practical availability | High — already used operationally by auto/vehicle-loan lenders. |
| Cost / integration complexity | Low. |
| Fraud / authenticity indicators | Mismatched ownership vs claimed fleet size; expired fitness/insurance/permit (non-operational or distressed logistics proxy); duplicate/cloned registration numbers. |
| Credit / risk indicators | Fleet size & vehicle age/class (asset base for a transport MSME), hypothecation status, permit type (goods-carriage vs private). |
| Manipulation resistance | High — centrally maintained RTO record, hard for a borrower to alter. |
| Limitations | Only rich for transport/logistics/vehicle-owning MSMEs; shows registration status, not utilization/movement. |
| Confidence | High. |

#### 3.5 DGFT / IEC + ICEGATE shipping bills

| Field | Value |
|---|---|
| Description | Export/import trade documentation — Importer-Exporter Code (IEC) registration/status, shipping bills, bills of entry, export-proceeds realization (via RBI's EDPMS). |
| Owner / generator | DGFT (IEC registration), CBIC/ICEGATE (customs filings), RBI (EDPMS), the exporter's AD (authorized dealer) bank. |
| Electronic availability | Partial — IEC identity/status is a genuine regulated API (API Setu "IEC Verification API"); full shipping-bill/transaction-history access by third parties is **explicitly barred by ICEGATE's own CSP policy** for financial-product-selling use.[^dgft] |
| Access model | Split — public/regulated API for IEC identity check only; everything else is self-share (exporter shares shipping-bill/eBRC PDFs) or via the exporter's own AD bank. |
| Update frequency | Real-time at source; effectively irregular for a lender, since it depends on manual exporter sharing. |
| Practical availability | Low for transaction/shipment history (manual/PDF only, policy-barred via the API route); medium for identity/IEC-status verification only. |
| Cost / integration complexity | Medium (API Setu registration) to high (manual document collection). |
| Fraud / authenticity indicators | IEC status (active/suspended) vs claimed export-business identity; shipping-bill values vs claimed export turnover (where self-shared). |
| Credit / risk indicators | Export volume/value trend, buyer-country diversification, realization timeliness (EDPMS overdue-realization is a strong distress signal). |
| Manipulation resistance | Medium — third-party filed with customs when actually obtained; self-shared PDFs are cherry-pickable. |
| Limitations | Narrow applicability (exporters/importers only); explicit policy prohibition on lending use of ICEGATE API data is a real access blocker; best realized via a lender's own AD-bank relationship. |
| Confidence | High. |

### Utilities & premises

#### 3.6 Electricity (DISCOM billing / smart meter)

| Field | Value |
|---|---|
| Description | Commercial electricity connection billing and (increasingly) smart-meter consumption data for a business premises — sanctioned load, monthly consumption (kWh), bill-payment regularity. |
| Owner / generator | ~40+ state/private DISCOMs (fragmented, no national utility); RDSS driving smart-meter rollout. |
| Electronic availability | Partial — each DISCOM runs its own portal; RDSS smart meters are only ~25-27% installed (5.4-5.8 crore of 20.33 crore sanctioned) as of early 2026, targeting FY2028; no unified national consumption database exists.[^discom] |
| Access model | Fragmented per-DISCOM; BBPS/Bharat Connect gives consent-based bill-fetch (amount due/due date only, **not** consumption history) and needs BBPOU empanelment; no electricity/utility FI type exists on the AA framework; commercial "bill APIs" (Karza/Perfios, AuthBridge, Signzy) scrape DISCOM portals for KYC/address-proof only. |
| Update frequency | Monthly/bimonthly billing cycles; smart meters capture 15-minute data internally but it isn't exposed externally. |
| Practical availability | Low — no lender-grade unified API exists; existing tools solve KYC/address-proof, not consumption-trend analytics, across 40+ fragmented DISCOMs. |
| Cost / integration complexity | High (per-DISCOM integration effort). |
| Fraud / authenticity indicators | Active connection + regular billing at the claimed business address (premises-existence proxy); sanctioned-load tier vs claimed production scale. |
| Credit / risk indicators | Consumption level/trend as an energy-intensity/production-activity proxy (strong for manufacturing); payment regularity/disconnection history as a distress signal. |
| Manipulation resistance | High where obtained — metered by the DISCOM, cannot be self-reported or inflated; the *access difficulty* is the limitation, not the data's integrity. |
| Limitations | Fragmentation across 40+ DISCOMs with no standard API is the core blocker; RDSS smart-meter rollout is still mid-way; BBPS gives payment-due info only, not consumption. |
| Confidence | High. |

#### 3.7 Property tax (municipal)

| Field | Value |
|---|---|
| Description | Municipal property-tax assessment and payment record for a business's registered premises — assessed category/value, payment status/history. |
| Owner / generator | 250+ Urban Local Bodies; MoHUA's UPYOG/DIGIT platform is unifying property-tax modules (live in 12+ states as of 2024-25, others still building). |
| Electronic availability | Partial — fragmented across ULBs; UPYOG exposes a documented "PT Service API" as an open public good where adopted.[^ptax] |
| Access model | Fragmented per-municipality + an emerging open API (UPYOG) in adopting states; BBPS lists property tax as a biller category (bill-fetch via Setu/Federal Bank), needing the customer's PTIN per transaction — not an AA/FI-type category. |
| Update frequency | Annual/half-yearly (statutory assessment/payment cycle). |
| Practical availability | Low-medium — a real signal with a genuinely open API model in UPYOG-adopting states, but ULB fragmentation and absence from the AA framework blocks systematic nationwide access today. |
| Cost / integration complexity | Medium-high (per-state/per-ULB rollout maturity varies significantly). |
| Fraud / authenticity indicators | Registered-premises existence/ownership vs claimed GST/bank business address (a strong premises-authenticity cross-check where obtainable); tax arrears as a distress flag. |
| Credit / risk indicators | Assessed property category/value as a coarse premises-scale proxy; payment regularity. |
| Manipulation resistance | High where obtained — third-party municipal assessment record, not self-reported. |
| Limitations | Coverage is patchy and rollout-stage-dependent; no single national API yet; requires an address-matching layer since it isn't PAN/GSTIN-indexed. |
| Confidence | High. |

### Licensing & compliance

#### 3.8 FSSAI licence / registration

| Field | Value |
|---|---|
| Description | Food Safety and Standards Authority of India licence/registration for any business handling food — basic registration, state licence, or central licence tier based on turnover/scale. |
| Owner / generator | FSSAI, state food-safety departments (FoSCoS portal). |
| Electronic availability | Yes — FoSCoS has a public licence-verification search by licence number/name. |
| Access model | Public — FoSCoS public search API/portal lookup. |
| Update frequency | Irregular (issued/renewed annually or multi-year; status changes on suspension/cancellation). |
| Practical availability | High for food-sector MSMEs — free, public, simple existence+validity check. |
| Cost / integration complexity | Low. |
| Fraud / authenticity indicators | Licence existence/validity/tier mismatch vs claimed turnover-scale; expired/cancelled licence. |
| Credit / risk indicators | Licence tier as a coarse turnover-band signal (basic <₹12L, state ₹12L-20Cr, central >₹20Cr annual turnover), sector formality. |
| Manipulation resistance | Medium-high — third-party issued, but tier is self-selected at application (turnover self-declared to FSSAI too). |
| Limitations | Sector-narrow (food businesses only); a compliance/existence check, not an ongoing activity signal. |
| Confidence | High. |

#### 3.9 Factory licence (State Factories Act)

| Field | Value |
|---|---|
| Description | Mandatory licence under the Factories Act 1948 for manufacturing premises using power above worker-count thresholds — safety/working-condition compliance plus a real physical-premises + headcount attestation. |
| Owner / generator | State Chief Inspector of Factories / Labour Department (state-specific). |
| Electronic availability | Partial — several states have e-licensing portals (Maharashtra's Aaple Sarkar, Tamil Nadu's single-window) with online applications and certificate-verification search; no national unified database or API. |
| Access model | Public search where a state portal exists; state-fragmented, no consent-based national API. |
| Update frequency | Annual renewal. |
| Practical availability | Medium — valuable where available (manufacturing MSMEs) but state-fragmented and inconsistent. |
| Cost / integration complexity | Medium-high (state-by-state integration effort). |
| Fraud / authenticity indicators | Licensed worker count vs claimed EPFO headcount cross-check; licence validity vs claimed operational status. |
| Credit / risk indicators | Sanctioned horsepower/power-load (rough capacity proxy), licensed worker count (scale band). |
| Manipulation resistance | Medium — statutory but only periodically inspected; sanctioned-load figures can lag actual usage. |
| Limitations | Manufacturing-sector-only, state-fragmented digitization, no single API. |
| Confidence | Medium. |

#### 3.10 Pollution Control Board consent (CTE/CTO)

| Field | Value |
|---|---|
| Description | Mandatory environmental "Consent to Establish" and "Consent to Operate" from the State Pollution Control Board for manufacturing/processing units above a pollution-category threshold. |
| Owner / generator | State Pollution Control Boards, under the CPCB umbrella (several states run single-window online consent systems). |
| Electronic availability | Partial — many SPCBs have moved consent issuance online with a certificate/status lookup; not a unified national API. |
| Access model | Public search where digitized; state-fragmented, no consent-based lender API. |
| Update frequency | Renewal cycle (typically every 1-5 years by category); status changes on closure/violation notice. |
| Practical availability | Medium — a strong authenticity signal for manufacturing MSMEs where digitized, but state-inconsistent. |
| Cost / integration complexity | Medium-high. |
| Fraud / authenticity indicators | Valid CTE/CTO vs claimed operational manufacturing activity; closure/violation-notice status. |
| Credit / risk indicators | Pollution category (Red/Orange/Green/White) as a coarse scale-and-sector-risk proxy; consent capacity limits approximate a production ceiling. |
| Manipulation resistance | Medium-high — third-party regulatory record, though "White category" micro units are legitimately exempt (absence isn't itself a red flag for genuinely small units). |
| Limitations | Only meaningful for manufacturing/processing MSMEs above the pollution-category threshold; state-fragmented access. |
| Confidence | Medium. |

#### 3.11 Shops & Establishment registration

| Field | Value |
|---|---|
| Description | State-level Shops & Establishments Act registration — mandatory baseline registration for almost any commercial premises (shop, office, service establishment). |
| Owner / generator | State Labour Department; increasingly folded into single-window MSME/business registration portals. |
| Electronic availability | Yes in most states — online registration, and in many states certificate download/verification. |
| Access model | Public verification where the state portal supports it; otherwise self-share of the certificate; no unified national API. |
| Update frequency | Irregular (registration + renewal cycle, varies by state — some now one-time with no renewal). |
| Practical availability | High as a near-universal baseline existence check; medium as an ongoing signal (state-fragmented, low information beyond "premises is registered"). |
| Cost / integration complexity | Low-medium. |
| Fraud / authenticity indicators | Registered address vs claimed GST/bank address match; existence of a genuine commercial premises. |
| Credit / risk indicators | Minimal beyond a formality/existence flag; registration vintage is a weak tenure proxy. |
| Manipulation resistance | Medium — cheap and easy to obtain, so it corroborates existence more than legitimacy of scale. |
| Limitations | Low information density, state-fragmented, largely a box-ticking exercise. |
| Confidence | Medium. |

### Commerce & payments

#### 3.12 GeM (Government e-Marketplace) — GeM Sahay

| Field | Value |
|---|---|
| Description | An MSME seller's transaction/order history on the Government e-Marketplace, accessed via the GeM Sahay OCEN-based invoice-financing app against confirmed government purchase orders. |
| Owner / generator | GeM (Ministry of Commerce); GeM Sahay platform (OCEN-based). |
| Electronic availability | Yes for the GeM Sahay flow specifically — real and operationally live. |
| Access model | MoU/empanelment-based — lenders sign an MoU to join as a GeM Sahay lending partner; not an open/public API. Data flowing is a confirmed Purchase Order plus a consent-based AA bank-statement pull, not bulk historical order data.[^gem] |
| Update frequency | Real-time/event-triggered at PO acceptance; AA data pulled on-demand per consent. |
| Practical availability | Medium — genuinely operational and growing fast (~35,485 loans in Q1-2026 vs ~5,641 in Q1-2025), but a closed lender panel via MoU. **IDBI Bank is itself already a listed GeM Sahay lending partner** — directly citable for the pitch. |
| Cost / integration complexity | Medium (a proven, well-trodden MoU/empanelment path). |
| Fraud / authenticity indicators | Confirmed-PO existence — a government counterparty verifying the transaction is real — is a strong authenticity signal, hard to fabricate. |
| Credit / risk indicators | Order value/frequency (B2G revenue diversification), repayment behaviour on prior GeM Sahay advances. |
| Manipulation resistance | High — the PO is confirmed by an actual government buyer entity, not self-reported by the seller. |
| Limitations | Relevant only to MSMEs selling to government buyers via GeM; MoU-gated, not general-purpose; loan-specific (invoice financing against a PO) rather than a broad transaction-history feed. |
| Confidence | High. |

#### 3.13 POS / QR acceptance (bank/PG-issued settlement data)

| Field | Value |
|---|---|
| Description | Card/QR-code acceptance infrastructure issued by an acquiring bank or payment aggregator — settlement data (batch amounts, transaction counts) sits with the acquirer/PG. |
| Owner / generator | Acquiring bank / payment aggregator (Pine Labs, Razorpay, PayU, bank acquiring divisions). |
| Electronic availability | Yes, but proprietary to the acquirer. |
| Access model | Licensed/commercial — requires the lender to be the same bank as the acquirer (a common, IDBI-relevant "acquiring + lending" bundle) or a data-sharing partnership with the PG; otherwise merchant self-share of settlement statements. |
| Update frequency | Daily settlement cycle. |
| Practical availability | Medium — high if the lending bank is also the merchant's acquiring bank; low if the acquirer is a third-party PG with no data-sharing agreement. |
| Cost / integration complexity | Low if same-bank acquiring; high if a fresh PG partnership is needed. |
| Fraud / authenticity indicators | Settlement velocity/regularity as an operating-business proxy; chargeback/refund-rate spikes. |
| Credit / risk indicators | Daily/weekly settlement trend, average ticket size, day-of-week seasonality. |
| Manipulation resistance | High — settlement data comes from the acquirer/bank ledger, not merchant self-report. |
| Limitations | Not treated as an independent core source — the richest, most detailed member of the UPI/digital-payments family; retained as its own row for catalog completeness, folded conceptually with §2.3 rather than double-counted. |
| Confidence | High. |

#### 3.14 E-commerce marketplace seller dashboards (Amazon/Flipkart/Meesho)

| Field | Value |
|---|---|
| Description | Seller-level sales/order transaction history from major e-commerce marketplaces, shared with lending partners under a platform-brokered arrangement — not just self-declared CSV export. |
| Owner / generator | Amazon (Seller Lending Network), Flipkart (Growth Capital → Flipkart Finance NBFC), Meesho (Instant Cash). |
| Electronic availability | Yes (Amazon, Flipkart) / partial (Meesho). |
| Access model | Licensed/partnership-based — Amazon: seller-consented API push to lender "Lender Central" portal; Flipkart: consent-based service-account integration, now shifting toward in-house NBFC direct lending (RBI licence, June 2025); Meesho: named lending partners exist but the data-transfer mechanism is undocumented/opaque.[^ecommerce] |
| Update frequency | Near real-time/continuous while a loan is active; no fixed published cadence. |
| Practical availability | High (Amazon/Flipkart) — a genuine platform-to-lender data pipe already used by named banks/NBFCs (historically BoB, Yes Bank, Aditya Birla Finance, SBI, Axis, Tata Capital, SIDBI, Lendingkart, Indifi); medium (Meesho — partners named but access mechanism less transparent). |
| Cost / integration complexity | Medium-high (requires becoming an approved lending partner on the specific marketplace's program). |
| Fraud / authenticity indicators | Platform-verified sales-order and payout history is much harder to fake than a seller-exported CSV; listing-suspension/policy-violation flags. |
| Credit / risk indicators | GMV trend, return/refund rate, customer-rating trend, payout regularity/velocity, category concentration. |
| Manipulation resistance | High — comes from the marketplace's own transaction/settlement systems, not seller self-report. |
| Limitations | Applicable only to the marketplace-selling subset of MSMEs; both Amazon and Flipkart are increasingly moving toward direct in-house NBFC lending rather than remaining open data-sharing partners to third-party banks — a real strategic risk that this channel narrows over time; Meesho's mechanism is opaque. |
| Confidence | High. |

### Risk & legal

#### 3.15 Insurance (policy/claims)

| Field | Value |
|---|---|
| Description | Business/asset/fire/marine/keyman insurance policy holding and claims history for the MSME. |
| Owner / generator | General/life insurers, IRDAI (regulator), Insurance Information Bureau (claims-data pooling). |
| Electronic availability | Partial — policy issuance is electronic, and IIB maintains a claims-data repository, but no open lender-facing API exists for a specific MSME's policy/claims history. |
| Access model | Consent-based (self-share of policy schedule/claims letter) or licensed (insurer-lender data-sharing agreement, common in bancassurance groups). |
| Update frequency | Irregular (policy issuance/renewal annually; claims as they occur). |
| Practical availability | Medium — strong where the lender has a bancassurance/insurance-arm relationship, weak/self-share-only otherwise. |
| Cost / integration complexity | Medium. |
| Fraud / authenticity indicators | Insured asset value vs claimed asset base (a business claiming large fixed assets but carrying token fire cover is a red flag); claims-frequency/fraud-flag history. |
| Credit / risk indicators | Insured asset value (fixed-asset scale proxy), cover lapses correlating with distress, keyman-insurance existence for promoter-dependency risk. |
| Manipulation resistance | Medium-high — third-party issued and priced against declared asset values, though the initial declared sum-insured is still self-reported at underwriting. |
| Limitations | No open API; meaningful mainly where lender and insurer share a group relationship; many MSMEs are under-insured, capping coverage. |
| Confidence | Medium. |

#### 3.16 Court records (e-Courts / NJDG)

| Field | Value |
|---|---|
| Description | Pending/disposed litigation involving the business or its promoters — civil suits, cheque-bounce (Sec 138 NI Act) cases, commercial disputes — via the National Judicial Data Grid and eCourts portals. |
| Owner / generator | e-Committee, Supreme Court of India / District & High Court registries. |
| Electronic availability | Yes. |
| Access model | Public — eCourts/NJDG case-status search is free by party name/case number/CNR; an eCourts API exists for approved integrations (some legal-tech products already built on it). |
| Update frequency | Near real-time to weekly (case-status updates as filed by the registry). |
| Practical availability | High for basic party-name search; medium for reliable entity resolution (name-matching is noisy without a stronger identifier like PAN, which court records don't carry). |
| Cost / integration complexity | Low-medium (search is free; a reliable name-disambiguation layer is the real cost). |
| Fraud / authenticity indicators | Cheque-bounce case volume against the promoter/entity (a strong direct fraud/distress signal); pending criminal cases. |
| Credit / risk indicators | Pending litigation count/type/age, promoter-as-defendant-vs-plaintiff pattern, commercial-dispute frequency. |
| Manipulation resistance | High — independently maintained judicial record, cannot be altered by the party. |
| Limitations | Name-based matching without a PAN/unique-ID anchor is noisy; coverage/digitization completeness varies by state/court tier; a case existing doesn't establish guilt. |
| Confidence | High. |

#### 3.17 Insolvency / IBC (NCLT / IBBI)

| Field | Value |
|---|---|
| Description | Insolvency proceedings (CIRP), liquidation status, and disqualified-director data under the Insolvency & Bankruptcy Code. |
| Owner / generator | IBBI (Insolvency and Bankruptcy Board of India), NCLT. |
| Electronic availability | Yes. |
| Access model | Public — IBBI publishes public CIRP/liquidation data; NCLT has an e-filing/case-status portal; MCA's disqualified-director list is also public. |
| Update frequency | Irregular (as proceedings are filed/updated); IBBI quarterly registers. |
| Practical availability | High as a binary "has this entity or its directors been through IBC proceedings" check, especially combined with MCA21 director data. |
| Cost / integration complexity | Low. |
| Fraud / authenticity indicators | Promoter linked to a prior insolvent/liquidated entity (a strong "serial defaulter" flag); director disqualification status. |
| Credit / risk indicators | None for a healthy MSME — mostly a negative-screening/rejection-list signal rather than a positive predictor. |
| Manipulation resistance | High — court/regulator-maintained, cannot be self-altered. |
| Limitations | A rare-event, tail-risk screen — most MSMEs show nothing here (not itself informative); works best keyed on promoter PAN/DIN, requiring MCA21 linkage. |
| Confidence | High. |

#### 3.18 Government procurement / tenders (CPPP)

| Field | Value |
|---|---|
| Description | Government tender participation, awards, and (where published) contract-performance record via the Central Public Procurement Portal and state e-procurement portals. |
| Owner / generator | Ministry of Commerce/DGS&D → CPPP (`eprocure.gov.in`), plus state e-procurement portals. |
| Electronic availability | Yes. |
| Access model | Public — CPPP tender/award data is openly published and searchable by bidder/awardee; no bulk API for third parties, but the search-and-list interface is public. |
| Update frequency | Irregular/per-tender. |
| Practical availability | Medium — meaningful only for the subset of MSMEs that participate in government procurement, but a strong, hard-to-fake signal where it exists. |
| Cost / integration complexity | Medium (scraping/structuring effort, no clean API). |
| Fraud / authenticity indicators | Debarment/blacklist status (a strong red flag); fake past-performance claims cross-checked against actual awarded tenders. |
| Credit / risk indicators | Value/frequency of government contracts won (B2G revenue diversification/credibility), EMD/performance-guarantee history. |
| Manipulation resistance | High where present — government-published award data can't be fabricated by the bidder (though absence of tender history is uninformative, since most MSMEs never bid). |
| Limitations | Applicable to a minority of MSMEs; no unified national API, per-portal scraping needed; overlaps conceptually with GeM. |
| Confidence | Medium. |

---

## 4. Reject (8 sources)

Rejected sources are not silent omissions — each carries a documented reason.

#### 4.1 ESIC contributions

| Field | Value |
|---|---|
| Description | Monthly employer contribution filings for ESI (health/disability insurance) for establishments above the applicability threshold. |
| Owner / generator | ESIC (Ministry of Labour & Employment). |
| Electronic availability | Partial — the ESIC Employer Search portal exists but is a manual, CAPTCHA-gated lookup of identity fields only (state/district/employer code/name); no contribution amounts or headcount exposed.[^esic] |
| Access model | Unavailable to third parties — no public API, no AA/consent integration; only path is borrower self-share of challan PDFs. |
| Update frequency | Monthly (filed), but not externally exposed at that cadence. |
| Practical availability | Low. |
| Cost / integration complexity | High (no integration path exists). |
| Fraud / authenticity indicators | Establishment-name match vs claimed business identity (weak). |
| Credit / risk indicators | None reliably extractable today. |
| Manipulation resistance | Low (self-shared documents are cherry-pickable). |
| Limitations | Much weaker access path than EPFO; substantially redundant with EPFO's workforce signal where both apply. |
| Confidence | High. |
| **Why rejected** | No API/consent path exists, and where obtainable at all (self-shared challans) it duplicates EPFO's workforce signal at a materially worse access cost. |

#### 4.2 Customs Bill-of-Entry data

| Field | Value |
|---|---|
| Description | Import declaration data (Bill of Entry) filed at customs — HS code, value, quantity, importer IEC. |
| Owner / generator | CBIC, via ICEGATE. |
| Electronic availability | Partial — importer sees their own BoE via ICEGATE login; commercial trade-data resellers (Zauba, Seair, Volza) scrape/license aggregated data at HS-code/count level. |
| Access model | Scraped/licensed (third-party trade-intelligence vendors) or self-share (importer's own portal PDF). |
| Update frequency | Irregular/per-shipment; access lag is high. |
| Practical availability | Low. |
| Cost / integration complexity | High (vendor licensing or manual document collection). |
| Fraud / authenticity indicators | Under/over-invoicing patterns (if cross-checked against GST/bank), IEC-GSTIN mismatch. |
| Credit / risk indicators | Import volume/value trend, sourcing diversification, sector/commodity risk. |
| Manipulation resistance | Medium. |
| Limitations | Narrow applicability (importers only); no clean API. |
| Confidence | Medium. |
| **Why rejected** | Narrow sector applicability, no practical lender-facing API today, and material overlap with the DGFT/ICEGATE + GST signals already retained at lower integration cost. |

#### 4.3 Water utility billing

| Field | Value |
|---|---|
| Description | Municipal/water-board billing and consumption for commercial premises. |
| Owner / generator | State/municipal water boards (hundreds of separate, fragmented utilities). |
| Electronic availability | Partial — most have bill-view/pay portals, some on BBPS, few expose structured consumption-history APIs. |
| Access model | Public bill-lookup at best; effectively scraped/manual where it exists. |
| Update frequency | Monthly/bimonthly billing cycle. |
| Practical availability | Low. |
| Cost / integration complexity | High (per-utility integration). |
| Fraud / authenticity indicators | Premises-occupancy proxy — but weak, since many commercial premises use borewell/private water. |
| Credit / risk indicators | Minimal — consumption correlates poorly with business turnover across sectors. |
| Manipulation resistance | Medium. |
| Limitations | Fragmented, low signal-to-noise, no realistic path to a scalable API. |
| Confidence | Medium. |
| **Why rejected** | Fragmented across thousands of municipal utilities with no standard API, and consumption correlates weakly with business scale/activity compared to electricity. |

#### 4.4 Commercial LPG connection/consumption

| Field | Value |
|---|---|
| Description | Commercial LPG cylinder/connection records (food-service, hospitality, small manufacturing) — connection status, consumption volume/frequency. |
| Owner / generator | Oil marketing companies (IOCL/BPCL/HPCL) via commercial-LPG distributor networks. |
| Electronic availability | Partial-to-no — OMC distributor records are internal only; no public bill-lookup portal exists (unlike electricity or property tax). |
| Access model | Unavailable to third parties in structured form; effectively self-share of physical bills only. |
| Update frequency | Irregular (per-refill, no continuous feed accessible). |
| Practical availability | Low. |
| Cost / integration complexity | High (no integration path exists; would need a direct OMC data-sharing agreement). |
| Fraud / authenticity indicators | Connection-name/address vs claimed business address (weak, self-shared). |
| Credit / risk indicators | Refill frequency as a rough throughput proxy in food/hospitality/small manufacturing. |
| Manipulation resistance | Low — self-shared bill copies are easy to cherry-pick or omit. |
| Limitations | Sector-narrow, no electronic access path at all. |
| Confidence | Medium. |
| **Why rejected** | No electronic access path exists — not even a bill-lookup portal comparable to electricity or property tax — leaving only easily-gamed self-shared documents. |

#### 4.5 Commercial lease / rent registration

| Field | Value |
|---|---|
| Description | Registered lease/rent agreement for commercial premises, registered with the Sub-Registrar (or e-registered in some states). |
| Owner / generator | State registration/stamp-duty departments. |
| Electronic availability | Partial — several states (Maharashtra IGR, Karnataka Kaveri, Delhi) have e-registration and public search-by-property/party portals, but most short-tenure MSME leases (11-month leave-and-licence) are deliberately kept unregistered to avoid stamp duty. |
| Access model | Public search where registered; no consent-based API; state-fragmented. |
| Update frequency | Irregular (at execution/renewal only). |
| Practical availability | Low. |
| Cost / integration complexity | High (state-by-state integration, low completeness). |
| Fraud / authenticity indicators | Premises-existence/business-address corroboration where a registered lease exists. |
| Credit / risk indicators | Lease tenure/rent level as a loose stability/affordability proxy. |
| Manipulation resistance | Medium-high where a genuine registered document exists, but coverage gap defeats it. |
| Limitations | Coverage bias — the smallest/most informal MSMEs (the credit-invisible target segment) are least likely to have a registered lease at all. |
| Confidence | Medium. |
| **Why rejected** | State-fragmented with no lender API, and the MSME segment PS3 targets is exactly the segment least likely to hold a registered (rather than informal) lease. |

#### 4.6 Telecom (mobile/broadband tenure & usage)

| Field | Value |
|---|---|
| Description | Mobile-number tenure, recharge/usage regularity, SIM-verification data as an alt-data proxy for business continuity and identity assurance. |
| Owner / generator | Telecom operators (Jio, Airtel, Vi), TRAI (regulator). |
| Electronic availability | Partial — TRAI's Mobile Number Revocation List (monthly) and the newer Mobile Number Validation platform give fraud/KYC verification only (RBI-mandated for bank onboarding by Jan 2026, NBFC by Feb-Mar 2026); telecom-as-FIP under the RBI AA/DEPA framework remains an unresolved TRAI proposal, contested by DoT.[^telecom] |
| Access model | Regulated API for fraud/KYC-grade checks only (MNRL/MNV, via Digitap/Signzy/Surepass); real tenure/usage-based credit data stays locked inside telcos' own closed-loop lending arms (Jio Financial Services, Airtel's own NBFC licence Feb 2026) — not available to third-party lenders. |
| Update frequency | MNRL monthly; MNV near real-time (fraud checks only). |
| Practical availability | Low. |
| Cost / integration complexity | Medium for MNRL/MNV (cheap, becoming RBI-mandated for KYC); effectively impossible for the richer usage-based credit signal. |
| Fraud / authenticity indicators | MNRL/MNV genuinely useful here — flags revoked/reassigned/suspicious numbers at onboarding (SIM-swap/mule-account prevention). |
| Credit / risk indicators | Essentially none accessible to a third-party lender today. |
| Manipulation resistance | N/A for the accessible part (a KYC control, not a gameable score); the credit-relevant part is simply inaccessible. |
| Limitations | The single largest gap between "hackathon pitch appeal" and 2026 access reality on this whole list. |
| Confidence | High. |
| **Why rejected** | No accessible tenure/usage-based credit signal exists for third-party lenders — it stays inside telcos' closed-loop lending arms; only fraud/KYC-grade number-validation is externally available, which is a KYC control, not a credit/alt-data signal. |

#### 4.7 ONDC seller/network data

| Field | Value |
|---|---|
| Description | Seller/order transaction data on the Open Network for Digital Commerce (Beckn-protocol-based open commerce network). |
| Owner / generator | ONDC (network protocol); individual Seller/Buyer/Logistics Network Participants who hold the actual transaction data. |
| Electronic availability | Partial — ONDC is a discovery/routing/protocol layer, not itself a seller-order-history export API. |
| Access model | Pilot/consent-via-other-rails — only ~9 network participants and 3 lenders (Aditya Birla Finance, DMI Finance, Karnataka Bank) live since Jan 2024 pilots; a larger pipeline is named (HDFC, IDFC First, Kotak, Tata Capital) with no confirmed go-live/scale.[^ondc] |
| Update frequency | Near real-time for the loan workflow itself (~6-minute disbursal claimed in pilots), not a periodic seller-data feed. |
| Practical availability | Low. |
| Cost / integration complexity | High (ONDC network participation + a new lender partnership, still maturing). |
| Fraud / authenticity indicators | None yet productized at scale — a genuine seller-order trail would be a strong authenticity signal in principle. |
| Credit / risk indicators | None yet productized for general third-party access. |
| Manipulation resistance | Potentially high once mature (network-witnessed transactions), but not yet assessable. |
| Limitations | A genuine "watch this space" source, not a usable 2026 signal. |
| Confidence | High. |
| **Why rejected** | Pilot-stage only (9 network participants, 3 lenders, no disclosed scale) with no standalone seller-data API yet — revisit as the network matures, but it doesn't clear the "realistically obtainable today" bar. |

#### 4.8 Satellite / geospatial imagery

| Field | Value |
|---|---|
| Description | Satellite/aerial/drone imagery of a business's physical premises (roof area, yard activity, construction progress) as a remote-sensing activity proxy. |
| Owner / generator | Commercial satellite-imagery providers (Planet Labs, Maxar), ISRO's Bhuvan (public, lower-resolution). |
| Electronic availability | Yes in principle (imagery is purchasable/API-accessible), but no working MSME-specific "activity score" pipeline exists as an off-the-shelf product in the India MSME-lending market. |
| Access model | Licensed (per-km²/per-tasking commercial pricing) plus a custom computer-vision build. |
| Update frequency | Days-to-weeks revisit cadence for commercial satellites. |
| Practical availability | Low — resolution is generally insufficient to distinguish a small MSME unit's activity in a dense urban/industrial-estate setting. |
| Cost / integration complexity | High. |
| Fraud / authenticity indicators | Gross premises-existence check (does a structure exist at the claimed address) — the one thing it's genuinely good for. |
| Credit / risk indicators | Very coarse (rooftop/plot size as an asset-scale proxy) — weak for most MSME sectors. |
| Manipulation resistance | High (imagery can't be faked by the borrower) but low information density for typical MSME plot sizes. |
| Limitations | Resolution/cost mismatch for small urban MSME premises; no existing India MSME-lending product built on it; best reserved for large-asset sectors (warehousing, agri-processing, mining). |
| Confidence | Medium. |
| **Why rejected** | For the typical small-to-medium urban/industrial-estate MSME this catalog targets, satellite resolution and cost make it impractical relative to the premises signals already retained (property tax + electricity + GST address) at far lower cost. |

---

## 5. Composite-indicator catalog

Single sources are inputs; these fused signals are the product — and the direct answer to the orientation session's "harder to manipulate than any single source" bar. For each, the "what a fraudster must simultaneously compromise" column is the crux of the argument.

| # | Composite indicator | Constituent sources | Fused signal | Why it resists manipulation (what must be compromised simultaneously) |
|---|---|---|---|---|
| 1 | **Turnover-Authenticity Score** *(flagship — the pre-existing signature cross-check from `solution-design.md`)* | GSTR-1 (declared outward supply) + GSTR-3B (self-assessed tax) + AA bank statement (settled inflows) + E-way bill (goods actually moved) | A single "declared vs delivered vs collected" turnover reconciliation — flags inflated-turnover fraud (loan-stacking), invoice-only/no-movement fraud, and under-banked cash-heavy operations. | Requires falsifying GSTN's own return, forging/generating matching e-way bills for goods that never moved (GSTN cross-validates 3B against e-way-bill counts systemically), **and** getting a regulated bank (an independent FIP) to show matching settled inflows — three independently-governed systems with no shared point of failure. |
| 2 | **Energy Intensity** | Electricity (DISCOM billing) + GST (declared turnover) | Turnover-per-kWh ratio by sector — a manufacturer claiming high turnover with negligible power consumption is a red flag (shell/inflated-turnover); high consumption with low declared turnover suggests GST under-reporting. | Requires gaming both a self-filed GST return **and** a metered electricity bill (physically alter consumption or collude with the DISCOM) at once; sector-normalized ratios expose an inconsistency even if only one side is faked. |
| 3 | **Estimated Production Capacity** | Electricity (sanctioned load/consumption) + EPFO (headcount/wage-bill) + Factory licence (sanctioned worker-count/power-load) | An independently cross-checked estimate of a manufacturing unit's real production scale/capacity — three separately regulated bodies each attesting to a piece of "how big is this factory really." | Sanctioned load (state electricity board), headcount (EPFO/labour dept), and factory licence (state factories inspectorate) are filed with three different regulators for three different reasons — collapsing all three consistently in a false direction is far harder than gaming one self-reported "annual turnover" figure. |
| 4 | **Logistics-Activity Index** | E-way bill (dispatch volume/frequency) + Vahan (vehicle registration/fleet) + FASTag (toll-crossing pattern, where a partnership exists) | An independent read on whether goods are actually moving at the volume/frequency implied by GST turnover — especially valuable for trading/distribution MSMEs. | Generating fake e-way bills for goods that never moved would require matching vehicle-registration numbers that are actually valid, actively-insured, right-class vehicles (Vahan), and — where FASTag is integrated — matching toll-crossing timestamps on the claimed route: three independently-witnessed physical/documentary layers. |
| 5 | **Premises Authenticity** | Property tax (municipal assessment/address) + Electricity (DISCOM billing address) + GST-registered principal place of business | Does a real, occupied commercial premises exist at the claimed address — corroborated by three independent civic/regulatory records rather than one self-declared address. | Renting a real address for a photo-op GST-registration inspection (a known fraud pattern) is easy; requiring the same address to also show up in an independently-billed, independently-metered electricity account and a separately-assessed municipal tax record raises the bar from "one fake lease" to "three consistent, separately-administered paper trails." |
| 6 | **Business Continuity** | AA bank-account activity continuity + UPI inflow continuity + GST filing-regularity streak | Has this business been continuously and actively operating (not dormant, not a shell freshly activated before a loan application) across the observation window. | Sustaining fabricated activity across a live bank account, a genuine UPI inflow pattern, **and** a multi-month GST filing streak simultaneously is a materially larger and more expensive fraud operation than padding a single channel just before an application. *Telecom tenure/usage was evaluated as a fourth constituent but is Reject-tier (§4.6) — no accessible third-party credit signal exists yet. Flagged as a natural future addition once/if telecom becomes a live AA FIP; until then this composite runs on banking + UPI + GST alone.* |
| 7 | **Operational Stability** | Utility bill-payment regularity (electricity, no disconnection/default) + EPFO contribution regularity (no arrears, stable headcount) | Is the business meeting its two hardest-to-defer recurring obligations — keep the lights on, pay statutory payroll dues — both of which a genuinely distressed business typically lets slip *before* a loan default becomes visible on a bureau report. | EPFO arrears carry a statutory first-charge and personal-liability exposure for directors, and utility disconnection is a hard, public, physically-enforced consequence — both are costly and visible to fake or hide simultaneously, unlike a self-reported "we're doing fine" narrative. |
| 8 | **Supply-Chain Consistency** | DGFT/ICEGATE trade data (self-share/AD-bank) + GST (turnover/ITC pattern) + E-way bill (inbound/outbound goods movement) | For a trading/export-oriented MSME: do the claimed import/export flows, the GST input-tax-credit pattern, and the physical goods-movement trail all tell the same story about what the business actually buys, makes, and sells. | A fraudulent circular-trading or over-invoicing scheme (a classic GST-ITC-fraud pattern) requires fabricating consistent entries across customs declarations, GSTN's own return, **and** e-way bills for movements that would need to physically correspond — three cross-referenced statutory trails, not one. |
| 9 | **B2G Credibility** | GeM/GeM Sahay (confirmed POs) + CPPP (tender participation/award/blacklist status) | A government-counterparty-verified revenue stream plus a debarment/blacklist screen — the buyer-side confirmation makes this one of the hardest revenue claims to fabricate. | A PO or awarded tender is issued and countersigned by an actual government buyer entity in a system the seller doesn't control — fabricating a fake government contract carries its own separate legal exposure, unlike inflating an invoice to a private (possibly related) counterparty. *Directly deployable, not hypothetical: IDBI Bank is already a live GeM Sahay lending partner.* |
| 10 | **Export Orientation** | DGFT/ICEGATE (IEC status/shipping-bill history) + GST (zero-rated/LUT exports, IGST pattern) | Cross-checks a claimed export-revenue share against the GST return's own export markers (zero-rated supply under LUT, IGST refunds claimed) — catches "paper exporters" claiming export incentives without matching GST-side evidence. | GST's own export-declaration fields are already cross-validated by GSTN against ICEGATE shipping-bill data at the system level for refund processing — independently faking both sides simultaneously is a well-monitored fraud vector, not a new gap this composite introduces. |
| 11 | **Legal-Risk Overlay** | e-Courts/NJDG (cheque-bounce/commercial-dispute records) + IBC/insolvency (IBBI/NCLT), both resolved to the individual via **MCA21 director (DIN/PAN) linkage** | A promoter-level (not just entity-level) negative screen — surfaces serial-defaulter patterns hidden behind a freshly incorporated entity. | Incorporating a brand-new company to escape an entity-level credit history is a known evasion pattern; keying the check on the promoter's PAN/DIN via MCA21's director linkage — rather than the applicant entity's name — closes that loophole, since court and IBBI records are independently maintained and cannot be scrubbed by starting a new company. |
| 12 | **Formal-Identity Integrity** *(bonus)* | Udyam (URN) + PAN/GSTIN verification (active status) + MCA21 (director/company master data) + GST registration | A single-glance check that every identity credential the applicant presents resolves to the same, real, active legal entity — name, PAN, GSTIN, Udyam URN, and (for companies) CIN/director all mutually consistent. | Each identifier is independently issued/validated by a different authority (MSME ministry, Protean/NSDL, GSTN, MCA); synthetic-identity fraud requires forging consistent cross-references across four separately-governed registries at once, not just one fake certificate. |
| 13 | **Credit-Exposure Cross-Check** *(bonus)* | Credit Bureau (declared obligations/EMI schedule) + AA bank statement (recurring NACH/EMI-pattern debits) | Catches undisclosed borrowing — recurring debits in the bank statement that don't match any bureau-reported obligation (informal-lender debt, or a very recent loan not yet reflected at the bureau). | Hiding a loan from the bureau is easy (it simply never gets reported), but the EMI still has to be physically paid from a real, AA-visible bank account every month — the repayment *behaviour* is much harder to hide than the loan's registration. |

---

## 6. Summary

Of 34 candidates evaluated against the `idbi-hackathon` SKILL's 12-field rubric, **8 are retained as core**, **18 as enrichment**, and **8 are rejected** with a documented reason each. Eight tier assignments diverge from the seed list's first-pass guesses, all driven by 2026 access-reality research: MCA21, DISCOM electricity, and DGFT/ICEGATE move from Core to Enrichment (real but access-constrained); ONDC moves from Core straight to Reject (pilot-stage, not production); and commercial LPG, telecom, and ESIC move from Enrichment to Reject (no viable third-party access model exists today for any of the three). The clearest single finding is that **telecom alt-data — probably the most-pitched "additional source" in this space — has no accessible credit signal for a third-party lender in 2026**; its tenure/usage data lives entirely inside telcos' own closed-loop NBFC lending arms, with only KYC-grade number-validation (MNRL/MNV) externally reachable. Conversely, the most underrated finding is that **IDBI Bank is already a live lending partner on GeM Sahay** — meaning the B2G-Credibility composite (§5, #9) is not a hackathon hypothetical but an extension of an integration IDBI already has.

The 13 composite indicators are the real deliverable of this appendix: each one is built so that faking it requires simultaneously compromising multiple independently-governed systems (a tax authority, a regulated bank, a state utility, a court registry) rather than shading a single self-reported number. That is the concrete, defensible answer to the orientation session's challenge — not a longer list of sources, but a fusion layer that turns "we also looked at FASTag" into "here is why FASTag plus e-way bill plus Vahan is harder to fake than any one of them alone."

---

## 7. Citations (web-verified sources)

[^mca21]: MCA21 master-data portal — `https://www.mca.gov.in/content/mca/global/en/mca/master-data/MDS.html` (public company/director master data); Probe42 API product page — `https://probe42.in/products/api.html` (commercial reseller, not an official MCA lender API).
[^itraa]: Sahamati live FI-types registry — `https://sahamati.org.in/data-fi-types-available-on-aa/` (confirms no CBDT/ITR FI-type is live on AA as of 2026).
[^ewb]: GSTN E-Way Bill API Developer Portal — `https://docs.ewaybillgst.gov.in/apidocs/`; GSP-model explainer — `https://gsthero.com/gst-suvidha-provider-gsp/`.
[^fastag]: Setu FASTag payments documentation — `https://docs.setu.co/payments/fastag`; D91 Labs FASTag-credit proposal (noted as unimplemented, aggregator/lender API gap confirmed).
[^dgft]: API Setu IEC Verification API directory — `https://directory.apisetu.gov.in/api-collection/iec`; TaxGuru commentary on ICEGATE CSP terms barring financial-product-selling use of its data.
[^discom]: RDSS smart-meter rollout dashboard (NSGM) — `https://nsgm.gov.in/en/sm-stats-all`; Sahamati FIP-mapping — `https://sahamati.org.in/fip-aa-mapping/` (confirms no utility FI-type on AA); Setu BBPS documentation — `https://docs.setu.co/payments/bbps`.
[^ptax]: UPYOG/DIGIT platform documentation — `https://upyog-docs.gitbook.io` (MoHUA property-tax module, live in 12+ states).
[^telecom]: Digitap MNRL/MNV mandate explainer — `https://blog.digitap.ai` (RBI-mandated bank/NBFC onboarding timelines); Storyboard18 reporting on the TRAI-DoT telecom-as-AA-FIP impasse.
[^ondc]: Business Standard reporting on ONDC's 9-LSP/3-lender live cohort since Jan 2024; ONDC financial-services resource page — `https://resources.ondc.org/financial-services`.
[^gem]: Tribune India reporting on GeM Sahay 2.0/OCEN launch and lender onboarding; IDBI Bank's own GeM Sahay product page — `https://www.idbibank.in/gem-sahay.aspx`.
[^ecommerce]: Amazon seller-financing announcement — `https://sellingpartners.aboutamazon.com/amazon-steps-up-financing-to-fuel-seller-growth`; Business Today reporting on Flipkart's June 2025 RBI NBFC licence and Flipkart Finance transition.
[^esic]: ESIC Employer Search portal — `https://portal.esic.gov.in/EmployerSearch` (identity-fields-only lookup, no contribution/headcount data exposed).
