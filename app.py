import streamlit as st
import pandas as pd
from data_loader import load_data
from reconciliation import preprocess, reconcile
from ai_module import explain, draft_email, ask_question

st.set_page_config(page_title="Marico Reconciliation AI", layout="wide")
st.title("📊 Marico Customer Reconciliation Dashboard")

# ── Load & process ──────────────────────────────────────────────────────────
@st.cache_data
def get_data():
    marico, customer = load_data()
    marico, customer = preprocess(marico, customer)
    df = reconcile(marico, customer)
    return df

df = get_data()

# ── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋 Dashboard", "🔍 Invoice Detail", "🤖 Ask AI"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — Dashboard
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Invoices", len(df))
    k2.metric("Mismatches", int(df["is_mismatch"].sum()))
    k3.metric("Escalations", int((df["action"] == "ESCALATE").sum()))
    total_disputed = df.loc[df["is_mismatch"], "amount_diff"].abs().sum()
    k4.metric("Total Disputed Amount", f"₹{total_disputed:,.0f}")

    st.divider()

    # Filters
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        customers = st.multiselect(
            "Filter by Customer",
            df["customer_clean"].unique(),
            default=list(df["customer_clean"].unique()),
        )
    with col_f2:
        categories = st.multiselect(
            "Filter by Category",
            df["category"].unique(),
            default=list(df["category"].unique()),
        )

    filtered = df[
        df["customer_clean"].isin(customers) & df["category"].isin(categories)
    ].copy()

    status_map = {
        "ESCALATE": "🔴 Escalate",
        "DISPUTE": "🟠 Dispute",
        "REVIEW": "🔵 Review",
        "ACCEPT": "🟢 Accept",
        "NO_ACTION": "⚪ No Action",
    }
    filtered["status"] = filtered["action"].map(status_map)

    st.subheader("Reconciliation Table")
    display_cols = [
        "invoice_id", "customer_clean", "invoice_amount", "paid_amount",
        "amount_diff", "qty_diff", "category", "status",
    ]
    existing_cols = [c for c in display_cols if c in filtered.columns]
    st.dataframe(filtered[existing_cols], use_container_width=True)

    # Category breakdown chart
    st.subheader("Category Breakdown")
    cat_counts = filtered["category"].value_counts().reset_index()
    cat_counts.columns = ["Category", "Count"]
    st.bar_chart(cat_counts.set_index("Category"))

    # Customer-wise disputed amount
    st.subheader("Disputed Amount by Customer")
    cust_dispute = (
        filtered[filtered["is_mismatch"]]
        .groupby("customer_clean")["amount_diff"]
        .apply(lambda x: x.abs().sum())
        .reset_index()
    )
    cust_dispute.columns = ["Customer", "Disputed Amount (₹)"]
    st.bar_chart(cust_dispute.set_index("Customer"))


# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — Invoice Detail + AI
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    invoice_id = st.selectbox("Select Invoice", df["invoice_id"].unique())
    selected = df[df["invoice_id"] == invoice_id]

    if selected.empty:
        st.warning("No data for this invoice.")
    else:
        row = selected.iloc[0]

        def safe(col):
            return row[col] if col in row.index else "N/A"

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Invoice Details**")
            st.json({
                "Customer": safe("customer_clean"),
                "Invoice Amount": f"₹{safe('invoice_amount'):,.2f}",
                "Paid Amount": f"₹{safe('paid_amount'):,.2f}",
                "Amount Difference": f"₹{safe('amount_diff'):,.2f}",
                "Qty Sent": int(safe("invoice_qty")) if safe("invoice_qty") != "N/A" else "N/A",
                "Qty Received": int(safe("received_qty")) if safe("received_qty") != "N/A" else "N/A",
                "Qty Difference": int(safe("qty_diff")) if safe("qty_diff") != "N/A" else "N/A",
                "Category": safe("category"),
                "Action": safe("action"),
            })

        with c2:
            st.markdown("**AI Assistant**")
            if st.button("🧠 Explain this mismatch"):
                with st.spinner("Thinking..."):
                    st.write(explain(row))

            if st.button("✉️ Draft resolution email"):
                with st.spinner("Drafting..."):
                    st.write(draft_email(row))


# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — RAG Chatbot
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("🤖 Ask anything about your reconciliation data")
    st.caption("Examples: 'Which customer has the most escalations?' / 'Show all underpayments' / 'Why is INV010 flagged?'")

    # df is passed directly to ask_question which builds a compact summary internally

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Display history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    question = st.chat_input("Ask a question about your reconciliation data...")

    if question:
        st.session_state.chat_history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.write(question)

        with st.chat_message("assistant"):
            with st.spinner("Analysing..."):
                answer = ask_question(question, df)
            st.write(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})