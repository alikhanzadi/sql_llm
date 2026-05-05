# Local Schema Migration Notes

This document reflects the current simplified setup.

## Current Direction

1. Local runtime uses only `athl_v2`.
2. `public` is legacy-only (docs/archive), not a runtime code path.
3. Streamlit Cloud (`DB_ENV=prod`) remains Neon-only.

---

## Runtime Sources of Truth

### `app/db/schema.py`

- `ACTIVE_LOCAL_SCHEMA = "athl_v2"`
- `get_active_local_schema()`
- `get_active_local_schema_docs_path()` -> `app/rag/catalog/schema_docs/neondb_schema_docs.json`
- `get_schema()` reads schema metadata from the active local schema.

### `app/db/query_runner.py`

- Local connections set `search_path` at connection startup using:
  - `options="-c search_path=athl_v2"`
- No runtime fallback to `public`.
- No post-error search-path reset helper needed.

---

## Loader and DDL

### `data/neondb/sql_create_tables/athl_raw_tables_postgres.sql`

- `tokens` is declared before `transactions` and wallet tables, so FK binding is deterministic.
- `issuer_daily_revenue` PK is source-corrected to:
  - `PRIMARY KEY (issuer_id, date)`

### `data/neondb/load_local_schema_v2.py`

Purpose: create and load local `athl_v2` from DDL + CSV files.

What it does:
1. Creates schema `athl_v2`
2. Executes source DDL as-is
3. Truncates target schema tables
4. Loads CSVs with column compatibility filtering

Removed from loader:
- Runtime DDL typo patching
- Runtime table rebuilds for FK correction
- Legacy schema toggles

---

## RAG Alignment

- `app/rag/embeddings.py`, `app/rag/ingest.py`, and `app/rag/vector_store.py` now read schema configuration from `app/db/schema.py`.
- Local ingest and vector collection state remain scoped to the active local schema (now fixed to `athl_v2`).

---

## Usage

Build/load local schema:

```bash
./venv/bin/python data/neondb/load_local_schema_v2.py
```

Run app:

```bash
python -m app.main
```

or

```bash
streamlit run app/ui.py
```
