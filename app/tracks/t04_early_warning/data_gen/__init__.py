"""Track 04 · Early Warning — synthetic loan-book & monthly-panel data layer (WP-4D).

Wave-1 deliverable: a 24-month monthly panel grown out of the existing MSME
cohort (`app.data_gen`, imported read-only so entity_ids / archetypes / latents
match Track 03). Encodes the track thesis *by construction*: a borrower's
alt-data footprint (GST turnover, bank inflows, UPI counts, EPFO headcount,
energy) sags several months before repayment behaviour (DPD, bounces) reacts —
because repayment responds to *lagged* health while alt-data responds to health
immediately.

Public surface for the Wave-2 ML agent (WP-4M):
  * `paths` — module constants locating the emitted CSVs.
  * `build.build_panel(...)` / `build.write_panel(...)` — regenerate everything.
  * CSV schemas documented in `panel.SCHEMAS`.
"""
