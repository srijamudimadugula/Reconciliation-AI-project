import pandas as pd

def standardize_columns(df):
    df.columns = df.columns.str.strip().str.lower()
    return df

def normalize_customer(name):
    if pd.isna(name):
        return name
    return str(name).lower().strip().replace("-", "").replace(" ", "")

def load_data():
    marico = pd.read_csv("marico_ledger.csv")
    customer = pd.read_csv("customer_ledger.csv")

    marico = standardize_columns(marico)
    customer = standardize_columns(customer)

    marico = marico.rename(columns={
        "amount": "invoice_amount",
        "quantity": "invoice_qty"
    })

    customer = customer.rename(columns={
        "amount_paid": "paid_amount",
        "quantity_received": "received_qty"
    })
    required_marico = ["invoice_amount", "invoice_qty"]
    required_customer = ["paid_amount", "received_qty"]

    for col in required_marico:
        if col not in marico.columns:
            raise ValueError(f"Missing column in marico: {col}")

    for col in required_customer:
        if col not in customer.columns:
            raise ValueError(f"Missing column in customer: {col}")
    # Normalize customers
    marico["customer_clean"] = marico["customer"].apply(normalize_customer)
    customer["customer_clean"] = customer["customer"].apply(normalize_customer)

    return marico, customer