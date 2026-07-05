"""Filesystem locations for the Track-04 early-warning panel data.

`DATA_DIR` is the single module constant the Wave-2 ML agent (WP-4M) imports to
locate the CSVs — do not hard-code the path elsewhere. The directory lives
inside the track folder so `rm -rf app/tracks/t04_early_warning` removes the
track's data with it (multi-track isolation, README §1a).
"""
from __future__ import annotations

from pathlib import Path

# app/tracks/t04_early_warning/data/  (sibling of data_gen/)
DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# Panel CSVs (features live here; engine/runtime code reads only these three).
LOAN_BOOK_CSV = DATA_DIR / "loan_book.csv"
REPAYMENT_CSV = DATA_DIR / "repayment_history.csv"
ALTDATA_CSV = DATA_DIR / "altdata_monthly.csv"

# Eval-only ground truth (forward-looking default event + hidden ramp params).
# NEVER read by feature/serving code — labels only, for training/eval (WP-4M).
DEFAULT_LABELS_CSV = DATA_DIR / "default_labels.csv"

# name -> path, in the order build.py writes them.
CSV_PATHS = {
    "loan_book": LOAN_BOOK_CSV,
    "repayment_history": REPAYMENT_CSV,
    "altdata_monthly": ALTDATA_CSV,
    "default_labels": DEFAULT_LABELS_CSV,
}
