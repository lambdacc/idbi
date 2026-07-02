---
name: msme-credit-scorecard
description: Build ML credit scorecards and financial health scores for MSME/SME lending at banks and NBFCs — NTB (new-to-bank) application scorecards, ETB (existing-to-book) behavioral scorecards, and alternate-data financial health cards. Use this skill whenever the user mentions MSME/SME credit scoring, financial health scores or health cards, NTB/ETB models, application or behavioral scorecards, default/PD prediction, early-warning signals, GST/bank-statement/bureau-based underwriting, alternate-data or composite cross-source indicators, turnover-authenticity or manipulation-resistance checks, or any ML model that ranks borrowers by credit risk — even if they just say "score these companies" or "predict which loans go bad".
---

# MSME Credit Scorecard

Purpose: build defensible, calibrated scorecards that rank MSME borrowers by probability of default (PD) or financial-health deterioration. Regulator-facing (RBI model risk expectations), so interpretability and documentation are requirements, not preferences.

## How to read this skill

Two registers. **[REPO]** = rules for building/modifying scoring code in this repo (CreditPulse — IDBI Innovate 2026 hackathon entry, all data SYNTHETIC with generator ground-truth labels; no real book, no real defaults, no incumbent policy, no reject population). **[PROD]** = doctrine for stage-2 (IDBI mock data, post-21-Jul sandbox) and any real-data refit/pilot — it is the roadmap the pitch must be able to defend, never instructions to execute against this repo's synthetic cohort. When a [PROD] rule cannot literally apply today, an inline note says what replaces it.

## This repo (CreditPulse) — current reality [REPO]

One NTB-analog application score from alternate data. Two coexisting scoring paths, wired in `app/ml/engine.py`:

1. **Deterministic backbone**: `app/ml/models/pillars.py` — features → 0–100 components (percentile rank in a frozen training reference, oriented by `app/config/feature_config.yaml` directions) → 5 pillar scores → weighted composite → 1–10 grade → onboarding band → recommendation + indicative limit (`app/config/scoring_config.yaml`). Monotonic in every feature by construction.
2. **ML PD path**: `app/ml/models/scorecard.py` (WoE/IV logistic, hand-rolled binner in `app/ml/models/woe.py`) + `app/ml/models/gbm.py` (LightGBM with hard monotone constraints from feature directions); blended PD → risk category. Optional 300–900 analogue (PDO 20) — first on the cut-list, never the primary output.

Semantics: the composite/grade is **cohort-calibrated** (z-mapped so grades spread 1–10) — it means "standing relative to this cohort", not an absolute PD. The PD path carries the probability semantics. Never present the grade as a PD; never let the two paths silently disagree without the card showing both.

Around them:
- **Cross-source composite layer** (`app/ml/features/composite_features.py`): 13 indicators fusing 25 sources — pure functions of already-computed per-source features, each paired with a manipulation-resistance rationale surfaced in reason codes. Catalog + rejection reasoning: `docs/appendix-a-data-source-catalog.md` §5–6.
- **Turnover-Authenticity Score** (`app/ml/features/turnover_authenticity.py`): the flagship differentiator, protected scope — never cut or dilute. Reconciles declared GST turnover against settled bank inflows and e-way-bill goods movement. Turnover-vs-turnover ONLY (ITR income deliberately excluded — profitability ≠ authenticity). Tolerance-banded, clipped. No GST footprint → neutral 60, flagged by confidence, never penalised.
- **Confidence score** (`app/ml/models/confidence_score.py`): data-completeness = 0.6·(IV-weighted source presence) + 0.4·(coverage breadth). First-class output; never folded into a pillar. Thin file ⇒ hedged score, not auto-reject.
- **Peer segmentation** (`app/ml/models/clustering.py`): K-Means in pillar space, DESCRIPTIVE ONLY — never in the credit decision. Do not confuse with risk segmentation.
- **Explainability** (`app/ml/explainability/`): reason codes from deterministic components (sign-consistent by construction), native point-contributions for the scorecard, SHAP for the GBM, Jaccard stability-across-refits test.
- **Eval harness** (`app/ml/eval/`, `make eval`): AUC/Gini/KS per model + composite-as-score + TA fraud discrimination + PSI train-vs-holdout.

