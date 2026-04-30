import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

# ── Config ───────────────────────────────────────────────────────────────────

CUSTOMERS = {
    "BigBasket": {
        "underpay_rate": 0.15,   # frequently underpays slightly
        "overpay_rate": 0.03,
        "missing_rate": 0.05,    # rarely goes missing
        "qty_dispute_rate": 0.08,
        "avg_amount": 14000,
        "avg_qty": 140,
    },
    "DMart": {
        "underpay_rate": 0.20,   # highest dispute rate
        "overpay_rate": 0.02,
        "missing_rate": 0.08,
        "qty_dispute_rate": 0.12,
        "avg_amount": 18000,
        "avg_qty": 180,
    },
    "Nykaa": {
        "underpay_rate": 0.10,
        "overpay_rate": 0.05,    # sometimes overpays (D2C quirk)
        "missing_rate": 0.04,
        "qty_dispute_rate": 0.06,
        "avg_amount": 7000,
        "avg_qty": 70,
    },
    "Reliance": {
        "underpay_rate": 0.08,   # fairly reliable
        "overpay_rate": 0.02,
        "missing_rate": 0.03,
        "qty_dispute_rate": 0.05,
        "avg_amount": 25000,
        "avg_qty": 250,
    },
    "Flipkart": {
        "underpay_rate": 0.18,
        "overpay_rate": 0.04,
        "missing_rate": 0.10,    # highest missing rate
        "qty_dispute_rate": 0.10,
        "avg_amount": 11000,
        "avg_qty": 110,
    },
}

START_DATE = datetime(2025, 10, 1)
NUM_INVOICES = 250

# ── Generate Marico ledger ────────────────────────────────────────────────────

def generate_marico_ledger():
    rows = []
    invoice_num = 1

    for i in range(NUM_INVOICES):
        customer = random.choices(list(CUSTOMERS.keys()), weights=[25, 25, 20, 15, 15])[0]
        cfg = CUSTOMERS[customer]

        date = START_DATE + timedelta(days=random.randint(0, 180))
        amount = max(1000, int(np.random.normal(cfg["avg_amount"], cfg["avg_amount"] * 0.2)))
        qty = max(10, int(np.random.normal(cfg["avg_qty"], cfg["avg_qty"] * 0.2)))

        rows.append({
            "invoice_id": f"INV{invoice_num:04d}",
            "customer": customer,
            "date": date.strftime("%Y-%m-%d"),
            "amount": amount,
            "quantity": qty,
        })
        invoice_num += 1

    return pd.DataFrame(rows)


# ── Generate Customer ledger (with realistic noise) ───────────────────────────

def generate_customer_ledger(marico_df):
    rows = []
    skipped = set()  # invoices that go "missing" in customer records

    for _, row in marico_df.iterrows():
        customer = row["customer"]
        cfg = CUSTOMERS[customer]
        invoice_id = row["invoice_id"]
        amount = row["amount"]
        qty = row["quantity"]

        roll = random.random()
        cumulative = 0

        # MISSING — invoice not in customer records at all
        cumulative += cfg["missing_rate"]
        if roll < cumulative:
            skipped.add(invoice_id)
            continue

        # UNDERPAYMENT — customer pays less
        cumulative += cfg["underpay_rate"]
        if roll < cumulative:
            shortfall_pct = random.uniform(0.03, 0.25)
            paid = round(amount * (1 - shortfall_pct), 2)
            rows.append({
                "invoice_id": invoice_id,
                "customer": customer,
                "date": row["date"],
                "amount_paid": paid,
                "quantity_received": qty,
            })
            continue

        # OVERPAYMENT — customer pays more
        cumulative += cfg["overpay_rate"]
        if roll < cumulative:
            excess_pct = random.uniform(0.01, 0.08)
            paid = round(amount * (1 + excess_pct), 2)
            rows.append({
                "invoice_id": invoice_id,
                "customer": customer,
                "date": row["date"],
                "amount_paid": paid,
                "quantity_received": qty,
            })
            continue

        # QUANTITY DISPUTE — qty received differs
        cumulative += cfg["qty_dispute_rate"]
        if roll < cumulative:
            qty_diff = random.randint(1, max(1, int(qty * 0.15)))
            received = max(1, qty - qty_diff)
            rows.append({
                "invoice_id": invoice_id,
                "customer": customer,
                "date": row["date"],
                "amount_paid": amount,
                "quantity_received": received,
            })
            continue

        # ROUNDING — tiny difference within tolerance
        cumulative += 0.05
        if roll < cumulative:
            rounding_error = random.uniform(-50, 50)
            rows.append({
                "invoice_id": invoice_id,
                "customer": customer,
                "date": row["date"],
                "amount_paid": round(amount + rounding_error, 2),
                "quantity_received": qty,
            })
            continue

        # MATCHED — perfect
        rows.append({
            "invoice_id": invoice_id,
            "customer": customer,
            "date": row["date"],
            "amount_paid": amount,
            "quantity_received": qty,
        })

    # Add a few EXTRA invoices in customer records (not in Marico)
    extra_count = 8
    for i in range(extra_count):
        customer = random.choice(list(CUSTOMERS.keys()))
        rows.append({
            "invoice_id": f"CUST_EXTRA_{i+1:03d}",
            "customer": customer,
            "date": (START_DATE + timedelta(days=random.randint(0, 180))).strftime("%Y-%m-%d"),
            "amount_paid": random.randint(3000, 20000),
            "quantity_received": random.randint(30, 200),
        })

    return pd.DataFrame(rows)


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Generating Marico ledger...")
    marico_df = generate_marico_ledger()
    marico_df.to_csv("marico_ledger.csv", index=False)
    print(f"  ✅ marico_ledger.csv — {len(marico_df)} rows")

    print("Generating Customer ledger...")
    customer_df = generate_customer_ledger(marico_df)
    customer_df.to_csv("customer_ledger.csv", index=False)
    print(f"  ✅ customer_ledger.csv — {len(customer_df)} rows")

    print("\nSummary:")
    print(f"  Total invoices (Marico)  : {len(marico_df)}")
    print(f"  Total invoices (Customer): {len(customer_df)}")
    print(f"  Missing from customer    : {len(marico_df) - (len(customer_df) - 8)}")
    print(f"  Extra in customer        : 8")
    print("\nDone. Run: streamlit run app.py")