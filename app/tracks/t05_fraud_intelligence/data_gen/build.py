"""Build the SentinelPulse synthetic transaction universe (Track 05, WP-5D).

Entry point for the Track-05 fraud dataset. Writes three CSVs to ``DATA_DIR``:

  * ``accounts.csv``            engine input — account_id, type, open_date,
                                kyc_income_band, linked_entity_id (nullable)
  * ``transactions.csv``        engine input — 90 days of the account ledger
  * ``fraud_ground_truth.csv``  EVAL / TESTS ONLY — is_mule, ring_id, role,
                                is_hard_negative, typologies_expressed.
                                NEVER read by scoring/runtime code at score time.

Run it with::

    python -m app.tracks.t05_fraud_intelligence.data_gen.build

Deterministic under ``FRAUD_SEED``: same seed -> byte-identical CSVs.
"""
from __future__ import annotations

import argparse
from datetime import timedelta
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd

from . import typologies as T
from .fraud_profiles import (AS_OF, FRAUD_SEED, AccountProfile, ROLE_CASHOUT,
                             ROLE_HARDNEG, ROLE_LEGIT, ROLE_MULE, ROLE_RECRUITER,
                             build_universe)
from .legit import gen_hard_negative, gen_legit
from .typologies import pick_channel, rand_dt, txn

# --- output locations (module constants — Wave-2 WP-5M locates outputs here) ---
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
ACCOUNTS_CSV = "accounts.csv"
TRANSACTIONS_CSV = "transactions.csv"
GROUND_TRUTH_CSV = "fraud_ground_truth.csv"


# --------------------------------------------------------------------------- #
# per-account transaction emission
# --------------------------------------------------------------------------- #
def _emit_account_rows(acc: AccountProfile, rings: Dict[str, dict]) -> List[dict]:
    """Raw rows (no account_id/txn_id/balance) for one account by role."""
    rows: List[dict] = []
    if acc.role == ROLE_MULE:
        ring = rings[acc.ring_id]
        for name in acc.typologies:
            injector = T.INJECTORS.get(name)
            if injector is not None:
                # deterministic per-typology salt (never Python's randomized hash)
                salt = 100 + T.ALL_TYPOLOGIES.index(name)
                rows.extend(injector(acc, ring, acc.rng(salt)))
    elif acc.role in (ROLE_RECRUITER, ROLE_CASHOUT):
        ring = rings[acc.ring_id]
        rng = acc.rng(7)
        rows.extend(gen_legit(acc, acc.rng(3)))  # thin legit cover
        dev = ring["device"]
        if acc.role == ROLE_CASHOUT:
            # cash extraction: ATM/POS withdrawals on the ring device
            for _ in range(int(rng.integers(6, 13))):
                amt = float(rng.uniform(8_000, 30_000))
                rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end), "debit",
                                amt, "ATM" if rng.random() < 0.7 else "POS",
                                "ATM-CASH", dev))
        else:  # recruiter forwards onward to its cash-out endpoints
            for _ in range(int(rng.integers(4, 9))):
                amt = float(rng.uniform(10_000, 40_000))
                tgt = str(rng.choice(ring["cashouts"]))
                rows.append(txn(rand_dt(rng, acc.active_start, acc.active_end), "debit",
                                amt, pick_channel(rng, amt), tgt, dev))
    elif acc.role == ROLE_HARDNEG:
        rows.extend(gen_hard_negative(acc, acc.rng(5)))
    else:  # ROLE_LEGIT
        rows.extend(gen_legit(acc, acc.rng(5)))
    return rows


def _mirror_intra_transfers(rows: List[dict], universe: set) -> List[dict]:
    """Double-entry the intra-universe transfers so ring targets get their side.

    A mule debit to a ring account (counterparty in ``universe``) becomes a credit
    on that account (and vice-versa), carrying the SAME device_id so the shared
    device spans the whole ring. Only original rows are mirrored (no cascade).
    """
    mirrors: List[dict] = []
    for r in rows:
        cp = r["counterparty_id"]
        if cp in universe and cp != r["account_id"]:
            opp = "credit" if r["direction"] == "debit" else "debit"
            mirrors.append(dict(
                account_id=cp, datetime=min(r["datetime"] + timedelta(seconds=2), AS_OF),
                direction=opp, amount=r["amount"], channel=r["channel"],
                counterparty_id=r["account_id"], device_id=r["device_id"]))
    return mirrors


