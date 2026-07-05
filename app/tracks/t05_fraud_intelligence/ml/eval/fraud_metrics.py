"""SentinelPulse detection scorecard (Track 05, WP-5M) — EVAL / TESTS ONLY.

Scores the fitted ``FraudEngine`` against the held-out labels and prints a
banker-legible scorecard. **This is the only module in the track permitted to
read the labels file** — the engine, features and typologies never do.

Headline metrics:
  * ring-level recall   — a ring counts as caught if >=60% of its members land
                          at Review or above;
  * hard-negative FP rate — the differentiator: clean high-velocity accounts that
                          are (wrongly) not Cleared. Target 0;
  * account precision / recall at Alert;
  * per-typology capture — did the right detector fire on each injected account.
"""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd

from ...data_gen.build import DATA_DIR, GROUND_TRUTH_CSV
from ...data_gen.typologies import ALL_TYPOLOGIES
from ..model import BAND_ALERT, BAND_REVIEW, FraudEngine

RING_CAUGHT_FRACTION = 0.60


def _load_labels(data_dir: Path) -> pd.DataFrame:
    gt = pd.read_csv(data_dir / GROUND_TRUTH_CSV, dtype=str)
    gt["is_mule"] = gt["is_mule"].astype(int)
    gt["is_hard_negative"] = gt["is_hard_negative"].astype(int)
    gt["ring_id"] = gt["ring_id"].fillna("").astype(str)
    gt["typologies_expressed"] = gt["typologies_expressed"].fillna("").astype(str)
    return gt


def evaluate(engine: FraudEngine, data_dir: Path | str = DATA_DIR) -> Dict:
    """Compute the scorecard metrics. Returns a plain dict of numbers."""
    data_dir = Path(data_dir)
    gt = _load_labels(data_dir)
    scored = engine.score_accounts()
    band = scored["band"].to_dict()
    at_review = {a: band.get(a, "Clear") in ("Review", "Alert") for a in gt.account_id}
    at_alert = {a: band.get(a, "Clear") == "Alert" for a in gt.account_id}

    # ---- ring-level recall ----
    rings = sorted(r for r in gt.ring_id.unique() if r)
    ring_caught = {}
    for rid in rings:
        members = list(gt.loc[gt.ring_id == rid, "account_id"])
        frac = sum(at_review[m] for m in members) / max(len(members), 1)
        ring_caught[rid] = frac >= RING_CAUGHT_FRACTION
    ring_recall = sum(ring_caught.values()) / max(len(rings), 1)

    # ---- account precision / recall at Alert (label = is_mule) ----
    mule = dict(zip(gt.account_id, gt.is_mule == 1))
    alert_ids = [a for a in gt.account_id if at_alert[a]]
    tp = sum(mule[a] for a in alert_ids)
    precision = tp / len(alert_ids) if alert_ids else 0.0
    n_mule = int((gt.is_mule == 1).sum())
    recall = tp / n_mule if n_mule else 0.0

    # ring-associated precision (recruiters / cash-outs are fraud infra too)
    ring_assoc = dict(zip(gt.account_id, gt.ring_id != ""))
    tp_ring = sum(ring_assoc[a] for a in alert_ids)
    precision_ring = tp_ring / len(alert_ids) if alert_ids else 0.0

    # ---- hard-negative false-positive rate (headline) ----
    hn = list(gt.loc[gt.is_hard_negative == 1, "account_id"])
    hn_fp = sum(at_review[a] for a in hn)  # a hard neg is an FP if not Cleared
    hn_fp_rate = hn_fp / len(hn) if hn else 0.0

    # ---- per-typology capture ----
    capture: Dict[str, float] = {}
    for typ in ALL_TYPOLOGIES:
        expressing = [a for a in gt.account_id
                      if typ in gt.loc[gt.account_id == a, "typologies_expressed"].iloc[0].split(";")]
        if not expressing:
            capture[typ] = float("nan")
            continue
        fired = sum(any(h.name == typ for h in engine.typology_hits(a))
                    for a in expressing)
        capture[typ] = fired / len(expressing)

    return {
        "n_accounts": len(gt),
        "n_mule": n_mule,
        "n_rings": len(rings),
        "ring_caught": ring_caught,
        "ring_recall": ring_recall,
        "rings_caught": sum(ring_caught.values()),
        "alert_count": len(alert_ids),
        "precision_at_alert": precision,
        "recall_at_alert": recall,
        "precision_ring_at_alert": precision_ring,
        "hard_negative_fp": hn_fp,
        "hard_negative_fp_rate": hn_fp_rate,
        "hard_negative_count": len(hn),
        "per_typology_capture": capture,
    }


def print_scorecard(engine: FraudEngine, data_dir: Path | str = DATA_DIR) -> Dict:
    """Print a human-legible scorecard; return the metrics dict."""
    m = evaluate(engine, data_dir)
    line = "=" * 62
    print(line)
    print("SentinelPulse — Detection Scorecard (synthetic holdout)")
    print(line)
    print(f"accounts scored        : {m['n_accounts']}  "
          f"(mules {m['n_mule']}, rings {m['n_rings']})")
    print(f"RING RECALL            : {m['rings_caught']}/{m['n_rings']} "
          f"({m['ring_recall']:.0%})   [caught = >=60% members at Review+]")
    for rid, ok in m["ring_caught"].items():
        print(f"    {rid}: {'caught' if ok else 'MISSED'}")
    print(f"HARD-NEGATIVE FP RATE  : {m['hard_negative_fp']}/"
          f"{m['hard_negative_count']} ({m['hard_negative_fp_rate']:.0%})   "
          f"[target 0 — the differentiator]")
    print(f"ALERTS raised          : {m['alert_count']}")
    print(f"  precision (is_mule)  : {m['precision_at_alert']:.2f}")
    print(f"  precision (ring)     : {m['precision_ring_at_alert']:.2f}")
    print(f"  recall  (is_mule)    : {m['recall_at_alert']:.2f}")
    print("PER-TYPOLOGY CAPTURE:")
    for typ, cap in m["per_typology_capture"].items():
        bar = "n/a" if cap != cap else f"{cap:.2f}"
        print(f"    {typ:<26}: {bar}")
    print(line)
    return m


def main() -> None:
    engine = FraudEngine().fit()
    print_scorecard(engine)


if __name__ == "__main__":
    main()
