"""Named demo archetypes + randomiser (Appendix B §4, demo-architecture.md).

Each archetype pins a sector/scale/latent profile and a plausible source subset;
the rest is randomised so repeated demo runs vary (ML reads as adaptive, not
hardcoded). Archetypes intentionally span the health/honesty space so the demo
can show a clean approve, a cautious thin-file, and a caught inflated-turnover.
"""
from __future__ import annotations

from typing import Optional
import numpy as np

from .profiles import MSMEProfile, sample_profile

# archetype_key -> override dict fed to sample_profile
ARCHETYPES = {
    "textile_manufacturer": dict(
        name="Sunrise Textiles Pvt Ltd", archetype="textile_manufacturer",
        sector="Manufacturing", category="Small", turnover=80_000_000,
        age_years=12, employees=45, incorporated=True, gst_registered=True,
        digital_adoption=True, exports=True, has_physical_premises=True,
        true_health="healthy", true_honesty="genuine"),
    "retail_kirana": dict(
        name="Anand Kirana Store", archetype="retail_kirana",
        sector="Trade", category="Micro", turnover=4_500_000,
        age_years=6, employees=2, incorporated=False, gst_registered=True,
        digital_adoption=True, exports=False, has_physical_premises=True,
        true_health="healthy", true_honesty="genuine"),
    "restaurant": dict(
        name="Spice Route Restaurant", archetype="restaurant",
        sector="Services", category="Micro", turnover=9_000_000,
        age_years=4, employees=8, incorporated=False, gst_registered=True,
        digital_adoption=True, exports=False, has_physical_premises=True,
        true_health="stressed", true_honesty="genuine"),
    "it_services": dict(
        name="Nexus IT Solutions LLP", archetype="it_services",
        sector="Services", category="Small", turnover=35_000_000,
        age_years=7, employees=30, incorporated=True, gst_registered=True,
        digital_adoption=True, exports=True, has_physical_premises=True,
        true_health="healthy", true_honesty="genuine"),
    "auto_components": dict(
        name="Precision Auto Components", archetype="auto_components",
        sector="Manufacturing", category="Small", turnover=60_000_000,
        age_years=9, employees=38, incorporated=True, gst_registered=True,
        digital_adoption=True, exports=False, sells_to_govt=True,
        has_physical_premises=True,
        # inflated-turnover fraud showcase: declared turnover >> real evidence.
        true_health="stressed", true_honesty="inflated"),
    "logistics": dict(
        name="FastTrack Logistics", archetype="logistics",
        sector="Services", category="Small", turnover=45_000_000,
        age_years=8, employees=22, incorporated=True, gst_registered=True,
        digital_adoption=True, exports=False, has_physical_premises=True,
        true_health="healthy", true_honesty="genuine"),
}

ARCHETYPE_KEYS = list(ARCHETYPES.keys())


def build_archetype(key: str, seed: int) -> MSMEProfile:
    if key not in ARCHETYPES:
        raise KeyError(f"Unknown archetype '{key}'. Options: {ARCHETYPE_KEYS}")
    rng = np.random.default_rng(seed)
    ov = dict(ARCHETYPES[key])
    p = sample_profile(rng, entity_id=key.upper(), seed=seed, overrides=ov)
    # Archetypes are narrative demo exemplars: pin their ground-truth outcome
    # deterministically by health so the demo tells a coherent story every run
    # (distressed defaults; healthy/stressed do not). The 400-entity random
    # cohort keeps stochastic labels for realistic model training.
    p.label_default = 1 if p.true_health == "distressed" else 0
    # Pin the inflated showcase to a STRONG, deterministic gap so the flagship
    # Turnover-Authenticity check flags it reliably every run (not a random draw).
    if p.true_honesty == "inflated":
        p.declared_turnover = round(p.true_scale_turnover * 2.2, 2)
    return p


def build_random(seed: int, entity_id: Optional[str] = None) -> MSMEProfile:
    rng = np.random.default_rng(seed)
    eid = entity_id or f"E{seed:06d}"
    return sample_profile(rng, entity_id=eid, seed=seed)
