# ATHL Analytics Agent 

ATHL Analytics Agent is an NL-to-SQL assistant for ATHL data with:

- schema-grounded retrieval
- deterministic planning
- optional KPI semantic routing
- safe execution + retry
- offline routing evals

## Why This Project Exists

Large language models can generate SQL quickly, but raw prompting alone often fails on:

- incorrect joins
- wrong aggregation semantics
- hallucinated columns/tables
- poor handling of unavailable business metrics

This project addresses those failure modes with a layered architecture that keeps SQL generation grounded in actual schema and controlled business semantics.

## What It Does Today

- Converts natural-language questions into SQL
- Executes validated SQL against PostgreSQL
- Retries once with context-aware fix logic on execution errors
- Explains successful query results in natural language
- Optionally maps clear KPI requests to canonical KPI definitions
- Returns explicit dependency warnings for blocked KPIs

## Quick Start

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Configure environment

Create `.env`:

```bash
OPENAI_API_KEY=your_key
DB_ENV=local

# Neon Postgres + pgvector (schema retrieval, KPI matching, and query execution).
# Either set DATABASE_URL, or provide a [postgres_neon] block via Streamlit secrets.
DATABASE_URL=postgresql://user:password@your-neon-host.neon.tech/dbname
```

The same Neon connection backs both the `pgvector` retrieval indexes and SQL execution. On
Streamlit Cloud, credentials resolve from `st.secrets["postgres_neon"]` instead of `DATABASE_URL`
(see `docs/streamlit_cloud_data_guide.md`).

### 3) Run the app

```bash
streamlit run app/ui.py
```

Optional CLI mode:

```bash
python -m app.main
```

## Runtime Flow (Current)

```text
User question
  -> embed_query_safe(question)                  [app/rag/embeddings.py]   (embed once, shared)
  -> get_retrieval_context(question, embedding)  [app/rag/context_service.py]
       -> retrieve_relevant_docs()               [app/rag/retriever.py]    (Neon pgvector kNN)
       -> build_context()
  -> build_sql_planning_context(question, embedding) [app/llm/generate_sql.py]
       -> plan_query()                           [app/llm/planner.py]
       -> match_kpi()                            [app/llm/kpi_matcher.py]  (embedding shortlist + LLM judge)
  -> generate_sql(question, context, planning_context) [app/llm/generate_sql.py]
       -> compose_sql_user_prompt()              [app/llm/prompts.py]
       -> (blocked KPI -> safe blocked_kpi_message SQL)
  -> validate_sql() + enforce_limit()            [app/db/validator.py]
  -> run_query()                                 [app/db/query_runner.py]
     -> explain_results()                        [app/llm/explain_results.py]
     -> or fix_sql(question, sql, error, context, planning_context)
```

## Architecture Layers

### 1) RAG Retrieval Layer (Neon pgvector)

- `app/rag/embeddings.py`: schema doc loading/normalization + question embedding (`embed_query_safe`, embed-once)
- `app/db/neon.py`: shared Neon connection resolver (`DATABASE_URL` or `st.secrets[postgres_neon]`)
- `app/rag/retriever.py`: schema grounding via Neon `pgvector` kNN (lexical fallback offline)
- `app/rag/context_service.py`: single retrieval pass and shared context text
- `app/rag/catalog/embed_schema.py` / `embed_kpis.py`: offline, hash-gated builds of the `schema_embeddings` and `kpi_embeddings` pgvector indexes

### 2) LLM Orchestration Layer

- `app/llm/planner.py`: deterministic intent/time-grain/entity hints
- `app/llm/kpi_matcher.py`: embedding-shortlist KPI routing (deterministic fast-path + `gpt-4o-mini` LLM judge, lexical fallback)
- `app/llm/prompts.py`: standardized prompt assembly
- `app/llm/generate_sql.py`: planning context + main generate/fix orchestration
- `app/llm/explain_results.py`: result narration

### 3) Execution/Safety Layer

