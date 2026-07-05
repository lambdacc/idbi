"""Track-05 glossary (in-track per isolation §1a).

Plain-language definitions for the fraud-desk jargon, imported by the pages so
tooltip copy stays consistent and every technical term has a simple synonym
(design decision D7). Each entry is <= 25 words, aimed at bank fraud-ops users.
"""
from __future__ import annotations

from typing import Dict

GLOSSARY: Dict[str, str] = {
    "mule_account": (
        "An account rented out (or sold) so someone else can move stolen money "
        "through it — the account holder is a front, not the real owner."
    ),
    "str": (
        "Suspicious-transaction report — the formal filing a bank sends the "
        "financial-intelligence unit when an account looks like it is being misused."
    ),
    "typology": (
        "A named behavioural pattern that tends to indicate account misuse — for "
        "example money passing straight through, or amounts kept just under limits."
    ),
    "pass_through": (
        "Money that arrives and is forwarded on almost immediately, so the balance "
        "never really rests — a sign the account is only a conduit."
    ),
    "structuring": (
        "Splitting money into amounts kept just under a reporting limit so no single "
        "transaction trips a mandatory report."
    ),
    "ring": (
        "A group of accounts operated together to move money — typically collectors, "
        "forwarding hubs and cash-out points, often sharing a device."
    ),
    "cash_out": (
        "The point where laundered money leaves the banking system as cash — usually "
        "repeated ATM or point-of-sale withdrawals."
    ),
    "citation_gate": (
        "The rule that no claim of suspicion is made unless it points to specific "
        "real transactions you can open and read."
    ),
    "anomaly_leg": (
        "An independent check that learns what normal account behaviour looks like "
        "and flags accounts that don't fit — no fraud labels needed."
    ),
}
