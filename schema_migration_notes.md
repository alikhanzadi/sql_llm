# Local Schema Migration + Runtime Selection Notes

This document explains, step by step, what was changed to support:

1. Keeping the old local schema available (`public`)
2. Adding a new local schema that follows Neon-style structure (`athl_v2`)
3. Running local CLI and local Streamlit against the new schema by default
4. Keeping Streamlit Cloud (`DB_ENV=prod`) isolated to Neon

---

## 1) Conceptual Design

### Problem we were solving
- Local app originally used a small/legacy schema (`public`) with old table names.
- Cloud app uses Neon with many more tables and different names.
- Retrieval, embeddings, SQL generation, and DB execution all need to stay aligned to the *same* schema in each run.

### Key design decision
Use a small runtime profile layer so one selected schema controls:
- Postgres `search_path`
- schema docs file used for embeddings/retrieval
- Chroma collection namespace
- ingestion hash file namespace

This prevents cross-contamination (for example, local-old docs accidentally being reused with local-new DB tables).

---

## 2) Functional Flow After Changes

### Local default path (new schema)
- `DB_ENV=local`
- default `LOCAL_PG_SCHEMA=athl_v2`
- DB queries run against `athl_v2` via `SET search_path TO athl_v2, public`
- RAG docs source uses `data/neondb_schema_docs.json`
- Chroma collection and hash are namespaced to `local_athl_v2`

### Local legacy path (manual switch)
- `export LOCAL_PG_SCHEMA=public`
- DB queries run against legacy tables
- RAG docs source switches to `data/local/schema_docs.json`
- Chroma collection/hash switch to `local_public`

### Cloud path (unchanged)
- `DB_ENV=prod`
- Uses Neon credentials and Neon docs
- Local schema selector is hidden in Streamlit
- Chroma mode remains ephemeral for cloud

---

## 3) File-by-File Changes

## `app/runtime_profile.py` (new)

Purpose: central runtime identity used across DB + RAG + Chroma.

Functions:
- `get_db_env()` -> normalized env (`local`/`prod`)
- `get_local_schema_name()` -> sanitized local schema name
  - default is now `athl_v2`
- `get_runtime_profile()` -> profile key
  - `prod` in cloud
  - `local_<schema>` locally (example: `local_athl_v2`)

Why this matters:
- One profile key drives all moving parts and avoids accidental mixing.

---

## `app/db/query_runner.py` (modified)

Purpose: choose DB credentials and set query execution schema.

What changed:
- Local-only search path setup:
  - `SET search_path TO <LOCAL_PG_SCHEMA>, public`

Result:
- Same SQL text can target either old or new local schema without hardcoding table prefixes.

---

## `app/rag/embeddings.py` (modified)

Purpose: load schema docs and normalize them for embeddings.

What changed:
- Docs source is now runtime-aware:
  - `prod` -> `data/neondb_schema_docs.json`
  - local `public` -> `data/local/schema_docs.json`
  - local non-public (like `athl_v2`) -> `data/neondb_schema_docs.json`
- Exposed `get_active_schema_path()` for startup visibility.
- Kept normalization for flattened Neon export format (`table_name`/`column_name`).

Result:
- SQL generation context follows the active runtime/schema instead of being fixed to one file.

---

## `app/rag/vector_store.py` (modified)

Purpose: configure Chroma client and collection naming.

What changed:
- Collection name now includes runtime profile:
  - `schema_docs_local_public`
  - `schema_docs_local_athl_v2`
  - `schema_docs_prod`
- Chroma mode:
  - local -> persistent
  - prod -> ephemeral

Result:
- Local old/new and prod retrieval contexts are isolated.

---

## `app/rag/ingest.py` (modified)

Purpose: rebuild embeddings only when schema docs changed.

What changed:
- Hash file is profile-aware:
  - `chroma_db/schema_hash_local_public.txt`
  - `chroma_db/schema_hash_local_athl_v2.txt`
  - `chroma_db/schema_hash_prod.txt`
- Startup log now prints:
  - `DB_ENV`
  - local schema
  - active schema docs file
  - chroma mode

Result:
- Better observability and no hash collisions across environments/schemas.

---

## `scripts/load_local_schema_v2.py` (new)

Purpose: create/load new local schema from Neon-style SQL + CSVs.

Inputs:
- DDL: `data/neondb/sql_create_tables/athl_raw_tables_postgres.sql`
- CSVs: `data/neondb/tables/*.csv`
- target schema: `LOCAL_PG_SCHEMA` (default `athl_v2`)

What it does:
1. Connects to local Postgres
2. Creates schema if missing
3. Executes DDL (with runtime patch for known `revenue_date` typo in source SQL)
4. Rebuilds specific tables (`transactions`, `payments`, `user_token_wallet`) with schema-qualified foreign keys so they bind to the target schema
5. Truncates target-schema tables
6. Loads CSV data with column compatibility filtering

Why table rebuild was needed:
- In raw DDL order, some FKs could bind to `public` tables if names overlap.
- Rebuilding with explicit `<schema>.<table>` FK targets guarantees correctness.

---

## `app/ui.py` (modified)

Purpose: local user control over schema selection.

What changed:
- Added Streamlit sidebar selector for local runs only:
  - `athl_v2` (new/default)
  - `public` (legacy)
- If changed, updates `LOCAL_PG_SCHEMA` and reruns.
- Selector is hidden when `DB_ENV=prod`.

Result:
- Easy local switching without code edits.
- No cloud behavior change.

---

## 4) Commands You Can Use

## Build/load new local schema

```bash
./venv/bin/python scripts/load_local_schema_v2.py
```

## Run local with new schema (default)

```bash
export DB_ENV=local
unset LOCAL_PG_SCHEMA
python -m app.main
```

or

```bash
export DB_ENV=local
unset LOCAL_PG_SCHEMA
streamlit run app/ui.py
```

## Run local with old schema

```bash
export DB_ENV=local
export LOCAL_PG_SCHEMA=public
python -m app.main
```

or use the Streamlit sidebar selector.

---

## 5) One-Change Manual Override Summary

Yes, manual switching can be done with one change:
- set `LOCAL_PG_SCHEMA`

Examples:
- New schema: `LOCAL_PG_SCHEMA=athl_v2`
- Old schema: `LOCAL_PG_SCHEMA=public`

Everything else (docs path, Chroma namespace, ingestion hash, DB search path) follows automatically.
