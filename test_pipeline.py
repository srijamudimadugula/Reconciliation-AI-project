from data_loader import load_data
from reconciliation import preprocess, reconcile

marico, customer = load_data()
marico, customer = preprocess(marico, customer)
df = reconcile(marico, customer)


print("\nCOLUMNS:")
print(df.columns)

print("\nHEAD:")
print(df.head())
expected_cols = [
    "invoice_id",
    "customer_clean",
    "invoice_amount",
    "paid_amount",
    "amount_diff",
    "qty_diff",
    "category",
    "action",
    "is_mismatch"
]

missing = [c for c in expected_cols if c not in df.columns]

if missing:
    print("❌ Missing columns:", missing)
else:
    print("✅ Schema OK")