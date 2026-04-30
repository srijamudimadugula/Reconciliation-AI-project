import os
from dotenv import load_dotenv

load_dotenv()

# Using Groq (free) instead of OpenAI
try:
    from groq import Groq
    groq_key = os.getenv("GROQ_API_KEY")
    client = Groq(api_key=groq_key) if groq_key else None
except ImportError:
    client = None


def _chat(prompt: str) -> str:
    """Single helper so we don't repeat the API call everywhere."""
    if not client:
        return "⚠️ Groq API key not set. Add GROQ_API_KEY to your .env file."
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=400,
    )
    return response.choices[0].message.content


def explain(row) -> str:
    prompt = f"""
You are a financial reconciliation analyst. Explain this invoice mismatch clearly and concisely.

Invoice ID   : {row.get('invoice_id', 'N/A')}
Customer     : {row.get('customer_clean', 'N/A')}
Amount Diff  : ₹{row.get('amount_diff', 0):,.2f}
Qty Diff     : {row.get('qty_diff', 0)}
Category     : {row.get('category', 'N/A')}
Action       : {row.get('action', 'N/A')}

Give a 3-sentence explanation: what the issue is, why it likely happened, and what the finance team should do next.
"""
    return _chat(prompt)


def draft_email(row) -> str:
    prompt = f"""
Draft a short, professional email from Marico's finance team to the customer regarding this reconciliation issue.

Invoice ID       : {row.get('invoice_id', 'N/A')}
Customer         : {row.get('customer_clean', 'N/A')}
Issue Type       : {row.get('category', 'N/A')}
Amount Difference: ₹{row.get('amount_diff', 0):,.2f}
Recommended Action: {row.get('action', 'N/A')}

Keep it under 120 words. Professional, polite, and action-oriented.
"""
    return _chat(prompt)


def build_summary(df) -> str:
    """Build a compact summary of reconciliation data to stay within token limits."""
    lines = []

    # Overall stats
    lines.append(f"Total invoices: {len(df)}")
    lines.append(f"Total mismatches: {int(df['is_mismatch'].sum())}")
    lines.append(f"Total disputed amount: ₹{df.loc[df['is_mismatch'], 'amount_diff'].abs().sum():,.0f}")

    # Per customer breakdown
    lines.append("\nPer-customer breakdown:")
    for cust, grp in df.groupby("customer_clean"):
        escalations = int((grp["action"] == "ESCALATE").sum())
        disputes = int((grp["action"] == "DISPUTE").sum())
        mismatches = int(grp["is_mismatch"].sum())
        disputed_amt = grp.loc[grp["is_mismatch"], "amount_diff"].abs().sum()
        lines.append(
            f"  {cust}: {len(grp)} invoices, {mismatches} mismatches, "
            f"{escalations} escalations, {disputes} disputes, ₹{disputed_amt:,.0f} disputed"
        )

    # Category counts
    lines.append("\nCategory counts:")
    for cat, count in df["category"].value_counts().items():
        lines.append(f"  {cat}: {count}")

    # Top 10 mismatches by amount
    lines.append("\nTop 10 mismatches by amount:")
    top = df[df["is_mismatch"]].nlargest(10, "amount_diff")[
        ["invoice_id", "customer_clean", "amount_diff", "qty_diff", "category", "action"]
    ]
    for _, r in top.iterrows():
        lines.append(
            f"  {r['invoice_id']} | {r['customer_clean']} | "
            f"₹{r['amount_diff']:,.0f} diff | {r['category']} | {r['action']}"
        )

    return "\n".join(lines)


def ask_question(question: str, df) -> str:
    """RAG-style Q&A over reconciliation data using a compact summary."""
    context = build_summary(df)
    prompt = f"""
You are a reconciliation assistant for Marico, an FMCG company.
Answer the user's question using only the summary data below.

--- RECONCILIATION SUMMARY ---
{context}
--- END SUMMARY ---

Question: {question}

Be specific. Use customer names, invoice IDs, and numbers from the data.
If the answer is not in the summary, say so clearly.
Keep your answer under 100 words.
"""
    return _chat(prompt)