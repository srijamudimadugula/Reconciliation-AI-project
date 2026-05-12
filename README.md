# Marico Customer Reconciliation

A Streamlit-based reconciliation dashboard for Marico customer invoices.

This repository compares Marico invoice data against customer payment records, categorizes mismatches, suggests actions, and offers AI-powered explanations and conversational summaries.

## Key features

- Load and normalize ledger files from `marico_ledger.csv` and `customer_ledger.csv`
- Reconcile invoices by `invoice_id` and normalized customer name
- Compute amount and quantity variances
- Classify reconciliation outcomes into categories like `MATCHED`, `UNDERPAYMENT`, `OVERPAYMENT`, `QUANTITY_DISPUTE`, `ROUNDING`, `MISSING_IN_CUSTOMER`, and `EXTRA_IN_CUSTOMER`
- Recommend actions including `NO_ACTION`, `ACCEPT`, `REVIEW`, `DISPUTE`, and `ESCALATE`
- Interactive Streamlit dashboard with filters, charts, and invoice detail views
- AI assistant for mismatch explanations, draft emails, and chat-style questions about the reconciliation data
- Sample ledger generator for synthetic test data

## Repository structure

- `app.py` - Main Streamlit application for the reconciliation dashboard and AI assistant
- `data_loader.py` - CSV loading, standardization, column normalization, and customer cleanup
- `reconciliation.py` - Preprocessing and reconciliation logic with thresholds and action rules
- `ai_module.py` - AI helpers for explanation, email drafting, and RAG-style question answering using Groq
- `config.py` - Tolerance thresholds and escalation multiplier configuration
- `generate_data.py` - Synthetic sample data generator for `marico_ledger.csv` and `customer_ledger.csv`
- `test_pipeline.py` - Simple schema validation pipeline test
- `marico_ledger.csv` - Sample Marico invoice ledger
- `customer_ledger.csv` - Sample customer payment ledger
- `requirements.txt` - Python dependencies

## Getting started

1. Create and activate a Python virtual environment

```powershell
python -m venv venv
.\venv\Scripts\Activate
```

2. Install dependencies

```powershell
pip install -r requirements.txt
```

3. Provide your Groq API key for AI features

Create a `.env` file in the repository root containing:

```env
GROQ_API_KEY=your_groq_api_key_here
```

If the key is missing or the `groq` package is not installed, the AI features will display a warning message instead of failing.

4. Generate sample ledgers (optional)

This creates or refreshes `marico_ledger.csv` and `customer_ledger.csv`.

5. Run the dashboard

```powershell
streamlit run app.py
```

6. Open the app

Visit `http://localhost:8501` in your browser.

## Data expectations

`data_loader.py` expects the following columns:

- `marico_ledger.csv`
  - `invoice_id`
  - `customer`
  - `date`
  - `amount` (renamed internally to `invoice_amount`)
  - `quantity` (renamed internally to `invoice_qty`)

- `customer_ledger.csv`
  - `invoice_id`
  - `customer`
  - `date`
  - `amount_paid`
  - `quantity_received`

Customer names are normalized by lowercasing, trimming spaces, and removing hyphens.

## Notes

- The main dashboard app uses `app.py`.

