"""Compact feature functions for the remaining enrichment sources.

Each is small (single-row source) but feeds a pillar or a composite:
  udyam/pan_gstin -> Formal-Identity + Stability
  property_tax    -> Premises-Authenticity composite
  vahan/factory   -> Logistics / Production-Capacity composites
  gem/procurement -> B2G-Credibility composite
  courts/insolvency/mca21 -> Legal-Risk-Overlay composite
  itr/dgft        -> Turnover-Authenticity (secondary) / Export-Orientation
"""
from __future__ import annotations

import pandas as pd

from .base import feature_source


def _row(df: pd.DataFrame) -> dict:
    return {} if df is None or df.empty else df.iloc[0].to_dict()


@feature_source("udyam")
def udyam_features(df: pd.DataFrame, master_row: dict) -> dict:
    # Business age is an entity attribute (also on master) — the Stability anchor.
    return {"business_age_years": float(master_row.get("age_years", 0.0)),
            "udyam_registered": 1.0 if not (df is None or df.empty) else 0.0}


@feature_source("pan_gstin")
def pan_gstin_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {
        "identity_name_match": float(r.get("name_match_score", 0.0)),
        "gstin_active": 1.0 if r.get("gstin_status") == "active" else 0.0,
    }


@feature_source("property_tax")
def property_tax_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {
        "ptax_has_record": float(r.get("has_record", 0.0)),
        "ptax_address_matches_gst": float(r.get("address_matches_gst", 0.0)),
        "ptax_paid_current": float(r.get("tax_paid_current", 0.0)),
    }


@feature_source("vahan")
def vahan_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"vahan_num_vehicles": float(r.get("num_vehicles", 0.0)),
            "vahan_fitness_valid": float(r.get("fitness_valid", 1.0))}


@feature_source("factory_licence")
def factory_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"factory_has_licence": float(r.get("has_licence", 0.0)),
            "factory_sanctioned_workers": float(r.get("sanctioned_workers", 0.0))}


@feature_source("gem")
def gem_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"gem_is_seller": float(r.get("is_gem_seller", 0.0)),
            "gem_po_value": float(r.get("po_value", 0.0)),
            "gem_confirmed_po_count": float(r.get("confirmed_po_count", 0.0))}


@feature_source("procurement")
def procurement_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"proc_tenders_won": float(r.get("tenders_won", 0.0)),
            "proc_blacklisted": float(r.get("blacklisted", 0.0))}


@feature_source("courts")
def courts_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"court_cheque_bounce_cases": float(r.get("cheque_bounce_cases", 0.0)),
            "court_pending_cases": float(r.get("pending_cases", 0.0))}


@feature_source("insolvency")
def insolvency_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"insolvency_cirp_flag": float(r.get("cirp_flag", 0.0)),
            "insolvency_promoter_prior": float(r.get("promoter_prior_insolvency", 0.0))}


@feature_source("mca21")
def mca21_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"mca_has_record": float(r.get("has_mca_record", 0.0)),
            "mca_num_charges": float(r.get("num_charges", 0.0)),
            "mca_director_disqualified": float(r.get("director_disqualified", 0.0))}


@feature_source("itr")
def itr_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"itr_reported_income": float(r.get("reported_income", 0.0)),  # raw for authenticity
            "itr_filed_on_time": float(r.get("filed_on_time", 0.0))}


@feature_source("dgft")
def dgft_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"dgft_has_iec": float(r.get("has_iec", 0.0)),
            "dgft_export_value": float(r.get("export_value", 0.0))}


@feature_source("fssai")
def fssai_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"fssai_has_licence": float(r.get("has_licence", 0.0))}


@feature_source("pollution")
def pollution_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"pollution_has_consent": float(r.get("has_consent", 0.0))}


@feature_source("shops_establishment")
def shops_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"shops_registered": float(r.get("has_registration", 0.0))}


@feature_source("insurance")
def insurance_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"insurance_sum_insured": float(r.get("sum_insured", 0.0))}


@feature_source("ecommerce")
def ecommerce_features(df: pd.DataFrame, master_row: dict) -> dict:
    r = _row(df)
    return {"ecom_gmv": float(r.get("gmv", 0.0)),
            "ecom_return_rate": float(r.get("return_rate", 0.0))}
