# Appendix B — Synthetic Data Generation Plan & MSME Distribution Profile

**Status:** Phase 1 research + Phase 2 design deliverable · **Date:** 01 Jul 2026 · **Owner:** Lambdac
**Reads with:** [`appendix-a-data-source-catalog.md`](appendix-a-data-source-catalog.md) (the 26 retained sources this appendix generates data for), [`implementation-plan.md`](implementation-plan.md) (consumes this as the `data_gen/` build spec), [`data-and-intel-sourcing-guide.md`](data-and-intel-sourcing-guide.md) (existing synthetic-data notes for GST/AA/UPI/EPFO)

---

## 0. Why this appendix exists

Two things have to be true simultaneously for CreditPulse's synthetic cohort to be credible: (1) the **distributions** it samples from must reflect real India MSME statistics, not made-up round numbers, and (2) **every Retain-tier source from Appendix A** — not just GST/UPI/AA/EPFO — must have a modeled generator, because the brief's "synthetic data only" constraint governs *integration*, not *breadth*. This appendix delivers both: §1 is the sourced/assumed MSME distribution profile that calibrates every generator; §2 specifies the generator for each of the 26 retained sources (8 core in full detail, 18 enrichment in compact table form, both are `data_gen/` build inputs); §3 covers cross-source consistency (why a given synthetic MSME's numbers agree with each other); §4 covers the demo archetypes.

Every figure in §1 is tagged `(sourced: citation)` or `(assumed: reasoning)` per the discipline already established in `intel-cag-gst-feature-analysis.md`. Do not add a new unsourced figure to this document without the same tag.

---

## 1. MSME Distribution Profile for India (sourced/assumed research)

### 1.0 Methodology note

Built from parallel research against official portals (PIB, MSME Ministry, MoSPI/NSS, RBI, GSTN/CBIC, dcmsme.gov.in, dashboard.msme.gov.in) and reputable secondary sources (SIDBI-CRISIL, TransUnion CIBIL MSME Pulse, ICRIER, Omidyar Network/MicroSave, IBEF, IFC/World Bank). Several official portals render via JavaScript or blocked automated fetches, so some figures rely on secondary quotation of a primary source rather than a directly-parsed primary document — flagged per figure. Where sources conflict (common with Udyam's live-counter data), both figures are shown with their date and the discrepancy is explained rather than silently resolved.

### 1.1 Udyam Registration aggregate stats

| Metric | Figure | Tag |
|---|---|---|
| Total Udyam + Udyam Assist Platform (UAP) registrations | **7.83 crore** as of 28 Feb 2026 | (sourced: PIB Press Release PRID 2246892, Ministry of MSME, 28 Feb 2026) |
| Same metric, alternate snapshot | **7.30+ crore** as of 17 Dec 2025 (4.37cr Udyam Portal + 2.92cr UAP) | (sourced: PIB "Year End Review 2025", PRID 2209712) |
| Registration growth trajectory (cumulative, FY-end) | FY21-22: 0.79cr → FY22-23: 1.64cr → FY23-24: 4.12cr → FY24-25: 6.19cr → FY25-26 (till 28 Feb 26): 7.83cr | (sourced: PIB PRID 2246892) |
| Micro share of registrations | **93.98%** (30 Sep 2021 snapshot) | (sourced: Office of the Development Commissioner (MSME), "Bulletin VII", Oct 2021) |
| Small / Medium share (same snapshot) | 5.39% / 0.62-0.65% | (sourced: same Bulletin VII) |
| Micro share, more recent snapshot | **>97%** Micro, ~1.5% Small, ~0.8% Medium | (sourced: Statista, Mar 2024 — paywalled aggregator, primary chain not independently confirmed) |

**Reconciliation:** Micro share rose from ~94% (2021) to ~97%+ (2024), most plausibly explained by the Jan-2023 **Udyam Assist Platform (UAP)** launch, purpose-built to onboard GST-exempt/informal micro units previously outside Udyam entirely (sourced: PIB PRID 2011262). **Calibration range used**: Micro ≈ 95-97%, Small ≈ 3-5%, Medium ≈ 0.6-0.8%.

### 1.2 Sector mix

| Population | Manufacturing | Trade/Retail | Services | Tag |
|---|---|---|---|---|
| Udyam-registered, 27 Feb 2026 | 20.89% | 42.89% | 36.22% | (sourced: IBEF, ibef.org/industry/msme) |
| All unincorporated non-agri enterprises (broader, incl. unregistered) | 31% | 36.3% | 32.6% | (sourced: NSS 73rd Round, NSSO/MoSPI, 2015-16) |

Top sub-sectors by count (2021 rank order, stale but the only NIC-level data found): food products manufacturing, land transport, food & beverage services, other personal services, other manufacturing (sourced: Bulletin VII, Oct 2021). Trade's share grew sharply since 2021 because wholesale/retail trade NIC codes were only added to Udyam mid-2021.

### 1.3 Geography

Top states, consistent across sources (high confidence on ranking, medium on exact %): **Maharashtra (~11%), Uttar Pradesh (~8.9%), Tamil Nadu (~6.7%), West Bengal (~5.9%), Karnataka (~5.6%), Gujarat (~6%), Rajasthan (~5%)** (sourced: PIB "Year End Review 2025" PRID 2209712, cross-checked against Bulletin VII 2021 for ranking stability). Urban/rural split (enterprise count, broader population): **Rural 51.25% / Urban 48.75%** (sourced: NSS 73rd Round, 2015-16) — Udyam-registered-only population plausibly skews more urban (assumed: no direct Udyam urban/rural split exists; formalization correlates with urban proximity to banks/CSCs).

### 1.4 Turnover distribution within Micro (₹0-5cr band)

| Figure | Tag |
|---|---|
| 88% of all Udyam-registered MSMEs have turnover under ₹1 crore | (sourced: "Udyam Registration Publication", Ministry of MSME/DPIIT, June 2022, n=80.16 lakh MSMEs) |
| 97% of all MSMEs have investment under ₹50 lakh | (sourced: same publication) |
| Own-Account Enterprises (no hired worker) = 84.2% of all enterprises; average GVA/OAE = ₹95,753/yr; average GVA/establishment = ₹6,41,104/yr | (sourced: NSS 73rd Round, 2015-16) |
| Gross Value of Output per establishment (turnover proxy) | ₹4,63,389 (2022-23), ₹4,91,862 (2023-24) | (sourced: ASUSE, MoSPI factsheets) |
| No direct turnover-band table exists within Micro | — | **not found** — confirmed absent from Udyam dashboard, MSME Annual Report, GSTN statistics pages, NSS/ASUSE |

**Assumed sub-band split within Micro** (arithmetic decomposition of the sourced 88%-of-all-MSMEs figure against Micro/Small/Medium shares, treating Small/Medium as ≥₹1cr): **<₹10L: ~52%, ₹10L-1cr: ~41%, ₹1-5cr: ~7%** of Micro units. This is the single most assumption-heavy parameter in this document — flagged for sensitivity-testing.

### 1.5 Formalization / digital footprint

GST-registration thresholds (the "credit-invisible" mechanism): **₹40 lakh (goods)**, **₹20 lakh (services)**, **₹20L/₹10L (special-category states)** (sourced: CBIC Notification 10/2019-CT; PIB PRID 1567975) — meaning most Micro units (≥90% per §1.4) are *legally exempt* from GST registration, can be entirely real operating businesses with zero GST footprint. **~35% of Micro units still unregistered on Udyam/Udyam Assist** (sourced: SIDBI, May 2025, n=2,097 firms). Digital adoption: **94% of small merchants accept UPI**, 57% of transaction value via UPI vs 38% cash (sourced: DFS/NPCI, Feb 2026, n=10,378); **71% of MSME owners use smartphone as primary business device** (84% among women-led MSMEs) (sourced: PayNearby MSME Digital Index 2025, n=10,000). Formal credit access: **~14% of MSMEs** (sourced: Deloitte, June 2026 — medium confidence, secondary coverage only).

### 1.6 Age/vintage distribution

No official age-of-enterprise tabulation exists in NSS or ASUSE (verified negative). **>50% of enterprises established after 2010** (sourced: ICRIER, Mar 2025, n=2,365 firms); pre-1990 (35+ years) share: Micro 7%, Small 9%, Medium 12% (sourced: same ICRIER report). **Assumed synthesis**: <3yr ~18%, 3-10yr ~40%, >10yr ~42% (interpolated from the ICRIER anchor, moderated against Omidyar's 25% "≤1yr" figure which applies to the broader informal population, not the formalized/Udyam slice).

### 1.7 Employment size

**84.2% of enterprises are OAE (zero hired workers)** nationally (91.4% rural, 76.6% urban) (sourced: NSS 73rd Round, 2015-16); ASUSE corroborates (~85-86% zero-hired-worker, 2022-23). Derived average employees/unit from Udyam Bulletin VII (Oct 2021): **Micro ≈6.5, Small ≈31.8, Medium ≈149.6** (sourced/computed from official aggregate totals ÷ official unit counts).

### 1.8 Credit gap / lending context

**₹20-25 lakh crore** MSME credit gap — RBI-appointed U.K. Sinha Committee, submitted 18 June 2019 (sourced: dcmsme.gov.in; corroborated by PRS India) — the most authoritative, consistently re-cited figure, reused by Parliament's Standing Committee on Finance (2022). More recent re-estimate: **₹30 lakh crore** gap, ~24% of ₹123 lakh crore total demand unmet (sourced: SIDBI-CRISIL, May 2025) — suggests the gap may have widened, not narrowed. MSME GNPA: **3.6%** as of March 2025, bank-book basis (sourced: RBI Financial Stability Report, June 2025); broader bureau/NBFC-inclusive basis: **8-11%** (sourced: SIDBI-TransUnion CIBIL MSME Pulse, June 2025).

### 1.9 Gender/ownership

**~39% of Udyam/Udyam Assist registrations are women-led** (sourced: Lok Sabha reply, Dec 2025) vs. a stricter "women-owned/majority proprietor" figure of **~20.5%** (sourced: PIB, Nov 2024) — the gap likely reflects a definitional shift (owned vs. led) rather than pure growth; both are reported here since the synthetic-data spec may need either definition.

### 1.10 Synthetic-data calibration summary (direct generator parameters)

```
Category split:        Micro 96% · Small 3.3% · Medium 0.7%
                        (assumed blended midpoints of the sourced 2021/2024 ranges)

Turnover bands (of ALL MSMEs):
  < ₹10L            : 50%   (assumed: 96% Micro × 52% of Micro in this band)
  ₹10L - 1cr        : 39%   (assumed: 96% Micro × 41%)
  ₹1cr - 5cr        : 7%    (assumed: 96% Micro × 7%, Micro's upper tail)
  ₹5cr - 15cr       : 2.0%  (assumed: 3.3% Small × 60%, right-skewed within Small)
  ₹15cr - 30cr      : 1.0%  (assumed: 3.3% Small × 30%)
  ₹30cr - 50cr      : 0.3%  (assumed: 3.3% Small × 10%)
  ₹50cr - 100cr     : 0.39% (assumed: 0.7% Medium × 55%, right-skewed within Medium)
  ₹100cr - 175cr    : 0.21% (assumed: 0.7% Medium × 30%)
  ₹175cr - 250cr    : 0.10% (assumed: 0.7% Medium × 15%)

Sector weights (blend of Udyam-registered + NSS broader population, since CreditPulse's target
spans both formal and credit-invisible informal units):
  Trade/Retail   : 40%   Services : 34%   Manufacturing : 26%

State weights (top 7 + tail):
  Maharashtra 11.0% · UP 8.9% · Tamil Nadu 6.7% · West Bengal 5.9% · Karnataka 5.6% ·
  Gujarat 6.0% · Rajasthan 5.0% · all other states/UTs 50.9%

Urban/rural:            broader population 51.25%/48.75% rural/urban;
                        Udyam-registered-only (assumed) 45%/55%

Age/vintage bands:      <3yr 18% · 3-10yr 40% · >10yr 42%   (assumed, see §1.6)

Employee-count bands (calibrated to match sourced per-unit averages 6.5/31.8/149.6):
  Micro:  0 emp 40% · 1-9 emp 50% · 10-49 emp 8% · 50+ emp 2%
  Small:  0 emp 2%  · 1-9 emp 20% · 10-49 emp 55% · 50+ emp 23%
  Medium: 10-49 emp 10% · 50-99 emp 25% · 100-199 emp 35% · 200+ emp 30%

GST-registration probability by turnover band (assumed, applying sourced thresholds):
  <₹10L 5% · ₹10-20L 12% · ₹20-40L 45% · ₹40L-1cr 88% · ₹1-5cr 97% · ₹5cr+ 99%

Digital-adoption probability by turnover band (assumed, anchored to sourced 94%/71% national figures):
  <₹10L 45% · ₹10L-1cr 75% · ₹1-5cr 90% · ₹5cr+ 96%

Women-owned probability:  39% (broader "led") or 20-25% (stricter "owned") — pick per generator need

Default/NPA-rate anchors: 3.6-4.5% (clean bank-book) or 8-11% (broader bureau/NBFC-inclusive);
                          skew upward for <₹10L / GST-unregistered / no-formal-credit segment
                          (assumed directional skew — informality correlates with risk, not a
                          sourced conditional default rate)

Headline pitch figure:    MSME credit gap ₹20-25 lakh crore (RBI U.K. Sinha Committee, 2019),
                          footnote the ₹30 lakh crore SIDBI-CRISIL 2025 re-estimate
```

---

## 2. Per-source generator specification

### 2.1 Cross-source consistency mechanism (applies to every generator below)

`data_gen/profiles.py` draws each synthetic MSME from a small set of **latent variables** first — true scale (revenue-generating capacity), true health (healthy / stressed / distressed), true honesty (genuine vs. inflated-turnover) — then every per-source generator samples its observable fields *conditioned on* those latents rather than independently. This is what makes the composite indicators in Appendix A §5 demonstrate a real fused signal instead of coincidental agreement: e.g. a MSME with a high "true scale" latent gets correspondingly high electricity consumption, EPFO headcount, and factory-licence sanctioned load — all three, together — while an "inflated-turnover" profile deliberately decouples declared GST turnover from the electricity/EPFO/bank-inflow evidence, so the Turnover-Authenticity and Energy-Intensity composites correctly flag it. Ground-truth labels (health/fraud profile) are stored alongside the generated data for the eval harness.

### 2.2 Core sources (full generator spec)

**GST (GSTR-1/3B)** — Fields: monthly turnover, tax liability, ITC availed, filing date vs. due date, exempted/nil turnover, credit notes, HSN/SAC code. Generation: monthly turnover sampled from §1.10's turnover-band weights with seasonal/trend noise conditioned on the "true scale" latent; filing regularity conditioned on "true health" latent (stressed businesses file late more often). *Accessibility narrative*: GSTN is a live AA FI type today; GST-only features require no consent and are computable pre-AA, matching the low-friction identification angle already established in `data-and-intel-sourcing-guide.md`.

**Account Aggregator — bank/deposit** — Fields: daily balance, transaction narration strings, inflow/outflow categorization, bounce events, OD/CC utilization. Generation: balance trajectory conditioned on "true health"; narration strings synthesized to be parseable (CR/DR, VPA-like strings) matching real AA-shaped narration format. *Accessibility narrative*: bank deposit is a live, schema-defined AA FI type (ReBIT `deposit.xsd`) — the richest, most production-ready rail available.

**UPI (via bank narration + optional PG data)** — Fields: P2M vs P2P split, counterparty concentration, recurring-inflow detection, optional MCC (PG-style only). Generation: derived as a sub-layer of the bank-narration generator above, plus an optional cleaner payment-gateway-style feed for the "richer data" story. *Accessibility narrative*: UPI has no FI type of its own on AA (rides inside bank narration, ~50-char string, no MCC); PG data is real but closed/proprietary — modeled as an optional enrichment feed, not claimed as freely available.

**EPFO (ECR v2)** — Fields: `#~#`-delimited 11-field records, headcount, wage bill, EE 12%/ER 8.33%+3.67% contribution split, ₹15k EPS ceiling, arrears flag. Generation: headcount conditioned on "true scale" and the employee-count bands in §1.10; arrears conditioned on "true health" (arrears are the strongest distress marker per `data-and-intel-sourcing-guide.md` §5). *Accessibility narrative*: **not live on AA** — must stay framed as mocked/roadmap; self-share (UMANG/DigiLocker) or third-party verification APIs are the real production path.

**Credit Bureau (CIBIL/CRIF MSME)** — Fields: existing obligations, EMI schedule, delinquency history, vintage/length of credit history. Generation: conditioned on "true health"; vintage distribution calibrated to TransUnion CIBIL's sourced New-to-Credit share (~47-51% of new originations, §1.8 sourcing). *Accessibility narrative*: real bureau API integration is out of scope for stage-1; mocked in the same shape a bureau pull would return.

**Udyam Registration** — Fields: URN, category (Micro/Small/Medium), NIC sector code, registration date. Generation: sampled directly from §1.10's category/sector/age weights — this is the anchor record every other source's entity resolves against. *Accessibility narrative*: public, near-universal, the natural identity anchor; genuinely free to query in production.

**PAN/GSTIN verification** — Fields: verification status (active/cancelled/suspended), name-match confidence. Generation: near-100% "active" for demo profiles, with a small synthetic fraction "cancelled" to exercise the failure path. *Accessibility narrative*: low-cost, real-time API (Protean/NSDL) — cheap KYC-grade anchor, realistic to integrate.

**E-way bill (NIC EWB)** — Fields: dispatch count/frequency, declared value, HSN, distance/route. Generation: volume conditioned on "true scale" and sector (trading/manufacturing profiles generate materially more e-way bills than services); deliberately decoupled from GST turnover in the "inflated-turnover" fraud profile (goods movement doesn't match declared sales) so the Turnover-Authenticity composite fires correctly. *Accessibility narrative*: confirmed genuinely core — real GSP-mediated API with proven consent-sharing lending products already live (Vayana Network, CredAvenue/Yubi), per Appendix A §2.8.

### 2.3 Enrichment sources (compact generator spec)

| Source | Key synthetic fields | Generation approach | Accessibility narrative (production path) |
|---|---|---|---|
| MCA21 | Director/DIN list, incorporation date, charges/liens | Only generated for the subset of synthetic entities flagged "incorporated" (companies/LLPs, not proprietorships) | Real data, but access is via paid commercial resellers (Probe42/Tofler/Zauba), not an official lender API |
| ITR/AIS/Form 26AS | Reported income, TDS credits | Conditioned on GST turnover with a plausible declared-income ratio; deliberately mismatched in fraud profiles | Not yet a live AA FI type; consent-based self-share is the realistic path |
| FASTag/NHAI toll | Toll-crossing count/frequency, route pattern | Generated only for logistics/trading archetypes, scaled with e-way-bill volume | Real transaction data exists (IHMCL/NETC); no lender-facing aggregator API confirmed yet |
| Vahan/Parivahan | Registered vehicle count, class, age | Scaled with "true scale" for logistics/manufacturing archetypes | Genuinely public API — realistic to integrate as-is |
| DGFT/IEC + ICEGATE | IEC status, shipping-bill count/value | Only generated for export-oriented archetypes | Real data, but ICEGATE's own CSP terms bar use for "financial product selling" — self-share/AD-bank relationship is the realistic route |
| Electricity (DISCOM) | Sanctioned load, monthly consumption (kWh) | Conditioned on the same "true scale" latent as EPFO headcount and factory licence, for the Energy-Intensity and Production-Capacity composites to be meaningful | Real but fragmented across 40+ DISCOMs; no unified API or AA FI type yet — self-share/DISCOM-specific integration is the realistic near-term path |
| Property tax (municipal) | Assessed value, payment-due status, registered address | Address cross-checked against the GST-registered principal place of business; deliberately mismatched in "shell/fake premises" fraud profiles | Real, digitized in 12+ states via the UPYOG/DIGIT platform; coverage varies by city |
| FSSAI licence | Licence number, category, validity | Only generated for F&B/food-processing archetypes | Public licence-search portal exists; low integration cost |
| Factory licence | Sanctioned worker count, sanctioned power load | Only generated for manufacturing archetypes; feeds Production-Capacity composite jointly with electricity + EPFO | State Factories Act registry; access via state labour department, low cost, sector-conditional |
| Pollution Control Board consent | CTE/CTO status, validity | Only for manufacturing archetypes | State PCB portals; public, sector-conditional |
| Shops & Establishment | Registration status, date | Near-universal for all archetypes with a physical premises | Partial digitization by state; near-universal applicability |
| GeM / GeM Sahay | Confirmed PO count/value | Only for archetypes selling to government (subset of manufacturing/services) | Real, and directly deployable — IDBI Bank is already a live GeM Sahay lending partner (Appendix A §3.12) |
| POS/QR acceptance | Settlement volume, acceptance uptime | Modeled as a sub-item of the UPI/PG feed, not a separate generator | Bank/PG-issued settlement data; realistic as an extension of existing AA bank data |
| E-commerce marketplace dashboards | Seller rating, order volume | Only for retail/e-commerce-active archetypes | Real (Amazon/Flipkart seller-financing programs exist) but proprietary/consent-gated |
| Insurance | Policy count, sum insured, claims history | Sparse — only generated for a minority of archetypes (asset-heavy sectors) | Low electronic centralization; realistic only via self-share |
| Court records (e-Courts/NJDG) | Cheque-bounce case count, case status | Near-zero for "healthy" profiles, present for "stressed"/"fraud" profiles as a negative flag | Public, free eCourts/NJDG search; name-matching without PAN anchor is the real-world limitation |
| Insolvency/IBC | CIRP status, liquidation flag | Near-zero incidence, reserved for a small "distressed" synthetic subset | Public IBBI/NCLT data; low coverage/frequency but high signal when present |
| Govt procurement/tenders (CPPP) | Tender participation/award count, blacklist flag | Only for archetypes selling to government, paired with GeM | Public CPPP portal; independent credibility signal alongside GeM |

---

## 3. Cross-source consistency examples (worked)

- **Healthy Textile Manufacturer**: high "true scale" latent → high electricity consumption + high EPFO headcount + factory licence sanctioned load all agree (Production-Capacity composite fires clean) → GST turnover matches bank inflows within tolerance (Turnover-Authenticity clean) → no court/IBC records.
- **Inflated-turnover fraud profile**: GST turnover set high, but electricity/EPFO/bank-inflow latents stay at the entity's *true* (lower) scale → Energy-Intensity and Turnover-Authenticity composites both flag a gap → this is the demo's explicit "here's how the system catches it" moment.
- **Genuinely thin-file but healthy Kirana Store**: no MCA21 record (proprietorship), no bureau history (new-to-credit), but consistent UPI inflows + GST filing regularity + Shops & Establishment registration → data-completeness confidence score is Medium (not High), but the pillar scores are healthy — demonstrating the "lend cautiously on partial data instead of auto-rejecting" narrative from `product-framework-notes`.

## 4. Demo archetypes

Six named archetypes, per `demo-architecture.md`, each pre-assigned a latent profile and a Retain-tier source subset appropriate to its sector (a Restaurant doesn't get DGFT/ICEGATE records; an IT Services company doesn't get a factory licence): **Textile Manufacturer** (manufacturing, high energy/EPFO/factory-licence signal), **Retail Kirana Store** (trade, thin-file, high UPI/digital-adoption), **Restaurant** (services, FSSAI-heavy), **IT Services Company** (services, minimal utility/logistics footprint, bureau-thin), **Auto Components Supplier** (manufacturing, e-way-bill and FASTag-heavy), **Logistics Business** (services, Vahan/FASTag/e-way-bill-heavy). Plus a randomizable generator varying revenue trend, GST compliance, employee stability, UPI adoption, working capital, and existing debt, so the ML system reads as adaptive rather than hardcoded across repeated demo runs.