## Non-negotiables in this repo [REPO]

1. **Every feature declares its health direction and rationale in `feature_config.yaml` before use.** That config is the single source of truth for pillar orientation, GBM monotone constraints, and reason-code phrasing. A feature without a direction is unconstrained and unexplained — don't ship it.
2. **Monotonicity is enforced and tested**: the model must never improve a score as a risk factor worsens. It lives in the pillar construction and the GBM constraints, not in the WoE binner. Preserve the tests.
3. **Holdout discipline** (`app/ml/eval/holdout.py`): split once, up front, stratified, fixed seed, and the 6 named demo archetypes pinned to TRAIN so demo entities never inflate reported test metrics. Do not "improve" the eval by re-splitting after feature work or letting archetypes into test.
4. **Leakage here means generator leakage**: labels (`label_default`, `label_fraud`) and generator latents must never feed features or composites. IV > 0.5 still triggers a check — but on synthetic data, high IV may be honest generator signal, not leakage; verify against the generator spec (`docs/appendix-b-synthetic-data-plan.md` §2) before deleting.
5. **Reason codes on every score** — implemented; keep it that way. No reason codes → no deployment. Composite reason codes must carry their manipulation-resistance rationale ("what must be simultaneously compromised").
6. **Synthetic honesty posture**: never claim real-default validation. Every metrics statement — code, docs, pitch — carries the caveat the eval runner already prints: metrics are on synthetic data calibrated to the generator; real-default backtesting + recalibration is the productionization step. Turn the ceiling into a credibility signal, don't hide it.
7. **Manipulation resistance is a feature-design axis.** When adding a signal, prefer a cross-source consistency check over another single-source ratio; state which independently-governed systems must be jointly compromised to fake it (the Appendix A §5 pattern).
8. **Do NOT do here**: reject inference (no reject population exists), OOT splits (single-vintage cohort, no time axis), swap-set vs incumbent (no incumbent), ETB behavioral features (no internal book). These are [PROD] items; attempting them against synthetic data fabricates rigor.
9. Stack is pinned (`requirements.txt`): pandas, scikit-learn, lightgbm, shap, no optbinning — the hand-rolled `woe.py` is deliberate (transparent, dependency-light, demo-deterministic). Don't add optbinning here. Persistence is the whole-engine pickle with cohort-staleness check (`engine.py`); keep binning inside the persisted artifact.

## Production doctrine [PROD] — stage-2 mock data onward; mandatory for any real-data refit

