# FinPulse AI - Production Web Application

FinPulse AI is a real-life personal financial intelligence engine built with a FastAPI backend, PostgreSQL database, PyTorch LSTM time-series forecaster, Scikit-learn Isolation Forest anomaly detector, EasyOCR receipt scanner, Google Gemini + LangChain financial advisor, and a React + Vite + TypeScript + Tailwind + Recharts frontend.

---

## Architecture & Stack

- **Backend**: Python 3.12, FastAPI, SQLAlchemy 2.x (async), Psycopg 3, Pydantic Settings, Uvicorn
- **Database**: PostgreSQL (`finpulse` database, automatic schema migrations via SQLAlchemy `create_all`)
- **Plaid Integration**: Official `plaid-python` SDK, Sandbox banking environment (`ins_109508`), background auto-synchronization every 2 minutes
- **Machine Learning**:
  - **PyTorch LSTM**: Autoregressive neural time-series forecaster trained automatically when expense history spans >= 60 days, with checkpoint persistence in `backend/model_checkpoints/`
  - **Scikit-learn Isolation Forest**: Multivariate anomaly detection flagging unusual expenditures and velocity spikes when ledger has >= 30 transactions
- **Receipt OCR**: EasyOCR (CPU mode) with intelligent total/merchant/date parsing and interactive pre-fill
- **AI Financial Advisor**: Google Gemini via LangChain (`langchain-google-genai`), contextualized directly with verified ledger balances, top categories, and pending unusual transactions
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Recharts, Axios, React Router v6

---

## Environment Configuration

A root `.env` file is required. The application reads configuration exclusively through Pydantic Settings and validates all required variables on startup.

### Environment Variable Names:
- `APP_ENV`
- `APP_DEBUG`
- `APP_SECRET_KEY`
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `GOOGLE_API_KEY`
- `GEMINI_MODEL` (optional, default: `gemini-1.5-flash`)
- `PLAID_CLIENT_ID`
- `PLAID_SECRET`
- `PLAID_ENV`
- `LOG_LEVEL`
- `OPENAI_API_KEY` (optional)

> Refer to `.env.example` for placeholder templates. Never commit `.env` or print/expose real secrets.

---

## Running the Application

### 1. Backend Server
Open PowerShell in the project root:
```powershell
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --app-dir backend
```
*(On Windows with Python 3.12 / Psycopg 3 async, you can also run: `python run_server.py`)*

- API Base URL: `http://localhost:8000`
- Interactive API Documentation (Swagger): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 2. Frontend Development Server
In a separate terminal:
```bash
cd frontend
npm run dev
```
- Web Application URL: `http://localhost:5173`

---

## Core Capabilities & Real-Life Flow

1. **User Authentication & Privacy**: Secure JWT authentication; users strictly see only their own financial data.
2. **Load Sample Data**: Single button generates ~6 months of realistic synthetic transactions directly in code (`source="sample_data"`). Refuses duplicate generation (HTTP 409 Conflict) once loaded.
3. **Plaid Sandbox Banking**:
   - Connect sandbox bank account (`ins_109508`) with one click (no Plaid Link UI needed).
   - Syncs transactions with cursor tracking; deduplicates on `plaid_transaction_id`.
   - Positive Plaid amounts correctly treated as money leaving the account (expenses).
   - "Simulate a purchase" creates everyday and occasional large transactions, triggering instant sync.
   - Background daemon syncs every connected item every 2 minutes.
4. **Receipt Scanner (EasyOCR)**:
   - Upload receipt image (JPG/PNG/WebP up to 5 MB).
   - Parses totals, merchants, dates, and categories.
   - Interactive review form allows adjustments before saving with `source="receipt_ocr"`.
5. **Automatic Model Training**:
   - PyTorch LSTM trains automatically when expense history spans >= 60 days, retrains when record count changes >= 20%, and saves checkpoints.
   - Isolation Forest fits automatically when transaction count >= 30, labeling unusual items with non-fraud vocabulary ("unusual", "suspicious").
   - `GET /api/models/status` monitors operational readiness.
6. **AI Financial Advisor**:
   - Answers questions using real-time ledger context without hallucinations.
   - Includes quick-prompt buttons for spending analysis and budget risk assessments.

---

## Verification Test Suite

Run the full end-to-end verification suite:
```powershell
.\.venv\Scripts\python.exe backend\tests\test_live_system_v2.py
```
Validates all 17 integration checkpoints end-to-end.
