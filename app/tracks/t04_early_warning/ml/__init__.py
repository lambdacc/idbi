"""Track-04 early-warning ML layer (WP-4M): causal snapshot features, the
EWSEngine (monotonic GBM + calibration, vs a repayment-only baseline), and the
lead-time eval scorecard. Imports the platform ML kit read-only; owns its own
prefit pickle inside the track folder (multi-track isolation)."""
from .model import EWSEngine, EWS_PICKLE, get_engine, prefit, warm  # noqa: F401