1. **NTB and ETB are two separate models. Never blend.** NTB (application): only data knowable at application — bureau, GST, financials/ITR, other-bank statements, alternate data, entity data. ETB (behavioral): adds internal account behavior (the most predictive block a bank has); rebuild monthly. Different label windows, feature sets, cut-offs. CreditPulse today is NTB-analog; an ETB variant starts from scratch on real internal data.
2. **Label definition is written before any modeling.** Standard: 90+ DPD (or SMA-2/NPA/restructured) within a 12-month performance window from observation point. For financial-health deterioration: define explicitly (slippage to SMA-1+, >2 notch downgrade, 30%+ turnover decline). Exclude indeterminates (1–89 DPD at window end) from training; score them anyway. Replaces the synthetic ground-truth labels — the first real-data task.
3. **Never optimize accuracy.** Defaults are 2–8% of book. Gini/KS, PR-AUC, bad-capture@approval-rate. Report swap-set vs incumbent policy once an incumbent exists.
4. **Leakage rule**: a feature is legal only if knowable at the observation/decision date. Watch: post-sanction utilization in NTB, restructuring flags, collection-activity fields, enquiries triggered by this application.
5. **Reject inference for NTB on a real book.** Approved-only training data is biased. Minimum: document the bias; better: parceling/fuzzy augmentation using bureau performance of declines at other lenders. State the method in the model card.
6. **Split: out-of-time always.** Train on cohorts to T, validate after T. For ETB, stack month-end snapshots with 12-month forward windows; dedupe or cluster SEs by borrower. Random splits overstate Gini badly on stacked cohorts.
7. **Calibrate to PD** (isotonic on OOT) — scores feed pricing, ECL staging (Ind AS 109), capacity. Re-anchor the cohort-calibrated composite/grade to observed PD bands at this point; until then it is explicitly relative.
8. **Scorecard hygiene**: coarse-class 5–10 bins, enforce monotonic WoE where economically required, IV filter 0.02–0.5 (>0.5 → leakage check), 10–20 variables with VIF check, at least one variable per information block (bureau, GST, banking, alternate/composite) for single-source-failure robustness, publish the attribute→bin→points table. `optbinning` is the right tool at this stage. Challenger GBM with SHAP reason codes only if model-risk policy allows.
9. **Segmentation**: separate scorecards by ticket/secured/sector only with ≥~1,500 bads per segment; below that, one model + segment variables (the only legal option at this repo's scale).
10. **Monitoring**: Gini/KS on OOT per segment; calibration by score band (band inversion fails review regardless of Gini); PSI on score and top features monthly (>0.25 investigate — the repo's `eval/psi.py` thresholds carry over); vintage curves by band; override tracking. Health-score grades keep a fixed PD range and a prescribed action per grade — a score without an action mapping changes nothing (the repo's grade→band→recommendation chain is the template).
11. **Governance artifacts (the deliverable)**: model development doc (label def, reject-inference method, windows, segment design, variable dictionary with IV, scorecard table), calibration/validation report, reason-code dictionary mapped to adverse-action language, monitoring pack spec, and a **fair-lending note** — no prohibited attributes, check proxies (pincode, gender-correlated features; several alternate-data sources are geography-rich, so this is live here, not theoretical). Hackathon analogue today: the `docs/` set + the eval runner's printed honesty gate.

## Feature landscape (Indian MSME)

Single sources are inputs; **fused cross-source signals are the product** — harder to fake than any one source. Full rubric-scored catalog (34 evaluated, 8 core + 18 enrichment + 8 rejected with reasons) and the 13-composite catalog: `docs/appendix-a-data-source-catalog.md`. Highlights:

- **Bureau** (strongest classic NTB block): CMR, delinquency count/recency, enquiry velocity, live exposure, promoter's consumer score (proprietor and firm finances are entangled).
- **GST** (goldmine): filing regularity, turnover trend/seasonality, credit-note intensity, concentration, ITC ratios; GST-vs-bank divergence is the signature red flag. GSTN-stable feature backlog: `docs/cag-gst-feature-analysis.md` (also lists obsolete indicators GSTN now auto-enforces — exclude them).
- **Bank/UPI via AA**: balance trend/volatility, bounce counts, EMI-to-inflow, low-balance frequency, continuity.
- **Widened alternate data**: e-way bill (goods actually moved), electricity (metered consumption vs claimed scale), EPFO (headcount + arrears = strongest distress marker), courts/IBC promoter-level negative screens via MCA21 DIN linkage, GeM/CPPP (government-countersigned revenue — IDBI is a live GeM Sahay partner), FASTag/Vahan, DGFT/ICEGATE, property tax, licences. Know the rejects too (telecom, ONDC, ESIC — no accessible third-party signal in 2026): defending the exclusions is part of the pitch.
- **ETB internal behavior** [PROD only]: utilization level/trend, cheque returns, drawing-power breaches, RBI EWS triggers — strongest block overall once a book exists.

Peer-normalize where sensible (within industry × ticket band); weight unaudited financial ratios low for micro — behavioral, GST, and composite evidence beat statements there.
