# Run ATHL Data Platform on a New Computer

This guide is the fastest way to run this project from a fresh machine.

## 1) Prerequisites

- Git
- Python 3.11+ (3.13 is also fine)
- Access to a PostgreSQL database (local Postgres or Neon)
- OpenAI API key

## 2) Clone and open project

```bash
git clone <YOUR_REPO_URL>
cd athl-data-platform
```

## 3) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 4) Install dependencies

```bash
pip install -r requirements.txt
```

## 5) Create `.env` in project root

Create a file named `.env` at the repository root with:

```env
OPENAI_API_KEY=sk-...

# local (default) or prod
DB_ENV=local

# Used when Streamlit secrets are not available (CLI/local fallback)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_db_name
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
```

Notes:

- `DB_ENV=local` uses local schema mode and persistent Chroma at `./chroma_db`.
- `DB_ENV=prod` uses prod mode and ephemeral Chroma.

## 6) (Optional but recommended) Rebuild schema docs from DDL

Run this if DDL changed or you want to guarantee fresh schema docs:

```bash
python data/v2/generate_schema_docs_from_ddl.py
```

By default, this writes to:

- `app/rag/catalog/schema_docs/v2_schema_docs.json`

## 7) Run the app (Streamlit UI)

```bash
python -m streamlit run app/ui.py
```

Open the URL printed by Streamlit (usually `http://localhost:8501`).

## 8) Quick verification checklist

1. Ask a simple query (example: `top 5 tokens by volume`).
2. Confirm SQL appears in UI.
3. Confirm results table renders.
4. In terminal logs, confirm startup line appears (DB env, schema docs path, chroma mode).
5. Confirm `chroma_db/` is created in local mode.

## 9) Common issues and fixes

- `ModuleNotFoundError: openai`
  - Ensure venv is active and re-run `pip install -r requirements.txt`.
- Database connection errors
  - Check `.env` Postgres credentials.
  - Verify host/network access (especially for Neon).
- Empty/incorrect retrieval context
  - Re-run schema doc generator and restart app.
  - Delete `chroma_db/` and rerun app to force re-ingest.
- Wrong DB mode
  - Confirm `DB_ENV` in `.env` (`local` vs `prod`).

## 10) Recommended team practice for portability

- Keep this file updated when env vars, schema path, or startup commands change.
- Avoid machine-specific absolute paths in code/config.
- When dependencies change, update `requirements.txt` in the same PR.