def build_tables(seed: int = FRAUD_SEED) -> Dict[str, pd.DataFrame]:
    """Return {'accounts', 'transactions', 'fraud_ground_truth'} DataFrames."""
    accounts, rings = build_universe(seed)
    universe = set(accounts.keys())

    all_rows: List[dict] = []
    for aid, acc in accounts.items():
        for r in _emit_account_rows(acc, rings):
            r["account_id"] = aid
            all_rows.append(r)
    all_rows.extend(_mirror_intra_transfers(all_rows, universe))

    tx = pd.DataFrame(all_rows,
                      columns=["datetime", "account_id", "counterparty_id",
                               "direction", "amount", "channel", "device_id"])
    # running balance per account (opening floored so balance stays >= 1000)
    tx["_signed"] = np.where(tx["direction"] == "credit", tx["amount"], -tx["amount"])
    tx = tx.sort_values(["account_id", "datetime"], kind="mergesort").reset_index(drop=True)
    tx["_cum"] = tx.groupby("account_id")["_signed"].cumsum()
    floor = tx.groupby("account_id")["_cum"].transform("min").clip(upper=0.0)
    tx["balance_after"] = (1_000.0 - floor + tx["_cum"]).round(2)

    # stable global txn_id after ordering by time
    tx = tx.sort_values(["datetime", "account_id", "direction"],
                        kind="mergesort").reset_index(drop=True)
    tx.insert(0, "txn_id", [f"TXN{i:07d}" for i in range(1, len(tx) + 1)])
    tx["datetime"] = tx["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    tx = tx[["txn_id", "datetime", "account_id", "counterparty_id", "direction",
             "amount", "channel", "device_id", "balance_after"]]

    acc_df = pd.DataFrame([
        dict(account_id=a.account_id, account_type=a.account_type,
             open_date=a.open_date.strftime("%Y-%m-%d"),
             kyc_income_band=a.kyc_income_band,
             linked_entity_id=(a.linked_entity_id if a.linked_entity_id else ""))
        for a in accounts.values()
    ]).sort_values("account_id").reset_index(drop=True)

    gt_df = pd.DataFrame([
        dict(account_id=a.account_id, is_mule=a.is_mule,
             ring_id=(a.ring_id if a.ring_id else ""), role=a.role,
             is_hard_negative=a.is_hard_negative,
             typologies_expressed=";".join(a.typologies))
        for a in accounts.values()
    ]).sort_values("account_id").reset_index(drop=True)

    return {"accounts": acc_df, "transactions": tx, "fraud_ground_truth": gt_df}


def write_csvs(tables: Dict[str, pd.DataFrame], data_dir: Path = DATA_DIR) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    tables["accounts"].to_csv(data_dir / ACCOUNTS_CSV, index=False)
    tables["transactions"].to_csv(data_dir / TRANSACTIONS_CSV, index=False)
    tables["fraud_ground_truth"].to_csv(data_dir / GROUND_TRUTH_CSV, index=False)


def build_all(seed: int = FRAUD_SEED, data_dir: Path = DATA_DIR) -> Dict[str, pd.DataFrame]:
    """Build everything and write the three CSVs. Returns the DataFrames."""
    tables = build_tables(seed)
    write_csvs(tables, data_dir)
    return tables


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate SentinelPulse fraud dataset")
    ap.add_argument("--seed", type=int, default=FRAUD_SEED)
    ap.add_argument("--out", type=str, default=str(DATA_DIR))
    args = ap.parse_args()

    tables = build_all(args.seed, Path(args.out))
    gt = tables["fraud_ground_truth"]
    tx = tables["transactions"]
    print(f"Accounts:     {len(tables['accounts']):6d}")
    print(f"Transactions: {len(tx):6d} rows  "
          f"(window ending {AS_OF.date()}, 90 days)")
    print(f"Mules:        {int(gt['is_mule'].sum()):6d}  "
          f"(rate {gt['is_mule'].mean():.3f})")
    print(f"Rings:        {gt.loc[gt['ring_id'] != '', 'ring_id'].nunique():6d}")
    print(f"Hard negs:    {int(gt['is_hard_negative'].sum()):6d}")
    print(f"Written to:   {args.out}")


if __name__ == "__main__":
    main()