- `app/db/validator.py`: SELECT-only safety checks + limit enforcement
- `app/db/query_runner.py`: DB execution
- `app/cache.py`: SQL/result caching
- `app/logger.py`: query logging

## KPI Semantic Layer

Catalog source:

- `app/rag/catalog/kpi_catalog.json`

Catalog validation:

- `app/rag/catalog/kpi_catalog.py`

Routing outcomes:

- **No confident match:** schema-only generation
- **Matched + active KPI:** inject canonical KPI context block into prompt
- **Matched + blocked KPI:** return safe dependency message SQL (no fabricated data paths)

Design rule:

- KPI routing is optional and should never block broad schema-grounded analytics coverage.

## Evaluation & Testing

### Offline eval suite

```bash
python app/eval/run_planner_kpi_eval.py      # planner intent/grain + KPI routing (canonical vocab)
python app/eval/run_sql_correctness_eval.py  # asserts generated SQL uses required tables/joins/filters
python app/eval/run_paraphrase_eval.py       # held-out matcher precision on paraphrases
python app/eval/run_paraphrase_eval.py --negatives  # abstention on non-KPI questions
```

Cases:

- `app/eval/planner_kpi_cases.json`
- `app/eval/paraphrase_cases.json`
- `app/eval/negative_cases.json`

Coverage includes:

- active KPI matches and schema fallback behavior
- planner intent/time-grain expectations
- SQL-shape assertions (required tables/joins/filters/aggregation) per KPI
- paraphrase-robustness and non-KPI abstention for the matcher

The embedding + judge paths require OpenAI + Neon, so run them with the project venv; a bare
environment exercises the lexical fallback instead.

## Project Structure

```text
sql_llm/
├── app/
│   ├── main.py                         # CLI entrypoint
│   ├── ui.py                           # Streamlit entrypoint (full app)
│   ├── ui_chat.py                      # thin chat-only Streamlit shell over ui.py
│   ├── catalog_explorer.py             # schema/catalog explorer view helpers
│   ├── cache.py                        # SQL/result caching
│   ├── logger.py                       # query logging
│   │
│   ├── db/
│   │   ├── neon.py                     # shared Neon/pgvector connection resolver
│   │   ├── query_runner.py             # PostgreSQL execution
│   │   ├── validator.py                # SELECT-only safety + LIMIT enforcement
│   │   └── schema.py                   # active schema selection helpers
│   │
│   ├── llm/
│   │   ├── generate_sql.py             # planning context + generate/fix orchestration
│   │   ├── prompts.py                  # system/user prompt composers
│   │   ├── planner.py                  # intent + time-grain planning
│   │   ├── kpi_matcher.py              # embedding-shortlist KPI routing + LLM judge
│   │   └── explain_results.py          # NL explanation of query results
│   │
│   ├── rag/
│   │   ├── context_service.py          # single retrieval context builder
│   │   ├── retriever.py                # schema grounding via Neon pgvector (lexical fallback)
│   │   ├── embeddings.py               # schema-doc loading/formatting + embed_query_safe
│   │   └── catalog/
│   │       ├── kpi_catalog.json        # canonical KPI runtime source of truth (62 active)
│   │       ├── kpi_catalog.py          # KPI catalog loader/validator
│   │       ├── embed_kpis.py           # offline build: kpi_embeddings (hash-gated)
│   │       ├── embed_schema.py         # offline build: schema_embeddings (hash-gated)
│   │       ├── generate_kpi_docs.py    # renders kpi_inventory_grouped_by_section.md
│   │       ├── generate_schema_docs_from_ddl.py
│   │       └── schema_docs/
│   │           └── v2_schema_docs.json # 13 table docs + 30 metric docs
│   │
│   └── eval/
│       ├── run_planner_kpi_eval.py     # planner intent/grain + KPI routing
│       ├── run_sql_correctness_eval.py # SQL-shape assertions per KPI
│       ├── run_paraphrase_eval.py      # matcher precision on paraphrases + negatives
│       ├── planner_kpi_cases.json
│       ├── paraphrase_cases.json
│       └── negative_cases.json
│
├── docs/                               # documentation (see Documentation below)
│   ├── archive/                        # superseded docs, kept for history
│   ├── kpi_sources/                    # upstream source material for the KPI catalog
│   └── my_docs/                        # working notes (migration/review)
│
├── data/
│   ├── tables/                         # local CSV snapshots of each table
│   ├── sql_create_tables/              # Postgres + Snowflake DDL
│   ├── neondb/                         # Neon data generation + load
│   └── local_athl_v2/                  # local Postgres load helpers
│
├── docker-compose.yml
├── requirements.txt
├── runtime.txt                         # Python 3.11 pin for Streamlit Cloud
└── Readme.md
```

