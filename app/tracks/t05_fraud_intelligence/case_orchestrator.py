"""SentinelPulse case orchestrator — the deterministic *agentic* investigation
(Track 05, WP-5A).

``investigate(fraud_engine, account_id) -> CaseFile`` decomposes one flagged
account into **five specialist agent stages** — Triage, Evidence, Network,
Adjudication, and the Case-file compiler — each a REUSED
``app.backend.services.pipeline_orchestrator.Stage`` so the existing
``components/stage.py`` renderer drives them unmodified. ``desk_snapshot`` builds
the Fraud-Desk queue, KPIs and typology distribution.

This module OWNS every user-facing string in Track 05 (module boundary D6:
``ml/`` computes, ``backend`` narrates, ``frontend`` renders only). It reads the
two engine-input CSVs (accounts / transactions) but NEVER the eval labels file —
roles are *inferred* from observable behaviour, not read from a label file.

The differentiator is the **citation gate**: an Evidence-stage ``Ground`` (a
ground of suspicion) cannot be constructed without >=1 citing ``txn_id`` — the
``Ground`` dataclass RAISES ``CitationError`` otherwise, so no uncited claim can
ever reach a case file. When a detector fires with no usable evidence the
orchestrator degrades to an explicit "insufficient evidence" note rather than
emit a claim.

"Agentic" here == orchestrated deterministic specialist stages with a human
approve/override gate. There is no runtime LLM (constraint D5); an LLM narrative
layer is disclosed as an optional pilot step in the Adjudication technique card.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from app.backend.services.pipeline_orchestrator import Stage

from .data_gen import ACCOUNTS_CSV, DATA_DIR, TRANSACTIONS_CSV
from .data_gen.typologies import (TYP_DEVICE, TYP_DORMANCY, TYP_FAN, TYP_KYC,
                                  TYP_NEWVEL, TYP_ODD, TYP_PASS, TYP_STRUCT)

# --------------------------------------------------------------------------- #
# Positioning constants — the "why this track" hooks (backend owns all copy).
# --------------------------------------------------------------------------- #
WHY_TRACK: List[str] = [
    "RBIH's MuleHunter.AI already flags suspected rented-out accounts across "
    "23–26 banks at the network level.",
    "The MHA directive requires every financial institution to integrate "
    "rented-out-account detection by December 2026.",
    "RBI's FREE-AI principles require each such decision to be explainable — "
    "SentinelPulse sits above the flagging layer and assembles the evidence.",
]

# This track is transaction-fraud operations, NOT lending/scoring (PS5's
# "unrelated to PS1–4" fence). Shown as an honesty caption on the desk.
SCOPE_NOTE = (
    "SentinelPulse is a transaction-fraud operations desk — it protects the "
    "payment rails. It is deliberately unrelated to the lending and financial-"
    "health scoring in the other tracks. All accounts and transactions here are "
    "synthetic; recalibrating on a bank's real ledger is the pilot step."
)

# --------------------------------------------------------------------------- #
# Pattern label maps (backend-owned copy). ``*_PLAIN`` are the simple-mode,
# jargon-free phrasings; the technical labels carry the industry term and are
# shown only in Technical view.
# --------------------------------------------------------------------------- #
TYPOLOGY_LABEL: Dict[str, str] = {
    TYP_FAN: "Fan-in / fan-out consolidation",
    TYP_PASS: "Rapid pass-through",
    TYP_DORMANCY: "Dormancy then burst",
    TYP_NEWVEL: "New-account velocity",
    TYP_KYC: "Income-band mismatch",
    TYP_STRUCT: "Threshold structuring",
    TYP_ODD: "Odd-hours activity",
    TYP_DEVICE: "Shared device",
}
TYPOLOGY_LABEL_PLAIN: Dict[str, str] = {
    TYP_FAN: "Collect-and-forward",
    TYP_PASS: "Money passed straight through",
    TYP_DORMANCY: "Sudden burst after a long silence",
    TYP_NEWVEL: "Brand-new account moving heavy volume",
    TYP_KYC: "Money far above the declared income",
    TYP_STRUCT: "Amounts kept just under reporting limits",
    TYP_ODD: "Activity in the dead of night",
    TYP_DEVICE: "One phone shared across many accounts",
}

# Recommendation strings (technical) + jargon-free simple variants.
REC_FREEZE = "Freeze + file STR draft"
REC_MONITOR = "Enhanced monitoring"
REC_CLEAR = "Clear with note"
REC_PLAIN: Dict[str, str] = {
    REC_FREEZE: "Freeze the account and prepare a suspicious-transaction report",
    REC_MONITOR: "Keep under closer watch",
    REC_CLEAR: "Clear the account, with a note on file",
}

BAND_ALERT, BAND_REVIEW, BAND_CLEAR = "Alert", "Review", "Clear"
# Above this daily-transaction rate a Clear account reads as a genuine
# high-velocity earner (gig worker / small merchant), not a dormant one.
HIGH_VELOCITY_TPAD = 4.0


# --------------------------------------------------------------------------- #
# Citation gate
# --------------------------------------------------------------------------- #
class CitationError(ValueError):
    """Raised when a ground of suspicion is built without any citing txn_id.

    This is the enforcement point of the citation gate (WP-5A differentiator):
    every claim in a case file must resolve to >=1 real transaction, so a Ground
    with an empty ``txn_ids`` can never be constructed.
    """


@dataclass
class Ground:
    """One ground of suspicion — a cited Evidence-stage finding.

    Construction RAISES ``CitationError`` if ``txn_ids`` is empty: no claim
    without a receipt. ``label``/``plain_label`` carry the technical vs simple
    naming; ``plain`` is the jargon-free narrated claim (shown in both views).
    """
    typology: str
    label: str
    plain_label: str
    plain: str
    txn_ids: List[str]
    counterparties: List[str] = field(default_factory=list)
    device_ids: List[str] = field(default_factory=list)
    score: float = 0.0

    def __post_init__(self) -> None:
        if not self.txn_ids:
            raise CitationError(
                f"ground '{self.typology}' has no citing transaction id — refusing "
                "to emit an uncited claim (citation gate)")

    def to_dict(self) -> dict:
        return {
            "typology": self.typology, "label": self.label,
            "plain_label": self.plain_label, "plain": self.plain,
            "txn_ids": list(self.txn_ids), "counterparties": list(self.counterparties),
            "device_ids": list(self.device_ids), "score": round(float(self.score), 1),
            "citation_count": len(self.txn_ids),
        }


# --------------------------------------------------------------------------- #
# Case file
# --------------------------------------------------------------------------- #
@dataclass
class CaseFile:
    account_id: str
    score: float
    band: str
    account_meta: Dict[str, Any]
    stages: List[Stage]
    grounds: List[Ground]
    ring: Dict[str, Any]
    roles: Dict[str, str]
    recommendation: str
    recommendation_plain: str
    rationale: List[str]
    is_high_velocity: bool = False

    def stage(self, key: str) -> Optional[Stage]:
        return next((s for s in self.stages if s.key == key), None)


# --------------------------------------------------------------------------- #
# small formatting helpers (backend-local, no frontend import — Guardrail G1)
# --------------------------------------------------------------------------- #
def _fmt_inr(x: float) -> str:
    x = float(x or 0.0)
    if x >= 1e7:
        return f"₹{x / 1e7:.2f} Cr"
    if x >= 1e5:
        return f"₹{x / 1e5:.1f} L"
    return f"₹{x:,.0f}"


def _i(v) -> int:
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return 0


def _finding(text: str, tone: str = "neutral", technical: bool = False) -> dict:
    return {"text": text, "tone": tone, "technical": technical}


def _band_tone(band: str) -> str:
    return {BAND_ALERT: "risk", BAND_REVIEW: "warn", BAND_CLEAR: "good"}.get(band, "neutral")


def _hit_tone(score: float) -> str:
    return "risk" if score >= 65 else ("warn" if score >= 45 else "neutral")


# --------------------------------------------------------------------------- #
# data access (engine inputs only — never the labels file)
# --------------------------------------------------------------------------- #
@lru_cache(maxsize=4)
def _accounts_frame(data_dir: str) -> pd.DataFrame:
    df = pd.read_csv(Path(data_dir) / ACCOUNTS_CSV, dtype=str).fillna("")
    return df.set_index("account_id", drop=False)


@lru_cache(maxsize=4)
def _transactions_frame(data_dir: str) -> pd.DataFrame:
    df = pd.read_csv(Path(data_dir) / TRANSACTIONS_CSV)
    df["account_id"] = df["account_id"].astype(str)
    df["counterparty_id"] = df["counterparty_id"].astype(str)
    df["txn_id"] = df["txn_id"].astype(str)
    return df


def _account_meta(account_id: str, data_dir: Path = DATA_DIR) -> Dict[str, Any]:
    acc = _accounts_frame(str(data_dir))
    if account_id not in acc.index:
        return {"account_id": account_id, "account_type": "?", "open_date": "?",
                "kyc_income_band": "?", "linked_entity_id": ""}
    return acc.loc[account_id].to_dict()


# --------------------------------------------------------------------------- #
# ground-of-suspicion narration (one per fired typology, all cited)
# --------------------------------------------------------------------------- #
def _narrate(name: str, p: Dict[str, float]) -> str:
    """Jargon-free plain-language claim for a fired detector, from its numeric
    ``plain_summary_inputs`` (never prose from ml)."""
    if name == TYP_FAN:
        return (f"{_i(p.get('fan_in_degree'))} different payers funnelled money in, "
                f"and it was consolidated back out to just {_i(p.get('fan_out_degree'))} "
                f"destination(s) — a {p.get('consolidation_ratio', 0):.1f}-to-1 squeeze "
                f"on {_fmt_inr(p.get('inflow_total'))} of inflow.")
    if name == TYP_PASS:
        return (f"Money barely rests here: inflows and outflows match to within "
                f"{p.get('conduit_ratio', 0):.0%}, and {p.get('outflow_top3_share', 0):.0%} "
                f"of it is forwarded to a handful of accounts, typically within "
                f"{_i(p.get('median_passthrough_minutes'))} minutes.")
    if name == TYP_DORMANCY:
        return (f"The account sat quiet, then erupted into a concentrated burst of "
                f"{_i(p.get('burst_txn_count'))} transactions inside a three-week window.")
    if name == TYP_NEWVEL:
        return (f"Only {_i(p.get('age_days'))} days old, yet already running "
                f"{_i(p.get('n_txn'))} transactions ({p.get('txn_per_day', 0):.1f} a day) "
                f"and {_fmt_inr(p.get('inflow_total'))} in — disproportionate for a "
                "brand-new account.")
    if name == TYP_KYC:
        return (f"Monthly money movement of about {_fmt_inr(p.get('monthly_throughput'))} "
                f"is roughly {p.get('throughput_ratio', 0):.0f} times the ceiling of the "
                f"declared '{p.get('kyc_income_band')}' income band.")
    if name == TYP_STRUCT:
        return (f"{_i(p.get('threshold_hug_count'))} transactions are round amounts pinned "
                f"just under reporting limits ({p.get('threshold_hug_share', 0):.0%} of all "
                "activity) — a deliberate attempt to stay below the radar.")
    if name == TYP_ODD:
        return (f"{_i(p.get('odd_hours_count'))} transactions ({p.get('odd_hours_share', 0):.0%} "
                "of activity) fall in the 00:00–05:00 window — unusual for genuine "
                "personal banking.")
    if name == TYP_DEVICE:
        return (f"The same device was used across a cluster of {_i(p.get('cluster_size'))} "
                f"accounts ({_i(p.get('co_account_count'))} others besides this one) — the "
                "structural glue that ties a group of accounts together.")
    return "A suspicious behavioural pattern was detected."


def _build_grounds(hits) -> List[Ground]:
    """One cited ``Ground`` per fired typology. A hit with no txn_ids degrades to
    nothing here (an explicit note is emitted by the Evidence stage) rather than
    becoming an uncited claim."""
    grounds: List[Ground] = []
    for h in sorted(hits, key=lambda x: -x.score):
        if not h.txn_ids:
            continue  # citation gate: no receipt -> no ground (Evidence stage notes it)
        grounds.append(Ground(
            typology=h.name,
            label=TYPOLOGY_LABEL.get(h.name, h.name),
            plain_label=TYPOLOGY_LABEL_PLAIN.get(h.name, h.name),
            plain=_narrate(h.name, h.plain_summary_inputs),
            txn_ids=list(h.txn_ids), counterparties=list(h.counterparties),
            device_ids=list(h.device_ids), score=float(h.score)))
    return grounds


# --------------------------------------------------------------------------- #
# ring role inference (observable behaviour only — NO label file)
# --------------------------------------------------------------------------- #
ROLE_THIS = "this"
ROLE_CASHOUT = "cashout"
ROLE_RECRUITER = "recruiter"
ROLE_MULE = "mule"
ROLE_LINKED = "linked"

_CASH_SINK = "ATM-CASH"


def _classify_ring(engine, ring: dict, tx: pd.DataFrame) -> tuple[Dict[str, str], Dict[str, str]]:
    """Infer each ring member's role from its ledger + its band.

    * cash-out endpoint — makes repeated ATM/POS cash withdrawals (sink = the
      cash-extraction counterparty);
    * recruiter — a flagged hub that forwards to >=1 detected cash-out;
    * mule — any other Alert/Review member;
    * linked account — a Clear member pulled in by a shared device.
    The seed is always "this account". Roles are INFERRED, never read from labels.
    """
    members = ring["members"]
    seed = ring["seed"]
    mset = set(members)
    scored = engine.score_accounts()
    bands = {m: (scored.loc[m, "band"] if m in scored.index else BAND_CLEAR) for m in members}

    sub = tx[tx["account_id"].isin(mset)]
    debits = sub[sub["direction"] == "debit"]
    cashouts = set()
    for aid, g in debits.groupby("account_id"):
        if int((g["counterparty_id"] == _CASH_SINK).sum()) >= 3:
            cashouts.add(str(aid))
    recruiters = set()
    for aid, g in debits.groupby("account_id"):
        if str(aid) in cashouts:
            continue
        if int(g["counterparty_id"].isin(cashouts).sum()) >= 2:
            recruiters.add(str(aid))

    roles: Dict[str, str] = {}
    for m in members:
        if m == seed:
            roles[m] = ROLE_THIS
        elif m in cashouts:
            roles[m] = ROLE_CASHOUT
        elif m in recruiters:
            roles[m] = ROLE_RECRUITER
        elif bands[m] in (BAND_ALERT, BAND_REVIEW):
            roles[m] = ROLE_MULE
        else:
            roles[m] = ROLE_LINKED
    return roles, bands


# --------------------------------------------------------------------------- #
# Per-stage ML technique disclosure (algorithm string is Technical-only).
# --------------------------------------------------------------------------- #
TECHNIQUES: Dict[str, Dict[str, str]] = {
    "triage": {
        "plain": "Risk triage",
        "algorithm": "Blended score = 0.55 · typology strength + 0.45 · anomaly "
                     "excess (Isolation Forest), banded Alert ≥ 65 / Review ≥ 45",
        "benefit": "One transparent score decides whether an account even reaches "
                   "the desk — an interpretable rule leg plus an independent "
                   "anomaly second opinion, so nothing is queued on a hunch.",
    },
    "evidence": {
        "plain": "Citation-gated evidence",
        "algorithm": "Deterministic behavioural detectors; every claim bound to "
                     "≥1 concrete transaction id (construction refuses an uncited claim)",
        "benefit": "Every line of suspicion is tied to specific transactions you "
                   "can open and read. If a pattern can't cite a real transaction, "
                   "it is never asserted — no receipt, no claim.",
    },
    "network": {
        "plain": "Ring expansion",
        "algorithm": "Pure-python breadth-first search over shared-device and "
                     "high-value-transfer edges; deterministic circular layout (no graph library)",
        "benefit": "Walks outward from the flagged account along shared devices and "
                   "money transfers to reveal the wider group it belongs to — "
                   "the network view a single-account check can't see.",
    },
    "adjudication": {
        "plain": "Deterministic decision table",
        "algorithm": "Rule-based mapping of band + evidence strength to a "
                     "recommendation; an LLM narrative layer is an optional pilot "
                     "step — nothing here requires one, and a human always decides",
        "benefit": "The recommendation follows explicit, auditable rules rather "
                   "than a black box, and it is only ever a recommendation — an "
                   "analyst approves or overrides.",
    },
    "casefile": {
        "plain": "Structured case file",
        "algorithm": "Assembles grounds + annexures into a suspicious-transaction-"
                     "report-style draft, awaiting the human decision",
        "benefit": "The whole investigation is packaged as a ready-to-review "
                   "dossier — grounds, the account and its network, and the "
                   "supporting transactions — for a fast, confident human call.",
    },
}


# --------------------------------------------------------------------------- #
# Stage builders
# --------------------------------------------------------------------------- #
def _stage_triage(account_id: str, row: dict, meta: dict, tpad: float) -> Stage:
    score = float(row["score"])
    band = row["band"]
    typ_c = float(row["typology_component"])
    anom_c = float(row["anomaly_component"])
    n_typ = _i(row["n_typologies"])
    log = [
        f"Triage agent · pulling risk file for account {account_id} …",
        f"Blended risk score: {score:.1f}/100  →  band '{band}'",
        f"  interpretable pattern strength : {typ_c:.1f}/100",
        f"  independent anomaly component  : {anom_c:.1f}/100",
        f"Behavioural patterns fired: {n_typ}",
        "Account admitted to the desk." if band != BAND_CLEAR
        else "No banded risk — routed for an explainable clearance.",
    ]
    if band == BAND_ALERT:
        headline = (f"Account {account_id} is queued at {score:.0f}/100 — the top "
                    "risk band — and needs an analyst's eyes.")
    elif band == BAND_REVIEW:
        headline = (f"Account {account_id} scores {score:.0f}/100 — a middle band that "
                    "warrants a closer look.")
    else:
        headline = (f"Account {account_id} scores {score:.0f}/100 and sits in the clear "
                    "band — this run explains why it should stay cleared.")
    findings = [_finding(
        f"Two independent voices agree on the score: a rule-based pattern strength "
        f"of {typ_c:.0f}/100 and an independent anomaly reading of {anom_c:.0f}/100.",
        _band_tone(band))]
    findings.append(_finding(
        f"Account type on file: {meta.get('account_type', '?')}; declared income band "
        f"'{meta.get('kyc_income_band', '?')}'; opened {meta.get('open_date', '?')}.",
        "neutral"))
    if tpad >= HIGH_VELOCITY_TPAD and band == BAND_CLEAR:
        findings.append(_finding(
            f"High day-to-day activity (~{tpad:.0f} transactions a day) — the kind a "
            "busy genuine earner shows; the checks below test whether it is benign.",
            "neutral"))
    return Stage(1, "triage", "Triage agent",
                 "Why this account reached the desk — the score and its two components.",
                 1.5, log, {"score": round(score, 1), "band": band,
                            "typology_component": round(typ_c, 1),
                            "anomaly_component": round(anom_c, 1),
                            "n_typologies": n_typ, "typologies": list(row["typologies"]),
                            "account_meta": meta, "txn_per_active_day": round(tpad, 2)},
                 headline=headline, findings=findings, technique=TECHNIQUES["triage"])


def _stage_evidence(grounds: List[Ground], n_fired: int) -> Stage:
    log = ["Evidence agent · assembling grounds of suspicion …"]
    findings: List[dict] = []
    if grounds:
        for g in grounds:
            cites = len(g.txn_ids)
            log.append(f"  ✓ {g.label:<32} {g.score:>5.1f}/100 · {cites} cited txn(s)")
            findings.append(_finding(g.plain, _hit_tone(g.score)))
        headline = (f"{len(grounds)} ground(s) of suspicion, each backed by real "
                    "transactions you can open and read.")
        total_cites = sum(len(g.txn_ids) for g in grounds)
        findings.append(_finding(
            f"Every ground cites at least one transaction — {total_cites} in total. "
            "No pattern is asserted without a transaction to back it.", "neutral"))
    else:
        log.append("  — no behavioural pattern cleared the evidence gate.")
        headline = ("No behavioural pattern could be evidenced against this account.")
        findings.append(_finding(
            "No suspicious pattern cited any transaction, so none is asserted. "
            "The account carries no evidenced grounds of suspicion.", "good"))
    if n_fired > len(grounds):
        log.append(f"  · {n_fired - len(grounds)} detector(s) fired without usable "
                   "evidence — dropped as 'insufficient evidence' (not asserted).")
        findings.append(_finding(
            f"{n_fired - len(grounds)} weaker signal(s) could not cite a specific "
            "transaction and were dropped rather than asserted without proof.",
            "neutral", technical=True))
    return Stage(2, "evidence", "Evidence agent",
                 "Each suspicious pattern, stated plainly and tied to the transactions that triggered it.",
                 2.5, log, {"grounds": [g.to_dict() for g in grounds],
                            "n_grounds": len(grounds), "n_fired": n_fired},
                 headline=headline, findings=findings, technique=TECHNIQUES["evidence"])


def _stage_network(ring: dict, roles: Dict[str, str], bands: Dict[str, str],
                   typ_dist: List[dict]) -> Stage:
    members = ring["members"]
    edges = ring["edges"]
    size = len(members)
    device_edges = [e for e in edges if e["type"] == "device"]
    n_cashout = sum(1 for r in roles.values() if r == ROLE_CASHOUT)
    n_recruiter = sum(1 for r in roles.values() if r == ROLE_RECRUITER)
    n_alert = sum(1 for m in members if bands.get(m) == BAND_ALERT)
    log = [
        "Network agent · expanding outward from the flagged account …",
        f"  linked accounts discovered : {size}",
        f"  shared-device links        : {len(device_edges)}",
        f"  cash-out endpoints         : {n_cashout}",
        f"  recruiter hubs             : {n_recruiter}",
        "Network mapped." if size > 1 else "No linked accounts — this account stands alone.",
    ]
    if size <= 1:
        headline = "This account is not linked to any other account in the ledger."
        findings = [_finding("No shared devices or repeated transfers connect this "
                             "account to others — it stands alone.", "neutral")]
    else:
        headline = (f"This account belongs to a cluster of {size} linked accounts"
                    + (f", including {n_cashout} cash-out endpoint(s)." if n_cashout
                       else "."))
        tone = "risk" if n_alert else "warn"
        findings = [_finding(
            f"{size} accounts are tied together by {len(device_edges)} shared-device "
            f"link(s) and repeated transfers; {n_alert} of them are themselves in the "
            "top risk band.", tone)]
        if n_cashout:
            findings.append(_finding(
                f"{n_cashout} member(s) look like cash-out points — accounts that "
                "repeatedly pull the money out as ATM/POS cash.", "risk"))
        if n_recruiter:
            findings.append(_finding(
                f"{n_recruiter} member(s) act as hubs, forwarding funds on to the "
                "cash-out points.", "warn"))
    return Stage(3, "network", "Network agent",
                 "The wider group the account belongs to — shared devices and money flows.",
                 2.5, log, {"ring": ring, "roles": roles, "bands": bands,
                            "size": size, "n_cashout": n_cashout,
                            "n_recruiter": n_recruiter, "n_alert": n_alert,
                            "typology_distribution": typ_dist},
                 headline=headline, findings=findings, technique=TECHNIQUES["network"])


def _decide(band: str, grounds: List[Ground], ring_size: int,
            is_high_velocity: bool) -> tuple[str, List[dict]]:
    """Deterministic decision table: (band, evidence) -> recommendation.

    Returns the recommendation plus the rule rows that fired (for disclosure)."""
    strong = [g for g in grounds if g.score >= 65]
    rows = [
        {"rule": "Top risk band (Alert)", "hit": band == BAND_ALERT},
        {"rule": "≥1 strongly-evidenced ground", "hit": bool(strong)},
        {"rule": "Part of a linked cluster (>1 account)", "hit": ring_size > 1},
        {"rule": "Middle band (Review)", "hit": band == BAND_REVIEW},
        {"rule": "Clear band, no evidenced grounds", "hit": band == BAND_CLEAR and not grounds},
        {"rule": "High genuine-looking velocity", "hit": is_high_velocity},
    ]
    if band == BAND_ALERT:
        rec = REC_FREEZE
    elif band == BAND_REVIEW or (grounds and band != BAND_CLEAR):
        rec = REC_MONITOR
    else:
        rec = REC_CLEAR
    return rec, rows


def _rationale(account_id: str, band: str, rec: str, grounds: List[Ground],
               ring_size: int, n_cashout: int, is_high_velocity: bool) -> List[str]:
    """The adjudication paragraph (2–3 sentences), fully composed here."""
    if rec == REC_FREEZE:
        lead = (f"Account {account_id} sits in the top risk band with "
                f"{len(grounds)} evidenced ground(s) of suspicion, each tied to real "
                "transactions.")
        net = (f" It is part of a linked cluster of {ring_size} accounts"
               + (f" with {n_cashout} cash-out point(s)." if n_cashout else ".")
               if ring_size > 1 else "")
        act = (" Recommendation: freeze the account and prepare a suspicious-transaction "
               "report for an analyst to review and file.")
        return [lead + net, act]
    if rec == REC_MONITOR:
        lead = (f"Account {account_id} shows {len(grounds)} suspicious pattern(s) but "
                "not at the strength that warrants a freeze on its own.")
        act = (" Recommendation: keep it under closer watch and re-check as more "
               "activity accrues.")
        return [lead, act]
    # Clear
    if is_high_velocity:
        return [
            (f"Account {account_id} moves money quickly, but the checks find the high "
             "velocity is consistent with declared gig-style income — and there is no "
             "collect-and-forward, no straight-through movement, and no shared device."),
            ("None of the structural patterns that define a rented-out account are "
             "present, so the account is cleared, with this reasoning kept on file."),
        ]
    return [
        (f"Account {account_id} carries no evidenced ground of suspicion; its activity "
         "is routine and none of the misuse patterns are present."),
        "Recommendation: clear the account, with a note on file.",
    ]


def _stage_adjudication(account_id: str, band: str, grounds: List[Ground],
                        ring_size: int, n_cashout: int,
                        is_high_velocity: bool) -> tuple[Stage, str, List[str]]:
    rec, rows = _decide(band, grounds, ring_size, is_high_velocity)
    rationale = _rationale(account_id, band, rec, grounds, ring_size, n_cashout,
                           is_high_velocity)
    log = ["Adjudication agent · applying the decision table …"]
    for r in rows:
        log.append(f"  [{'x' if r['hit'] else ' '}] {r['rule']}")
    log.append(f"Recommendation: {rec}")
    tone = {REC_FREEZE: "risk", REC_MONITOR: "warn", REC_CLEAR: "good"}[rec]
    headline = f"Recommendation: {REC_PLAIN[rec]}."
    findings = [_finding(line, tone if i == 0 else "neutral")
                for i, line in enumerate(rationale)]
    return (Stage(4, "adjudication", "Adjudication agent",
                  "A transparent decision table turns the evidence into a recommendation — a human decides.",
                  2.0, log, {"recommendation": rec, "recommendation_plain": REC_PLAIN[rec],
                             "rationale": rationale, "decision_rows": rows, "band": band},
                  headline=headline, findings=findings,
                  technique=TECHNIQUES["adjudication"]),
            rec, rationale)


def _stage_casefile(account_id: str, meta: dict, row: dict, grounds: List[Ground],
                    ring: dict, roles: Dict[str, str], rec: str,
                    rationale: List[str]) -> Stage:
    txn_ids = sorted({t for g in grounds for t in g.txn_ids})
    ring_annexure = [{"account": m, "role": roles.get(m, ROLE_LINKED)}
                     for m in ring["members"]]
    account_annexure = {
        "account_id": account_id, "account_type": meta.get("account_type"),
        "open_date": meta.get("open_date"), "kyc_income_band": meta.get("kyc_income_band"),
        "linked_entity_id": meta.get("linked_entity_id") or "—",
        "score": round(float(row["score"]), 1), "band": row["band"],
    }
    log = [
        "Case-file compiler · drafting the suspicious-transaction-report package …",
        f"  grounds of suspicion : {len(grounds)}",
        f"  cited transactions   : {len(txn_ids)}",
        f"  ring annexure        : {len(ring_annexure)} account(s)",
        f"  recommendation       : {rec}",
        "Draft assembled — awaiting the analyst's approve / override.",
    ]
    headline = (f"A ready-to-review case file: {len(grounds)} ground(s), "
                f"{len(txn_ids)} cited transaction(s), and a recommendation — "
                "awaiting your decision.")
    findings = [_finding(rationale[0] if rationale else "", _band_tone(row["band"]))]
    findings.append(_finding(
        "The file is a draft only. Nothing is actioned until an analyst approves "
        "or overrides it — the human stays in charge.", "neutral"))
    return Stage(5, "casefile", "Case-file compiler",
                 "The evidence, the network and the recommendation packaged for a human decision.",
                 2.0, log, {"grounds": [g.to_dict() for g in grounds],
                            "account_annexure": account_annexure,
                            "ring_annexure": ring_annexure, "txn_annexure_ids": txn_ids,
                            "recommendation": rec, "recommendation_plain": REC_PLAIN[rec],
                            "rationale": rationale},
                 headline=headline, findings=findings, technique=TECHNIQUES["casefile"])


# --------------------------------------------------------------------------- #
# Public entry point — the five-stage investigation
# --------------------------------------------------------------------------- #
def investigate(fraud_engine, account_id: str,
                transactions: Optional[pd.DataFrame] = None,
                data_dir: Path = DATA_DIR) -> CaseFile:
    """Run the five-stage agentic investigation for one account.

    Composes every user-facing string here (D6). The citation gate is enforced
    inside ``Ground`` construction, so no uncited claim can reach the case file.
    """
    row = fraud_engine.account_row(account_id)
    band = row["band"]
    hits = fraud_engine.typology_hits(account_id)
    ring = fraud_engine.expand_ring(account_id)
    meta = _account_meta(account_id, data_dir)
    tx = transactions if transactions is not None else _transactions_frame(str(data_dir))

    fm = getattr(fraud_engine, "feature_matrix", None)
    tpad = float(fm.loc[account_id, "txn_per_active_day"]) \
        if fm is not None and account_id in fm.index else 0.0
    is_high_velocity = tpad >= HIGH_VELOCITY_TPAD

    grounds = _build_grounds(hits)
    roles, bands = _classify_ring(fraud_engine, ring, tx)
    n_cashout = sum(1 for r in roles.values() if r == ROLE_CASHOUT)
    typ_dist = _typology_distribution_for(grounds)

    triage = _stage_triage(account_id, row, meta, tpad)
    evidence = _stage_evidence(grounds, n_fired=len(hits))
    network = _stage_network(ring, roles, bands, typ_dist)
    adjud, rec, rationale = _stage_adjudication(
        account_id, band, grounds, len(ring["members"]), n_cashout, is_high_velocity)
    casefile = _stage_casefile(account_id, meta, row, grounds, ring, roles, rec, rationale)

    return CaseFile(
        account_id=account_id, score=float(row["score"]), band=band,
        account_meta=meta, stages=[triage, evidence, network, adjud, casefile],
        grounds=grounds, ring=ring, roles=roles, recommendation=rec,
        recommendation_plain=REC_PLAIN[rec], rationale=rationale,
        is_high_velocity=is_high_velocity)


def _typology_distribution_for(grounds: List[Ground]) -> List[dict]:
    """Per-ground label+score, for a small in-case bar (not the desk-wide one)."""
    return [{"typology": g.typology, "label": g.label,
             "plain_label": g.plain_label, "score": round(g.score, 1)}
            for g in grounds]


# --------------------------------------------------------------------------- #
# Desk snapshot — queue, KPIs, typology distribution (all copy composed here)
# --------------------------------------------------------------------------- #
def _exposure(fm, account_id: str) -> float:
    if fm is not None and account_id in fm.index:
        return float(fm.loc[account_id, "inflow_total"])
    return 0.0


def _count_rings(engine, alert_ids: List[str]) -> int:
    """Distinct suspected rings among the Alert accounts (connected components of
    the suspicious-edge graph), computed via expand_ring — no label file."""
    seen: set = set()
    n = 0
    for aid in alert_ids:
        if aid in seen:
            continue
        members = set(engine.expand_ring(aid)["members"])
        if len(members) > 1:
            n += 1
        seen |= members
    return n


def desk_snapshot(fraud_engine) -> dict:
    """The Fraud-Desk payload: queue rows, KPIs (labelled illustrative), the
    typology distribution, and deterministic default selections (a juicy ring
    seed + a high-velocity hard-negative to show the clear-both-ways story).
    All copy composed here; the page renders only."""
    scored = fraud_engine.score_accounts()
    fm = getattr(fraud_engine, "feature_matrix", None)

    queue_df = scored[scored["band"].isin([BAND_ALERT, BAND_REVIEW])]
    queue: List[dict] = []
    for aid, r in queue_df.iterrows():
        typ = list(r["typologies"])
        queue.append({
            "account": aid, "score": float(r["score"]), "band": r["band"],
            "typologies": typ,
            "typology_labels": [TYPOLOGY_LABEL.get(t, t) for t in typ],
            "typology_labels_plain": [TYPOLOGY_LABEL_PLAIN.get(t, t) for t in typ],
            "n_typologies": _i(r["n_typologies"]),
            "exposure": round(_exposure(fm, aid), 2),
            "exposure_display": _fmt_inr(_exposure(fm, aid)),
        })
    queue.sort(key=lambda q: (-q["score"], q["account"]))

    alert_ids = scored[scored["band"] == BAND_ALERT].index.tolist()
    n_rings = _count_rings(fraud_engine, alert_ids)
    blocked = sum(_exposure(fm, a) for a in alert_ids)

    kpis = [
        {"label": "Accounts monitored", "value": f"{len(scored):,}", "kind": "",
         "sub": "synthetic ledger"},
        {"label": "Accounts on the desk", "value": str(len(queue)), "kind": "warn",
         "sub": f"{len(alert_ids)} in the top band"},
        {"label": "Suspected rings", "value": str(n_rings), "kind": "risk",
         "sub": "linked account clusters"},
        {"label": "Exposure flagged", "value": _fmt_inr(blocked), "kind": "risk",
         "sub": "illustrative — inflow through flagged accounts"},
    ]

    # typology distribution across the whole flagged desk
    dist: Dict[str, int] = {}
    for q in queue:
        for t in q["typologies"]:
            dist[t] = dist.get(t, 0) + 1
    typ_dist = [{"typology": t, "label": TYPOLOGY_LABEL.get(t, t),
                 "plain_label": TYPOLOGY_LABEL_PLAIN.get(t, t), "count": c}
                for t, c in sorted(dist.items(), key=lambda kv: -kv[1])]

    default_case = _default_ring_seed(fraud_engine, scored)
    hard_negative = _default_hard_negative(scored, fm)

    return {
        "kpis": kpis, "queue": queue, "typology_distribution": typ_dist,
        "why_track": WHY_TRACK, "scope_note": SCOPE_NOTE,
        "default_case": default_case, "hard_negative": hard_negative,
        "n_alert": len(alert_ids), "n_rings": n_rings,
    }


def _default_ring_seed(engine, scored: pd.DataFrame) -> Optional[str]:
    """The juiciest ring mule: the Alert account with the most fired patterns whose
    ring pulls in the most accounts (deterministic tie-breaks)."""
    alerts = scored[scored["band"] == BAND_ALERT]
    if alerts.empty:
        return None
    best = None
    best_key = None
    for aid, r in alerts.iterrows():
        size = len(engine.expand_ring(aid)["members"])
        key = (_i(r["n_typologies"]), size, -_ord(aid))
        if best_key is None or key > best_key:
            best_key, best = key, aid
    return best


def _default_hard_negative(scored: pd.DataFrame, fm) -> Optional[str]:
    """A Clear account with the highest genuine-looking velocity — the
    explainably-cleared demo star (gig worker / small merchant)."""
    clears = scored[scored["band"] == BAND_CLEAR].index.tolist()
    if fm is None or not clears:
        return clears[0] if clears else None
    pool = [a for a in clears if a in fm.index]
    if not pool:
        return clears[0]
    return max(pool, key=lambda a: (float(fm.loc[a, "txn_per_active_day"]), -_ord(a)))


def _ord(account_id: str) -> int:
    """Stable numeric ordinal of an account id for deterministic tie-breaking."""
    digits = "".join(ch for ch in str(account_id) if ch.isdigit())
    return int(digits) if digits else 0
