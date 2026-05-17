# ATHL Analytics Agent — Copilot Instructions

## Project Overview
AI-powered natural language → SQL pipeline for ATHL analytics. Users ask questions in plain English; the system retrieves relevant schema context via RAG, generates PostgreSQL queries with an LLM, validates, executes, and explains results.

## Architecture & Data Flow
```
User Question
  → run_ingest()             [app/rag/ingest.py]      — hash-gated embed & store schema docs
  → retrieve_relevant_docs() [app/rag/retriever.py]   — metrics matched deterministically; tables via Chroma vector search
  → build_context()          [app/rag/context_builder.py]
  → generate_sql()           [app/llm/generate_sql.py] — OpenAI gpt-4o-mini, temp=0
  → validate_sql()           [app/db/validator.py]    — SELECT-only allowlist
  → enforce_limit()                                   — appends LIMIT 10 if absent
  → PostgresClient.run_query() [app/db/query_runner.py]
  → on error: fix_sql()      [app/llm/generate_sql.py] — retry with error + context
  → explain_results()        [app/llm/explain_results.py]
```

The Streamlit UI (`app/ui.py`) is the primary entry point; `app/main.py` is a CLI version of the same pipeline.

## Key Conventions

### Schema Docs as First-Class Citizens
- Schema metadata lives in `data/neondb_schema_docs.json` (prod) or `data/local/schema_docs.json` (local), controlled by `DB_ENV` env var.
- Both **tables** and **metrics** are document types in the JSON. Metrics carry a `definition` field used to guide correct aggregation (e.g., "average trades per user" uses a subquery pattern).
- `run_ingest()` is idempotent — it hashes the schema docs and skips re-embedding if unchanged. Hash state stored at `chroma_db/schema_hash_{db_env}.txt`.

### RAG Retrieval Strategy
- Metrics are matched **deterministically** (keyword match on `doc["name"]`) before vector search — do not change this to pure vector retrieval.
- Tables are retrieved via ChromaDB similarity search (`top_k=4`).
- `format_doc()` in `app/rag/embeddings.py` controls how docs are serialized for embedding — changes here affect retrieval quality.

### ChromaDB Environments
- `DB_ENV=local` (default): persistent Chroma client at `./chroma_db/`, collections suffixed `_local`.
- `DB_ENV=prod`: ephemeral in-memory Chroma client (filesystem is not persistent in cloud deploys).

### SQL Generation Rules (enforced via `app/llm/prompts.py`)
- LLM must return **raw SQL only** — no markdown, no backticks. `clean_sql()` strips fences as a fallback.
- Always qualify columns with table aliases when joining (`u.signup_date`, not `signup_date`).
- For "average of a per-entity metric", use a subquery pattern — this is explicitly in the system prompt to avoid common LLM aggregation errors.

### Caching
- `app/cache.py` uses simple in-process dicts — `query_cache` (question → SQL) and `result_cache` (SQL → results). No persistence across restarts.

## Developer Workflows

### Run the app
```bash
python -m streamlit run app/ui.py
```

### Run CLI pipeline
```bash
python -m app.main
```

### Environment setup
Create `.env` with:
```
OPENAI_API_KEY=your_key
DB_ENV=local          # or "prod" for ephemeral Chroma
DATABASE_URL=postgresql://...
```

### Re-ingesting schema (force)
Delete `chroma_db/schema_hash_local.txt` (or `_prod`) to force re-embed on next run.

## Key Files
| File | Role |
|------|------|
| `app/ui.py` | Streamlit UI — primary entry point |
| `app/llm/generate_sql.py` | NL→SQL + self-correction (`fix_sql`) |
| `app/llm/prompts.py` | System prompt with SQL rules & examples |
| `app/rag/retriever.py` | Hybrid metric+vector retrieval |
| `app/rag/ingest.py` | Hash-gated schema embedding pipeline |
| `app/rag/vector_store.py` | ChromaDB client (env-aware) |
| `data/neondb_schema_docs.json` | Prod schema + metric definitions |

## Not Yet Implemented
`airflow/` (DAG orchestration) and `dbt/` (data modeling) directories are scaffolded but empty — do not reference them as functional components.
