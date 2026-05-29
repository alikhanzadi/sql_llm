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
pip install -r requirements_intel.txt
```

### 2) Configure environment

Create `.env`:

```bash
OPENAI_API_KEY=your_key
DB_ENV=local
```

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
  -> run_ingest()                                [app/rag/ingest.py]
  -> get_retrieval_context(question)             [app/rag/context_service.py]
       -> retrieve_relevant_docs()               [app/rag/retriever.py]
       -> build_context()
  -> generate_sql(question, context)             [app/llm/generate_sql.py]
       -> plan_query()                           [app/llm/planner.py]
       -> match_kpi()                            [app/llm/kpi_matcher.py]
       -> resolve_metric()                       [app/llm/metric_resolver.py]
       -> compose_sql_user_prompt()              [app/llm/prompts.py]
  -> validate_sql() + enforce_limit()            [app/db/validator.py]
  -> run_query()                                 [app/db/query_runner.py]
     -> explain_results()                        [app/llm/explain_results.py]
     -> or fix_sql(question, sql, error, context)
```

## Architecture Layers

### 1) RAG Retrieval Layer

- `app/rag/embeddings.py`: schema doc loading/normalization + embedding generation
- `app/rag/vector_store.py`: Chroma collection/client/query management
- `app/rag/retriever.py`: active retrieval strategy (metric-first + vector table retrieval)
- `app/rag/context_service.py`: single retrieval pass and shared context text
- `app/rag/ingest.py`: schema hash checks + conditional re-embedding

### 2) LLM Orchestration Layer

- `app/llm/planner.py`: deterministic intent/time-grain/entity hints
- `app/llm/kpi_matcher.py`: confidence-gated canonical KPI routing
- `app/llm/metric_resolver.py`: metric phrase disambiguation
- `app/llm/prompts.py`: standardized prompt assembly
- `app/llm/generate_sql.py`: main generate + fix orchestration
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

### Offline routing eval

Run:

```bash
python app/eval/run_planner_kpi_eval.py
```

Cases:

- `app/eval/planner_kpi_cases.json`

Coverage includes:

- active KPI matches
- blocked KPI behavior
- schema fallback behavior
- planner intent/time-grain expectations

### Manual retrieval checks

Use:

- `docs/retrieval_test_checklist.md`

This checklist validates table/metric retrieval quality and routing behavior before changing retriever logic.

## Repository Map (Core)

- `app/main.py` CLI entrypoint
- `app/ui.py` Streamlit entrypoint
- `app/llm/` generation, planning, KPI/metric routing, prompt composition
- `app/rag/` retrieval, embeddings, vector store, ingestion
- `app/rag/catalog/` KPI catalog + schema docs assets
- `app/eval/` offline planner/KPI routing eval harness
- `docs/` architecture, KPI, schema, and call-graph documentation
- `data/` synthetic/source datasets + DDL assets

## Known Constraints

- Depends on OpenAI APIs for embeddings + SQL/explanation generation.
- Retrieval quality still depends on schema doc quality and catalog curation.
- `app/rag/retriever_experimental.py` is intentionally not runtime-wired.
- `query.log` is runtime output and should be treated as an artifact.

## Suggested Next Improvements

- Expand offline eval set to include SQL shape assertions per intent class
- Add deterministic join-path checks for high-risk multi-table questions
- Add retrieval A/B mode switch (baseline vs reranked retriever) after eval coverage grows
- Add CI job to run planner/KPI eval on every PR

## Reference Docs

- `docs/kpi_catalog_spec.md`
- `docs/kpi_processing_flow.md`
- `docs/database_schema_taxonomy.md`
- `docs/function_call_graph_rag.md`
- `docs/module_call_graph.md`
