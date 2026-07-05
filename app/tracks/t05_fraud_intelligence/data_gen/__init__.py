"""SentinelPulse (Track 05) synthetic fraud data layer — WP-5D.

Public surface for Wave-2 (WP-5M detection engine) and the tests:

  * ``DATA_DIR``          where the three CSVs land
  * ``ACCOUNTS_CSV`` / ``TRANSACTIONS_CSV`` / ``GROUND_TRUTH_CSV``  filenames
  * ``build_all()``       build + write the dataset
  * ``build_tables()``    build in-memory (no write)

Build the dataset from the CLI::

    python -m app.tracks.t05_fraud_intelligence.data_gen.build
"""
from __future__ import annotations

from .build import (ACCOUNTS_CSV, DATA_DIR, GROUND_TRUTH_CSV, TRANSACTIONS_CSV,
                    build_all, build_tables, write_csvs)
from .fraud_profiles import FRAUD_SEED

__all__ = [
    "DATA_DIR", "ACCOUNTS_CSV", "TRANSACTIONS_CSV", "GROUND_TRUTH_CSV",
    "FRAUD_SEED", "build_all", "build_tables", "write_csvs",
]
