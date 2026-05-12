import pandas as pd
import numpy as np
from config import THRESHOLDS, DEFAULT_THRESHOLD, ESCALATION_MULTIPLIER


def preprocess(marico, customer):

    marico_cols = ["invoice_amount", "invoice_qty"]
    for col in marico_cols:
        if col in marico.columns:
            marico[col] = pd.to_numeric(marico[col], errors="coerce").fillna(0)

    customer_cols = ["paid_amount", "received_qty"]
    for col in customer_cols:
        if col in customer.columns:
            customer[col] = pd.to_numeric(customer[col], errors="coerce").fillna(0)

    marico = marico.groupby(["invoice_id", "customer_clean"], as_index=False).sum()
    customer = customer.groupby(["invoice_id", "customer_clean"], as_index=False).sum()

    return marico, customer


def reconcile(marico, customer):

    merged = pd.merge(
        marico,
        customer,
        on=["invoice_id", "customer_clean"],
        how="outer",
        indicator=True
    )

    print("After merge:", merged.shape)
    print("Columns after merge:", merged.columns)

    merged = merged.fillna(0)

    # Safety for missing columns
    for col in ["invoice_amount", "paid_amount", "invoice_qty", "received_qty"]:
        if col not in merged.columns:
            merged[col] = 0

    # Differences
    merged["amount_diff"] = merged["invoice_amount"] - merged["paid_amount"]
    merged["qty_diff"] = merged["invoice_qty"] - merged["received_qty"]

    # Thresholds
    merged["tolerance"] = DEFAULT_THRESHOLD
    for idx, row in merged.iterrows():
        customer = row["customer_clean"]
        if customer in THRESHOLDS:
            merged.at[idx, "tolerance"] = THRESHOLDS[customer]
    merged["tolerance_value"] = merged["invoice_amount"] * merged["tolerance"]
   
    # Classification
    conditions = [
        merged["_merge"] == "left_only",
        merged["_merge"] == "right_only",
        (merged["amount_diff"] == 0) & (merged["qty_diff"] == 0),
        
        np.abs(merged["amount_diff"]) <= merged["tolerance_value"],
        merged["qty_diff"] != 0,
        merged["amount_diff"] > 0,
        merged["amount_diff"] < 0
    ]

    choices = [
        "MISSING_IN_CUSTOMER",
        "EXTRA_IN_CUSTOMER",
        "MATCHED",
        "QUANTITY_DISPUTE",
        "ROUNDING",
        "UNDERPAYMENT",
        "OVERPAYMENT"
    ]

    merged["category"] = np.select(conditions, choices, default="REVIEW")

    print("After classification:", merged.shape)

    # Action
    conditions_action = [
        merged["category"] == "MATCHED",
        merged["category"] == "ROUNDING",
        merged["category"].isin(["MISSING_IN_CUSTOMER", "EXTRA_IN_CUSTOMER"]),
        merged["category"] == "QUANTITY_DISPUTE",
        np.abs(merged["amount_diff"]) > merged["tolerance"] * ESCALATION_MULTIPLIER
    ]

    choices_action = [
        "NO_ACTION",
        "ACCEPT",
        "ESCALATE",
        "DISPUTE",
        "ESCALATE"
    ]

    merged["action"] = np.select(conditions_action, choices_action, default="REVIEW")

    # Mismatch flag (CRITICAL)
    merged["is_mismatch"] = (
        (merged["_merge"] != "both") |
        (np.abs(merged["amount_diff"]) > merged["tolerance"]) |
        (merged["qty_diff"] != 0)
    )

    # Output contract validation
    required_cols = ["category", "action", "is_mismatch"]
    for col in required_cols:
        if col not in merged.columns:
            raise ValueError(f"{col} missing from reconcile output")

    return merged
