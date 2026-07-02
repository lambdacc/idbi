"""MSME distribution profile for India — direct generator parameters.

Every figure here traces to appendix-b-synthetic-data-plan.md §1.10, which tags
each as (sourced: citation) or (assumed: reasoning). This module is the single
source of calibration truth for all generators in data_gen/generators/.
"""
from __future__ import annotations

# --- Category (Micro/Small/Medium) ---  (assumed blended midpoints, Appx-B §1.1)
CATEGORY_WEIGHTS = {"Micro": 0.96, "Small": 0.033, "Medium": 0.007}

# --- Turnover bands (annual, INR) with population weights (Appx-B §1.10) ---
# (lo, hi) in INR, weight is share of ALL MSMEs.
TURNOVER_BANDS = [
    (0,            1_000_000,   0.50),   # < 10L
    (1_000_000,    10_000_000,  0.39),   # 10L - 1cr
    (10_000_000,   50_000_000,  0.07),   # 1cr - 5cr
    (50_000_000,   150_000_000, 0.020),  # 5cr - 15cr
    (150_000_000,  300_000_000, 0.010),  # 15cr - 30cr
    (300_000_000,  500_000_000, 0.003),  # 30cr - 50cr
    (500_000_000,  1_000_000_000, 0.0039),  # 50cr - 100cr
    (1_000_000_000, 1_750_000_000, 0.0021), # 100cr - 175cr
    (1_750_000_000, 2_500_000_000, 0.0010), # 175cr - 250cr
]

# --- Sector weights (blend of Udyam-registered + NSS broader, Appx-B §1.10) ---
SECTOR_WEIGHTS = {"Trade": 0.40, "Services": 0.34, "Manufacturing": 0.26}

# --- State weights (top 7 + tail, Appx-B §1.10) ---
STATE_WEIGHTS = {
    "Maharashtra": 0.110, "Uttar Pradesh": 0.089, "Tamil Nadu": 0.067,
    "West Bengal": 0.059, "Gujarat": 0.060, "Karnataka": 0.056,
    "Rajasthan": 0.050, "Other": 0.509,
}

# --- Urban/rural (Udyam-registered-only assumed skew, Appx-B §1.10) ---
URBAN_RURAL_WEIGHTS = {"Urban": 0.55, "Rural": 0.45}

# --- Age/vintage bands in years (assumed, Appx-B §1.6) ---
AGE_BANDS = [(0, 3, 0.18), (3, 10, 0.40), (10, 35, 0.42)]

# --- Employee-count bands by category (Appx-B §1.10) ---
# list of (lo, hi, weight)
EMPLOYEE_BANDS = {
    "Micro":  [(0, 0, 0.40), (1, 9, 0.50), (10, 49, 0.08), (50, 80, 0.02)],
    "Small":  [(0, 0, 0.02), (1, 9, 0.20), (10, 49, 0.55), (50, 120, 0.23)],
    "Medium": [(10, 49, 0.10), (50, 99, 0.25), (100, 199, 0.35), (200, 400, 0.30)],
}

# --- GST-registration probability by turnover band ceiling (Appx-B §1.10) ---
# (turnover_upper_bound, probability)
GST_REG_PROB = [
    (1_000_000, 0.05), (2_000_000, 0.12), (4_000_000, 0.45),
    (10_000_000, 0.88), (50_000_000, 0.97), (float("inf"), 0.99),
]

# --- Digital-adoption probability by turnover band ceiling (Appx-B §1.10) ---
DIGITAL_ADOPTION_PROB = [
    (1_000_000, 0.45), (10_000_000, 0.75), (50_000_000, 0.90), (float("inf"), 0.96),
]

# --- Women-owned probability (Appx-B §1.9) — "led" definition ---
WOMEN_OWNED_PROB = 0.39

# --- Baseline default/NPA anchors (Appx-B §1.8/§1.10) ---
# Broad bureau/NBFC-inclusive basis; skewed upward for thin-file/unregistered.
BASE_DEFAULT_RATE = 0.09

# Probability a Micro unit is incorporated (company/LLP vs proprietorship).
# Most Micro units are proprietorships (assumed; MCA21 excludes proprietorships).
INCORPORATION_PROB = {"Micro": 0.05, "Small": 0.35, "Medium": 0.80}

# GST filing months of history modelled per entity.
GST_HISTORY_MONTHS = 18
BANK_HISTORY_MONTHS = 18
