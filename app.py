import streamlit as st
from data_loader import load_data
from reconciliation import preprocess, reconcile
from ai_module import explain, draft_email

st.set_page_config(page_title="Reconciliation AI", layout="wide")
st.title("📊 Marico Customer Reconciliation Dashboard")

# Load + process
marico, customer = load_data()
marico, customer = preprocess(marico, customer)
df = reconcile(marico, customer)

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total Invoices", len(df))
col2.metric("Mismatches", int(df["is_mismatch"].sum()))
col3.metric("Escalations", int((df["action"] == "ESCALATE").sum()))

# Filters
st.sidebar.header("Filters")

customers = st.sidebar.multiselect(
    "Customer",
    df["customer_clean"].unique(),
    default=df["customer_clean"].unique()
)

categories = st.sidebar.multiselect(
    "Category",
    df["category"].unique(),
    default=df["category"].unique()
)

filtered = df[
    (df["customer_clean"].isin(customers)) &
    (df["category"].isin(categories))
].copy()

# Safe assignment
filtered.loc[:, "status"] = filtered["action"].map({
    "ESCALATE": "🔴 Escalate",
    "DISPUTE": "🟠 Dispute",
    "REVIEW": "🔵 Review",
    "ACCEPT": "🟢 Accept",
    "NO_ACTION": "⚪ No Action"
})

# Table
st.subheader("📋 Reconciliation Table")
st.dataframe(filtered, use_container_width=True)

# Detail view
st.subheader("🔍 Invoice Details")

invoice = st.selectbox("Select Invoice", filtered["invoice_id"])
selected = filtered[filtered["invoice_id"] == invoice]

if selected.empty:
    st.warning("No data for selected invoice")
else:
    row = selected.iloc[0]
def safe_get(row, col):
    return row[col] if col in row else 0
st.json({
    "Customer": safe_get(row, "customer_clean"),
    "Invoice Amount": safe_get(row, "invoice_amount"),
    "Paid Amount": safe_get(row, "paid_amount"),
    "Quantity Sent": safe_get(row, "invoice_qty"),
    "Quantity Received": safe_get(row, "received_qty"),
    "Amount Difference": safe_get(row, "amount_diff"),
    "Quantity Difference": safe_get(row, "qty_diff"),
    "Category": safe_get(row, "category"),
    "Action": safe_get(row, "action")
})

# AI Assistant
st.subheader("🧠 AI Assistant")

col1, col2 = st.columns(2)

with col1:
    if st.button("Explain Mismatch"):
        st.write(explain(row))

with col2:
    if st.button("Draft Email"):
        st.write(draft_email(row))