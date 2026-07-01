"""Latent-variable MSME profile model — cross-source consistency mechanism.

Appendix B §2.1: each synthetic MSME is drawn from a few *latent* variables
(true scale, true health, true honesty) FIRST; every per-source generator then
samples its observable fields conditioned on those latents rather than
independently. That is what makes the composite indicators (Appendix A §5)
demonstrate a real fused signal instead of coincidental agreement, and it is
what lets the "inflated-turnover" profile decouple declared GST turnover from
the electricity/EPFO/bank evidence so the authenticity composites fire.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Optional
import numpy as np

from . import distributions as D

# Latent health states and their default-probability multipliers.
HEALTH_STATES = ("healthy", "stressed", "distressed")
HEALTH_WEIGHTS = (0.62, 0.28, 0.10)
HEALTH_DEFAULT_MULT = {"healthy": 0.25, "stressed": 1.4, "distressed": 4.0}

# Honesty states: 'genuine' vs 'inflated' (declares turnover above true scale).
HONESTY_STATES = ("genuine", "inflated")
HONESTY_WEIGHTS = (0.90, 0.10)


def _weighted_choice(rng: np.random.Generator, mapping: dict) -> str:
    keys = list(mapping.keys())
    probs = np.array(list(mapping.values()), dtype=float)
    probs = probs / probs.sum()
    return str(rng.choice(keys, p=probs))


def _sample_band(rng: np.random.Generator, bands) -> tuple:
    weights = np.array([b[2] for b in bands], dtype=float)
    weights = weights / weights.sum()
    idx = rng.choice(len(bands), p=weights)
    return bands[idx]


@dataclass
class MSMEProfile:
    """A single synthetic MSME with its latent drivers and observable attributes.

    The `true_*` fields are the ground truth latents; generators read them.
    `label_default` / `label_fraud` are the eval-harness ground-truth targets.
    """
    entity_id: str
    name: str
    sector: str
    category: str
    state: str
    urban_rural: str
    age_years: float
    employees: int
    incorporated: bool
    gst_registered: bool
    digital_adoption: bool
    women_owned: bool
    exports: bool
    sells_to_govt: bool
    has_physical_premises: bool

    # --- latents ---
    true_scale_turnover: float          # true annual turnover (INR)
    true_health: str                    # healthy / stressed / distressed
    true_honesty: str                   # genuine / inflated
    declared_turnover: float            # what GST/self-reported shows (>= true if inflated)
    seed: int = 0

    # --- ground-truth labels ---
    label_default: int = 0              # 1 => defaults within horizon
    label_fraud: int = 0                # 1 => turnover misrepresentation present

    # archetype tag (None for randomised entities)
    archetype: Optional[str] = None

    def rng(self, salt: int = 0) -> np.random.Generator:
        """Deterministic per-entity RNG so re-runs are identical (ReconWise determinism)."""
        return np.random.default_rng(self.seed + salt)

    def as_dict(self) -> dict:
        return asdict(self)


def sample_profile(rng: np.random.Generator, entity_id: str, seed: int,
                   overrides: Optional[dict] = None) -> MSMEProfile:
    """Draw one MSME profile from the calibrated distributions.

    `overrides` lets archetypes/scenarios pin specific attributes while leaving
    the rest randomised.
    """
    overrides = overrides or {}

    category = overrides.get("category") or _weighted_choice(rng, D.CATEGORY_WEIGHTS)
    sector = overrides.get("sector") or _weighted_choice(rng, D.SECTOR_WEIGHTS)
    state = overrides.get("state") or _weighted_choice(rng, D.STATE_WEIGHTS)
    urban_rural = overrides.get("urban_rural") or _weighted_choice(rng, D.URBAN_RURAL_WEIGHTS)

    # Turnover: pick a band (optionally constrained), then uniform within it.
    if "turnover" in overrides:
        true_turnover = float(overrides["turnover"])
    else:
        lo, hi, _ = _sample_band(rng, D.TURNOVER_BANDS)
        true_turnover = float(rng.uniform(lo, hi))

    # Age
    if "age_years" in overrides:
        age = float(overrides["age_years"])
    else:
        lo, hi, _ = _sample_band(rng, D.AGE_BANDS)
        age = float(rng.uniform(lo, hi))

    # Employees conditioned on category
    if "employees" in overrides:
        employees = int(overrides["employees"])
    else:
        elo, ehi, _ = _sample_band(rng, D.EMPLOYEE_BANDS[category])
        employees = int(rng.integers(elo, ehi + 1))

    # GST registration probability by turnover
    if "gst_registered" in overrides:
        gst_registered = bool(overrides["gst_registered"])
    else:
        p = next(prob for ub, prob in D.GST_REG_PROB if true_turnover <= ub)
        gst_registered = bool(rng.random() < p)

    # Digital adoption by turnover
    p_dig = next(prob for ub, prob in D.DIGITAL_ADOPTION_PROB if true_turnover <= ub)
    digital_adoption = bool(overrides.get("digital_adoption", rng.random() < p_dig))

    incorporated = bool(overrides.get(
        "incorporated", rng.random() < D.INCORPORATION_PROB[category]))
    women_owned = bool(overrides.get("women_owned", rng.random() < D.WOMEN_OWNED_PROB))
    exports = bool(overrides.get("exports", sector == "Manufacturing" and rng.random() < 0.20))
    sells_to_govt = bool(overrides.get("sells_to_govt", rng.random() < 0.12))
    has_premises = bool(overrides.get("has_physical_premises", sector != "Services" or rng.random() < 0.7))

    # Latents
    health = overrides.get("true_health") or _weighted_choice(
        rng, dict(zip(HEALTH_STATES, HEALTH_WEIGHTS)))
    honesty = overrides.get("true_honesty") or _weighted_choice(
        rng, dict(zip(HONESTY_STATES, HONESTY_WEIGHTS)))

    # Declared turnover: genuine ~= true (small noise); inflated multiplies up.
    if honesty == "inflated":
        declared = true_turnover * float(rng.uniform(1.4, 2.6))
    else:
        declared = true_turnover * float(rng.uniform(0.95, 1.05))

    # Ground-truth default label: base rate * health multiplier, skewed up for
    # thin-file / unregistered / very small (Appx-B §1.10 directional skew).
    base = D.BASE_DEFAULT_RATE * HEALTH_DEFAULT_MULT[health]
    if not gst_registered:
        base *= 1.5
    if true_turnover < 1_000_000:
        base *= 1.3
    if honesty == "inflated":
        base *= 1.8
    p_default = float(np.clip(base, 0.0, 0.97))
    label_default = int(rng.random() < p_default)
    label_fraud = int(honesty == "inflated")

    return MSMEProfile(
        entity_id=entity_id,
        name=overrides.get("name", f"MSME {entity_id}"),
        sector=sector, category=category, state=state, urban_rural=urban_rural,
        age_years=round(age, 1), employees=employees, incorporated=incorporated,
        gst_registered=gst_registered, digital_adoption=digital_adoption,
        women_owned=women_owned, exports=exports, sells_to_govt=sells_to_govt,
        has_physical_premises=has_premises,
        true_scale_turnover=round(true_turnover, 2), true_health=health,
        true_honesty=honesty, declared_turnover=round(declared, 2), seed=seed,
        label_default=label_default, label_fraud=label_fraud,
        archetype=overrides.get("archetype"),
    )
