"""Fit the scoring engine and print the 6-archetype demo scorecard.

This is the documented manual demo script from Sprint-2 acceptance (c): it runs
every archetype end-to-end and records grade / score / confidence, and does a
light sanity check that healthy archetypes outrank stressed ones. Run: `make train`.
"""
from __future__ import annotations

from .engine import ScoringEngine
from ..data_gen.scenarios import ARCHETYPE_KEYS

_EXPECTED = {  # narrative expectation per archetype (for the sanity read)
    "textile_manufacturer": "healthy -> fast-track/approve",
    "retail_kirana": "healthy thin-file -> cautious approve",
    "restaurant": "stressed -> review/decline",
    "it_services": "healthy -> approve",
    "auto_components": "inflated turnover -> authenticity should flag it",
    "logistics": "healthy -> approve",
}


def main() -> None:
    engine = ScoringEngine().fit()
    print("=" * 92)
    print(" CreditPulse — Archetype Demo Scorecard")
    print("=" * 92)
    print(f"{'archetype':22s}{'score':>6s}{'grd':>4s}{'band':>13s}{'PD':>7s}"
          f"{'auth':>6s}{'conf':>7s}  expectation")
    print("-" * 92)
    results = {}
    for key in ARCHETYPE_KEYS:
        r = engine.score_entity(key.upper())
        results[key] = r
        print(f"{key:22s}{r['composite_score']:6.1f}{r['grade']:>4d}"
              f"{r['onboarding_band']:>13s}{r['pd']:>7.3f}"
              f"{r['turnover_authenticity_score']:>6.0f}{r['confidence_band']:>7s}  {_EXPECTED[key]}")
    print("-" * 92)

    # Sanity checks (not a formal test — documented expectations).
    textile = results["textile_manufacturer"]
    restaurant = results["restaurant"]
    auto = results["auto_components"]
    checks = [
        ("healthy textile outranks stressed restaurant",
         textile["composite_score"] > restaurant["composite_score"]),
        ("inflated auto-components flagged by authenticity (<75)",
         auto["turnover_authenticity_score"] < 75),
        ("textile is fast-track grade (<=3)", textile["grade"] <= 3),
    ]
    for label, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    print("=" * 92)
    print(" Reason-code sample — auto_components (inflated turnover):")
    for r in auto["reasons_negative"][:3]:
        print(f"   (-) {r['text'][:82]}")
    print("=" * 92)


if __name__ == "__main__":
    main()
