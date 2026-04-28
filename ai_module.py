import os
from dotenv import load_dotenv

load_dotenv()
try:
    from openai import OpenAI
    client = OpenAI() if os.getenv("OPENAI_API_KEY") else None
except:
    client = None


def explain(row):
    if not client:
        return f"{row['category']} detected. Action: {row['action']}."

    prompt = f"""
    Explain this reconciliation issue:

    Invoice: {row['invoice_id']}
    Customer: {row['customer_clean']}
    Amount Diff: {row['amount_diff']}
    Qty Diff: {row['qty_diff']}
    Category: {row['category']}
    Action: {row['action']}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )

    return response.choices[0].message.content


def draft_email(row):
    if not client:
        return f"Please review invoice {row['invoice_id']} due to {row['category']}."

    prompt = f"""
    Draft a professional email:

    Invoice: {row['invoice_id']}
    Issue: {row['category']}
    Amount Difference: {row['amount_diff']}
    """

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    return response.choices[0].message.content
    