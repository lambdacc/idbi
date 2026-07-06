"""Track-04 monitoring orchestrator — the backend that turns the EWSEngine's raw
arrays into the copy, actions and staged narrative the two pages render.

Module boundaries (multi-track D6): the **frontend renders only**, the **ml layer
computes only**, and *every* user-facing string a Track-04 page shows is composed
HERE. Pages import `run_monitoring()` / `case_detail()`, read the typed result and
lay it out — they never format a narrative sentence or an action label themselves.

"Agentic monitoring" (D5) = a deterministic, disclosed sequence of specialist
stages (re-score → band → detect migration → prioritise → recommend), reusing the
platform `Stage` dataclass. There is NO runtime LLM; the technique cards say so.

Read-only platform imports: `app.backend.services.pipeline_orchestrator.Stage`
(reused dataclass + technique-tone pattern) and `app.data_gen.build_dataset`
(the shared cohort master, for borrower names/sectors — a core data artefact, not
a cross-track import). The EWS engine is this track's own ml layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from app.backend.services.pipeline_orchestrator import Stage
from app.data_gen.build_dataset import DATA_DIR as _CORE_DATA_DIR

from .ml.features import FEATURE_LABELS
from .ml.model import EWSEngine

# The flagship deteriorating borrower the Watchlist opens on — its alt-data rolls
# over ~7 months before "today" while every EMI is still paid, and the
# repayment-only baseline never fires (the money shot).
SHOWCASE_ENTITY = "AUTO_COMPONENTS"


# --------------------------------------------------------------------------- #
# RBI-EWS action vocabulary (plain language). One recommended action + tone per
# band; the officer-facing idiom mirrors the RBI early-warning-signal red-flag
# playbook (review limits, site visit, GST/bank refresh, routine review).
# --------------------------------------------------------------------------- #
ACTIONS: Dict[str, Dict[str, str]] = {
    "Red": {
        "action": "Review limit · site visit · open restructuring dialogue",
        "tone": "risk",
        "gist": "Act now — treat as an incipient-stress account.",
    },
    "Amber": {
        "action": "Enhanced monitoring · request fresh GST & bank statements",
        "tone": "warn",
        "gist": "Watch closely and refresh the evidence before the next cycle.",
    },
    "Green": {
        "action": "Routine annual review",
        "tone": "good",
        "gist": "No action beyond the normal review calendar.",
    },
}

# feature key -> plain-language risk phrase (the driver moving the WRONG way). The
# engine hands back sign-aware risk drivers; these turn each into one clause a
# credit officer reads without a data-science glossary.
_REASON_PHRASE: Dict[str, str] = {
    "gst_turnover_slope_6m": "declared GST turnover is trending down",
    "gst_missed_filings_6m": "GST returns filed late or skipped",
    "inflow_slope_6m": "bank inflows are shrinking",
    "inflow_vs_gst_gap": "bank credits are lagging behind declared GST sales",
    "upi_count_slope_6m": "UPI payment activity is falling",
    "epfo_headcount_delta_6m": "payroll headcount is shrinking",
    "energy_slope_6m": "metered energy use is falling",
    "utilization_now": "the sanctioned limit is heavily drawn",
    "utilization_slope_6m": "the sanctioned limit is being drawn down faster",
    "dpd_current": "currently past due on an EMI",
    "dpd_max_3m": "a recent EMI delinquency",
    "bounce_cnt_6m": "recent EMI bounces",
    "months_on_book": "a thin repayment track record",
}

# Technique disclosure surfaced on the case drilldown (D5/D7). `plain`+`benefit`
# always shown; `algorithm` is Technical-view only (it carries banned jargon).
TECHNIQUE: Dict[str, str] = {
    "plain": "Monthly alt-data re-scoring vs a repayment-only baseline",
    "algorithm": "Monotonic gradient-boosted trees over repayment + alt-data deltas, "
                 "probability-calibrated; banded on calibrated PD (Red ≥ 0.30, "
                 "Amber ≥ 0.10). Baseline = the same pipeline on repayment "
                 "features only at a 3-month horizon. Deterministic staged "
                 "orchestration — no runtime LLM.",
    "benefit": "Re-reads the borrower's whole digital footprint every month and "
               "flags deterioration in GST, bank inflows and payroll months before "
               "any EMI bounces — where a repayment-only view is still blind.",
}

_HONESTY = ("All figures are computed on a synthetic loan book that encodes the "
            "thesis by construction; on-screen numbers demonstrate the mechanism, "
            "not a real-world accuracy claim. Retuning on real defaults is the "
            "pilot step.")


# --------------------------------------------------------------------------- #
# Small formatting helpers (kept local so the backend never imports frontend).
# --------------------------------------------------------------------------- #
def _fmt_pd(p: float) -> str:
    """Display cap for the 12-month default risk. The calibrated tail saturates
    at 1.0 on the synthetic book; printing a literal 100% (or 0%) reads as a bug
    to a credit audience, so the display clamps to an honest open interval."""
    p = float(p or 0.0)
    if p < 0.01:
        return "<1%"
    if p > 0.95:
        return ">95%"
    return f"{p:.0%}"


def _fmt_inr(x: float) -> str:
    x = float(x or 0.0)
    if x >= 1e7:
        return f"₹{x / 1e7:.2f} Cr"
    if x >= 1e5:
        return f"₹{x / 1e5:.1f} L"
    return f"₹{x:,.0f}"


def _month_label(m: Optional[int]) -> str:
    """Panel months are indexed relative to 'today' (0). Render them the way an
    officer reads a calendar."""
    if m is None:
        return "—"
    if m < 0:
        return f"month {m} ({-m} mo ago)"
    if m == 0:
        return "this month"
    return f"month +{m} (~{m} mo ahead)"


def _reason_phrases(reasons: List[dict], top_k: int = 3) -> List[str]:
    out: List[str] = []
    for r in reasons[:top_k]:
        phrase = _REASON_PHRASE.get(r["feature"])
        if phrase is None:
            phrase = FEATURE_LABELS.get(r["feature"], r["feature"]).replace("_", " ")
        out.append(phrase[0].upper() + phrase[1:])
    return out


# --------------------------------------------------------------------------- #
# Cohort master (names/sectors) — a core data artefact, read once and cached.
# --------------------------------------------------------------------------- #
_MASTER: Optional[pd.DataFrame] = None


def _master() -> pd.DataFrame:
    global _MASTER
    if _MASTER is None:
        p = _CORE_DATA_DIR / "msme_master.csv"
        try:
            _MASTER = pd.read_csv(p).set_index("entity_id")
        except Exception:
            _MASTER = pd.DataFrame()
    return _MASTER


def _name(entity_id: str) -> str:
    m = _master()
    if entity_id in m.index and "name" in m.columns:
        return str(m.loc[entity_id, "name"])
    return entity_id.replace("_", " ").title()


def _sector(entity_id: str) -> str:
    m = _master()
    if entity_id in m.index and "sector" in m.columns:
        return str(m.loc[entity_id, "sector"])
    return "—"


# --------------------------------------------------------------------------- #
# Typed results.
# --------------------------------------------------------------------------- #
@dataclass
class WatchRow:
    entity_id: str
    name: str
    sector: str
    product: str
    band: str
    tone: str                       # ui tone: good/warn/risk
    pd_12m: float
    pd_pct: str
    exposure: float
    exposure_str: str
    dpd_current: float
    baseline_band: str
    reasons: List[str]              # plain-language, top-3
    action: str                     # recommended RBI-EWS action for the band
    rationale: str                  # one-line "why flagged" from the top driver
    prior_band: Optional[str] = None
    is_new: bool = False            # escalated INTO this band vs prior month


@dataclass
class Kpi:
    label: str
    value: str
    sub: str = ""
    kind: str = ""                  # ui tone class
    tip: str = ""


@dataclass
class MonitoringRun:
    as_of_month: int
    n_loans: int
    exposure_total: float
    band_counts: Dict[str, int]
    red_count: int
    amber_count: int
    green_count: int
    red_share: float
    amber_share: float
    exposure_at_risk: float
    median_lead_ews: float
    median_lead_baseline: float
    lead_gap: float
    capture_ews: float
    capture_baseline: float
    alert_precision: float
    alert_recall: float
    false_alert_rate: float
    holdout_auc_ews: float
    watchlist: List[WatchRow]
    kpis: List[Kpi]
    migration: Dict[str, int]
    stages: List[Stage]
    honesty_caption: str = _HONESTY
    exposure_caption: str = ("Exposure figures are illustrative planning estimates "
                             "off the synthetic sanctioned limits — not booked balances.")

    def row(self, entity_id: str) -> Optional[WatchRow]:
        return next((r for r in self.watchlist if r.entity_id == entity_id), None)


@dataclass
class CaseDetail:
    entity_id: str
    name: str
    sector: str
    product: str
    band: str
    tone: str
    pd_pct: str
    exposure_str: str
    dpd_current: float
    is_defaulter: bool
    timeline: Dict[str, object]     # raw entity_timeline dict (chart data)
    ews_first_alert: Optional[int]
    baseline_first_alert: Optional[int]
    default_month: Optional[int]
    lead_time: Optional[int]        # months of EWS warning before (projected) default
    reasons: List[str]
    action: str
    action_gist: str
    headline: str
    verdict: str                    # the narrative paragraph (computed values)
    technique_plain: str
    technique_benefit: str
    technique_algorithm: str
    marker_note: str                # plain caption explaining the three markers


# --------------------------------------------------------------------------- #
# Migration (band vs prior month) — read the engine's own scored panel if it is
# available; degrade gracefully to "no prior month" so a cold call never raises.
# --------------------------------------------------------------------------- #
def _band_migration(engine: EWSEngine, snapshot: Dict[str, object]
                    ) -> tuple[Dict[str, int], Dict[str, Optional[str]]]:
    _SEV = {"Green": 0, "Amber": 1, "Red": 2}
    prior: Dict[str, Optional[str]] = {}
    snaps = getattr(engine, "_snaps", None)
    latest = int(snapshot["as_of_month"])
    if snaps is not None and len(snaps):
        prev = snaps[snaps["as_of"] == latest - 1]
        prior = {r.entity_id: r.ews_band for r in prev.itertuples()}
    counts = {"new_red": 0, "new_amber": 0, "worsened": 0, "improved": 0, "movers": 0}
    for r in snapshot["rows"]:
        cur = r["band"]
        pb = prior.get(r["entity_id"])
        if pb is None:
            continue
        if _SEV[cur] > _SEV[pb]:
            counts["worsened"] += 1
            counts["movers"] += 1
            if cur == "Red":
                counts["new_red"] += 1
            elif cur == "Amber":
                counts["new_amber"] += 1
        elif _SEV[cur] < _SEV[pb]:
            counts["improved"] += 1
            counts["movers"] += 1
    return counts, prior


# --------------------------------------------------------------------------- #
# Staged monitoring narrative (the "agentic" reveal; disclosed, deterministic).
# --------------------------------------------------------------------------- #
def _stages(run_kpis: Dict[str, object]) -> List[Stage]:
    n = run_kpis["n_loans"]
    red, amber = run_kpis["red"], run_kpis["amber"]
    lead, base = run_kpis["lead_ews"], run_kpis["lead_base"]
    return [
        Stage(1, "rescore", "Monthly re-score",
              "Every live loan re-scored on its latest footprint.", 0.0,
              headline=f"Re-scored {n} live loans on this month's alt-data + repayment panel.",
              technique={"plain": TECHNIQUE["plain"], "algorithm": TECHNIQUE["algorithm"],
                         "benefit": TECHNIQUE["benefit"]}),
        Stage(2, "band", "Band assignment",
              "Calibrated PD mapped to Green / Amber / Red.", 0.0,
              headline=f"{red} loans land in Red and {amber} in Amber on the calibrated-PD bands."),
        Stage(3, "migration", "Migration check",
              "This month's bands compared with last month's.", 0.0,
              headline="Accounts that escalated a band since last month are surfaced as movers."),
        Stage(4, "prioritise", "Prioritisation",
              "Watchlist ranked by band, then PD, then exposure.", 0.0,
              headline="Red before Amber, higher PD and larger exposure first."),
        Stage(5, "recommend", "Recommended action",
              "Each account paired with its RBI-EWS action.", 0.0,
              headline=f"Median early warning: {lead:.0f} months vs {base:.0f} for the "
                       "repayment-only baseline."),
    ]


# --------------------------------------------------------------------------- #
# Public API.
# --------------------------------------------------------------------------- #
def run_monitoring(engine: EWSEngine) -> MonitoringRun:
    """Compose the full portfolio monitoring result (KPIs + ranked watchlist +
    migration + staged narrative) — the single object both pages read."""
    snap = engine.portfolio_snapshot()
    ev = snap.get("eval", {}) or {}

    bands = snap["band_counts"]
    red_c, amber_c, green_c = bands.get("Red", 0), bands.get("Amber", 0), bands.get("Green", 0)

    migration, prior = _band_migration(engine, snap)

    # Rank: Red before Amber, then higher PD, then larger exposure.
    _rank = {"Red": 0, "Amber": 1, "Green": 2}
    flagged = [r for r in snap["rows"]
               if r["band"] in ("Red", "Amber") and r["status"] != "closed"]
    flagged.sort(key=lambda r: (_rank[r["band"]], -r["pd_12m"], -r["exposure"]))

    watchlist: List[WatchRow] = []
    exposure_at_risk = 0.0
    for r in flagged:
        eid = r["entity_id"]
        band = r["band"]
        meta = ACTIONS[band]
        phrases = _reason_phrases(r["reasons"])
        rationale = (f"Flagged because {phrases[0].lower()}" if phrases
                     else "Flagged on its overall deterioration profile") + "."
        exposure_at_risk += r["exposure"]
        pb = prior.get(eid)
        watchlist.append(WatchRow(
            entity_id=eid, name=_name(eid), sector=_sector(eid), product=r["product"],
            band=band, tone=meta["tone"], pd_12m=r["pd_12m"], pd_pct=_fmt_pd(r["pd_12m"]),
            exposure=r["exposure"], exposure_str=_fmt_inr(r["exposure"]),
            dpd_current=r["dpd_current"], baseline_band=r["baseline_band"],
            reasons=phrases, action=meta["action"], rationale=rationale,
            prior_band=pb,
            is_new=bool(pb is not None and _rank[band] < _rank[pb]),  # more severe now
        ))

    lead_ews = float(ev.get("median_lead_ews") or 0.0)
    lead_base = float(ev.get("median_lead_baseline") or 0.0)
    lead_gap = float(ev.get("median_lead_gap") or 0.0)
    cap_ews = float(ev.get("capture_decile_ews") or 0.0)
    cap_base = float(ev.get("capture_decile_baseline") or 0.0)

    kpis = [
        Kpi("Loans monitored", f"{snap['n_loans']:,}",
            "live accounts re-scored this month", "",
            "Every open loan on the synthetic book, re-scored on its latest footprint."),
        Kpi("Red — act now", f"{red_c}",
            f"{snap['red_share']:.0%} of the book", "risk" if red_c else "good",
            "Calibrated default risk in the highest band — treat as incipient stress."),
        Kpi("Amber — watch", f"{amber_c}",
            f"{snap['amber_share']:.0%} of the book", "warn" if amber_c else "good",
            "Elevated risk — enhanced monitoring and an evidence refresh."),
        Kpi("Exposure monitored", _fmt_inr(snap["exposure_total"]),
            "illustrative planning estimate", "",
            "Sum of synthetic sanctioned limits under monitoring — not booked balances."),
        Kpi("Exposure at risk", _fmt_inr(exposure_at_risk),
            "Red + Amber · illustrative planning estimate",
            "risk" if red_c else "warn",
            "Illustrative exposure carried by the flagged (Red + Amber) accounts."),
        Kpi("Early-warning lead", f"{lead_ews:.0f} mo",
            f"vs {lead_base:.0f} mo for the repayment-only baseline",
            "good",
            "Median months of warning before default — how far ahead the alt-data "
            "model turns Red versus a repayment-only view."),
    ]

    stages = _stages({"n_loans": snap["n_loans"], "red": red_c, "amber": amber_c,
                      "lead_ews": lead_ews, "lead_base": lead_base})

    return MonitoringRun(
        as_of_month=int(snap["as_of_month"]),
        n_loans=int(snap["n_loans"]),
        exposure_total=float(snap["exposure_total"]),
        band_counts=bands, red_count=red_c, amber_count=amber_c, green_count=green_c,
        red_share=float(snap["red_share"]), amber_share=float(snap["amber_share"]),
        exposure_at_risk=exposure_at_risk,
        median_lead_ews=lead_ews, median_lead_baseline=lead_base, lead_gap=lead_gap,
        capture_ews=cap_ews, capture_baseline=cap_base,
        alert_precision=float(ev.get("alert_precision_red") or 0.0),
        alert_recall=float(ev.get("alert_recall_red") or 0.0),
        false_alert_rate=float(ev.get("false_alert_rate") or 0.0),
        holdout_auc_ews=float(ev.get("holdout_auc_ews") or 0.0),
        watchlist=watchlist, kpis=kpis, migration=migration, stages=stages,
    )


def _pct_change(series: List[float], window: int = 6) -> Optional[float]:
    if not series or len(series) <= window:
        return None
    a, b = float(series[-1 - window]), float(series[-1])
    if a == 0:
        return None
    return (b - a) / abs(a)


def _verdict(name: str, tl: Dict[str, object], lead: Optional[int]) -> tuple[str, str]:
    """Deterministic narrative paragraph (template + computed values). Returns
    (headline, paragraph). Never presents the projected default as observed."""
    ews = tl.get("ews_first_alert")
    base = tl.get("baseline_first_alert")
    dm = tl.get("default_month")
    is_def = bool(tl.get("is_defaulter"))
    epfo = tl.get("epfo_employee_count") or []
    inflows = tl.get("bank_inflows") or []

    inflow_chg = _pct_change([float(x) for x in inflows])
    parts: List[str] = []

    if ews is not None:
        headline = (f"{name} moved to Red in {_month_label(ews)} — "
                    "on the alt-data footprint, not on missed EMIs.")
        parts.append(f"CreditPulse turned {name} Red in {_month_label(ews)}.")
    else:
        headline = f"{name} is under enhanced monitoring on early alt-data drift."
        parts.append(f"{name} is flagged on early alt-data drift.")

    drift_bits: List[str] = []
    if inflow_chg is not None and inflow_chg < 0:
        drift_bits.append(f"bank inflows are down {abs(inflow_chg):.0%} over six months")
    if len(epfo) >= 7:
        a, b = int(epfo[-7]), int(epfo[-1])
        if b < a:
            drift_bits.append(f"payroll shrank from {a} to {b}")
    if drift_bits:
        parts.append("Over the run-up, " + " and ".join(drift_bits)
                     + " while declared GST turnover slipped.")

    dpd = tl.get("dpd") or []
    emis_clean = all((d or 0) == 0 for d in dpd)
    if base is None:
        if emis_clean:
            parts.append("The repayment-only baseline has not flagged it at all — "
                         "every EMI is still being paid on time.")
        else:
            parts.append("The repayment-only baseline never turned Red.")
    else:
        gap = (base - ews) if (ews is not None) else None
        gtxt = f", {gap} months later" if gap else ""
        parts.append(f"The repayment-only baseline only turned Red in "
                     f"{_month_label(base)}{gtxt}.")

    if is_def and dm is not None:
        if dm > 0:
            parts.append(f"On the current trajectory the model projects default around "
                         f"{_month_label(dm)}"
                         + (f" — roughly {lead} months after the first Red flag." if lead else "."))
        else:
            parts.append(f"Default followed in {_month_label(dm)}"
                         + (f", {lead} months after the first Red flag." if lead else "."))

    return headline, " ".join(parts)


def case_detail(engine: EWSEngine, entity_id: str) -> CaseDetail:
    """Compose the per-borrower drilldown: the timeline (chart data), the three
    ordered markers, plain-language drivers, the RBI-EWS action, the narrative
    verdict and the technique disclosure. All copy originates here."""
    tl = engine.entity_timeline(entity_id)

    # Latest banding/reasons for this entity from the portfolio snapshot.
    snap = engine.portfolio_snapshot()
    prow = next((r for r in snap["rows"] if r["entity_id"] == entity_id), None)
    if prow is not None:
        band = prow["band"]
        reasons = _reason_phrases(prow["reasons"])
        pd_pct = _fmt_pd(prow["pd_12m"])
        exposure_str = _fmt_inr(prow["exposure"])
        dpd_current = float(prow["dpd_current"])
        product = prow["product"]
    else:
        # Cold fallback (entity not on the live book): band off its own PD tail.
        pd_tail = tl.get("ews_pd") or [0.0]
        band = engine.band(float(pd_tail[-1]))
        reasons, pd_pct = [], _fmt_pd(float(pd_tail[-1]))
        exposure_str, dpd_current, product = "—", 0.0, "—"

    meta = ACTIONS.get(band, ACTIONS["Green"])
    ews, base, dm = tl.get("ews_first_alert"), tl.get("baseline_first_alert"), tl.get("default_month")
    lead = (dm - ews) if (tl.get("is_defaulter") and dm is not None and ews is not None) else None
    headline, verdict = _verdict(_name(entity_id), tl, lead)

    marker_note = ("Dashed markers, left to right: the alt-data model's first Red "
                   "alert, the repayment-only baseline's first alert (if any), and "
                   "the projected default month. The gap between the first two is the "
                   "warning the alt-data footprint buys you.")

    return CaseDetail(
        entity_id=entity_id, name=_name(entity_id), sector=_sector(entity_id),
        product=product, band=band, tone=meta["tone"], pd_pct=pd_pct,
        exposure_str=exposure_str, dpd_current=dpd_current,
        is_defaulter=bool(tl.get("is_defaulter")), timeline=tl,
        ews_first_alert=ews, baseline_first_alert=base, default_month=dm,
        lead_time=lead, reasons=reasons, action=meta["action"], action_gist=meta["gist"],
        headline=headline, verdict=verdict,
        technique_plain=TECHNIQUE["plain"], technique_benefit=TECHNIQUE["benefit"],
        technique_algorithm=TECHNIQUE["algorithm"], marker_note=marker_note,
    )
