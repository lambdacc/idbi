"""Track-05 session / cache helpers (in-track per isolation §1a).

Keeps the fraud engine and the transactions table cached, and owns the two
Track-05 session keys:

  * ``cp_case_account`` — the account the desk handed to Case Investigation;
  * ``cp_case_audit``   — the ordinal, wall-clock-free audit trail of analyst
                          approve / override decisions.

The audit logic (``append_audit``) is a PURE function over a plain list so it is
unit-testable with no Streamlit import; the ``record_decision`` wrapper just binds
it to ``st.session_state``.
"""
from __future__ import annotations

from typing import List, Optional

import pandas as pd
import streamlit as st

from .data_gen import DATA_DIR, TRANSACTIONS_CSV
from .ml.model import get_engine as _get_engine

CASE_ACCOUNT_KEY = "cp_case_account"
CASE_AUDIT_KEY = "cp_case_audit"


@st.cache_resource(show_spinner="Fitting the fraud-detection engine on the "
                   "synthetic ledger (one time, a few seconds).")
def get_fraud_engine():
    """Cached fitted FraudEngine singleton (pre-fit pickle when fresh)."""
    return _get_engine()


@st.cache_data(show_spinner=False)
def load_transactions() -> pd.DataFrame:
    """The transactions ledger, indexed by txn_id for fast citation lookups.

    This is an engine INPUT (never the labels file); pages read it only to show
    the concrete transactions a ground of suspicion cites."""
    df = pd.read_csv(DATA_DIR / TRANSACTIONS_CSV)
    df["txn_id"] = df["txn_id"].astype(str)
    df["account_id"] = df["account_id"].astype(str)
    df["counterparty_id"] = df["counterparty_id"].astype(str)
    return df.set_index("txn_id", drop=False)


# ------------------------------------------------------------- case selection
def set_case_account(account_id: str) -> None:
    st.session_state[CASE_ACCOUNT_KEY] = account_id


def get_case_account() -> Optional[str]:
    return st.session_state.get(CASE_ACCOUNT_KEY)


def has_case_account() -> bool:
    return bool(st.session_state.get(CASE_ACCOUNT_KEY))


# ------------------------------------------------------------- audit trail
def append_audit(audit: List[dict], account_id: str, action: str,
                 recommendation: str, note: str = "") -> List[dict]:
    """Append one ordinal audit entry (NO wall-clock — tests stay deterministic).

    Pure: takes and returns the list, so it is testable with no Streamlit. The
    ordinal ``n`` is 1-based and monotonic in append order."""
    entry = {
        "n": len(audit) + 1,
        "account": account_id,
        "action": action,                 # "Approved" | "Overridden"
        "recommendation": recommendation,
        "note": note,
    }
    audit.append(entry)
    return audit


def record_decision(account_id: str, action: str, recommendation: str,
                    note: str = "") -> None:
    """Bind ``append_audit`` to the session-state audit list."""
    audit = st.session_state.get(CASE_AUDIT_KEY)
    if not isinstance(audit, list):
        audit = []
    append_audit(audit, account_id, action, recommendation, note)
    st.session_state[CASE_AUDIT_KEY] = audit


def get_audit() -> List[dict]:
    audit = st.session_state.get(CASE_AUDIT_KEY)
    return audit if isinstance(audit, list) else []