## Known Constraints

- Depends on OpenAI APIs for embeddings (`text-embedding-3-small`) + SQL/explanation/judge generation (`gpt-4o-mini`).
- Depends on a Neon Postgres instance with `pgvector` for retrieval indexes and query execution.
- Retrieval quality still depends on schema doc quality and catalog curation.
- When OpenAI/Neon are unavailable, retriever and KPI matcher degrade to lexical scoring.
- `query.log` is runtime output and should be treated as an artifact.

## Suggested Next Improvements

- Add deterministic join-path checks for high-risk multi-table questions
- Add retrieval A/B mode switch (baseline vs reranked retriever) after eval coverage grows
- Add CI job to run the planner/KPI/SQL-correctness/paraphrase evals on every PR

## Documentation

All docs live in `docs/`. Start with `system_processing_flow.md` for the end-to-end picture, then
`kpi_catalog_spec.md` + `kpi_canonical_list.md` for the KPI layer.

### Architecture & flow
- **`system_processing_flow.md`** — the whole "Ask the Data" pipeline (one question → one answer) at module altitude. The best single entry point.
- **`module_call_graph.md`** — runtime module dependency graph (layered: entry → orchestration → RAG/LLM/DB).
- **`function_call_graph_rag.md`** — function-level call graph for the RAG + KPI retrieval paths and the shared Neon resolver.
- **`llm.md`** — LLM function flow (generate → validate → execute → fix → explain) for the CLI and Streamlit entrypoints.
- **`kpi_processing_flow.md`** — the KPI-matching slice in detail (embedding shortlist → deterministic fast-path / LLM judge).
- **`kpi_processing_flow_future.md`** — Phase 1.7 design record (delivered) plus the remaining smaller future ideas.

### KPI semantic layer
- **`kpi_catalog_spec.md`** — runtime contract for KPI routing: entry schema, validation rules, matcher thresholds, eval wiring.
- **`kpi_canonical_list.md`** — hand-maintained source of truth for the 62 canonical KPIs (definitions, tables, sections, revenue family). The JSON catalog is linted against this.
- **`kpi_inventory_grouped_by_section.md`** — auto-generated mirror of the catalog grouped by section. Do not hand-edit; regenerate with `generate_kpi_docs.py`.

### Schema & data
- **`database_schema_taxonomy.md`** — narrative taxonomy of the schema (entities, domains, data semantics).
- **`database_er_diagram.md`** — entity-relationship diagram (mermaid).

### Deployment & design
- **`streamlit_cloud_data_guide.md`** — deploying and using the app on Streamlit Community Cloud (secrets, tabs, data inventory, runtime path).
- **`athl_design_language.md`** — visual/design brief for building ATHL-styled analytics dashboards.

### Supporting folders
- **`docs/archive/`** — superseded docs kept for history (`implementation_scope.md`, `retrieval_test_checklist.md`, `kpi_canonical_overview.md`).
- **`docs/kpi_sources/`** — upstream source material the KPI catalog was built from (north star KPIs, handoffs, framework spreadsheet).
- **`docs/my_docs/`** — personal working notes (migration and review logs).
