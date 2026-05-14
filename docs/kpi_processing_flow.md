# KPI Processing Flow

```mermaid
flowchart TD
    A[User NL Question] --> B[app/rag/retriever.py<br/>retrieve_relevant_docs()]
    B --> C[app/rag/embeddings.py<br/>load_schema_docs + format_doc]
    C --> D[Schema Context Block]

    A --> E[app/llm/planner.py<br/>plan_query()]
    E --> F[QueryPlan]
    F --> G[app/llm/kpi_matcher.py<br/>match_kpi()]
    G --> H[app/rag/catalog/kpi_catalog.py<br/>load + validate]
    H --> I[app/rag/catalog/kpi_catalog.json]

    G --> J{KPI decision}
    J -- no_match --> K[Schema-only prompt]
    J -- matched_active --> L[Inject Canonical KPI Context]
    J -- matched_blocked --> M[Return blocked_kpi_message SQL]

    D --> K
    D --> L
    K --> N[app/llm/prompts.py<br/>compose_sql_user_prompt()]
    L --> N
    N --> O[app/llm/generate_sql.py<br/>LLM SQL generation]
    O --> P[SQL output]

    Q[app/eval/planner_kpi_cases.json] --> R[app/eval/run_planner_kpi_eval.py]
    R --> S[Planner + matcher regression report]
```

## File Responsibilities
- `app/llm/planner.py`
  - Deterministic intent/time-grain/entity extraction.
  - Handles phrases like `last 7 days` and `past 30 days`.

- `app/llm/kpi_matcher.py`
  - Scores candidate KPIs using name/alias/example overlap plus planner hints.
  - Applies threshold/ambiguity/leaderboard guardrails.
  - Returns `KpiMatchDecision`.

- `app/llm/generate_sql.py`
  - Orchestrates planner + KPI matcher + prompt assembly.
  - Handles blocked KPI route with explanatory SQL payload.

- `app/eval/run_planner_kpi_eval.py`
  - Offline assertion harness for planner and KPI routing behavior.

## What Each File/Function Does
- `app/rag/retriever.py` (`retrieve_relevant_docs`)
  - Why: retrieve only relevant schema/metric text for the current question.
  - What: combines deterministic metric lookup with vector-based table retrieval.

- `app/rag/embeddings.py` (`load_schema_docs`, `format_doc`)
  - Why: keep schema docs consumable by retrieval and prompting.
  - What: loads active schema docs, normalizes legacy formats, and formats table/metric text blocks.

- `app/llm/planner.py` (`plan_query`)
  - Why: add deterministic intent scaffolding before LLM generation.
  - What: infers `intent`, `time_grain`, `entities`, and ranking hints from NL query text.

- `app/llm/kpi_matcher.py` (`match_kpi`, `_score_entry`)
  - Why: route clear KPI-style questions to canonical KPI definitions.
  - What: loads validated catalog entries, scores candidates, applies confidence/ambiguity/tier/leaderboard guardrails, and returns `KpiMatchDecision`.

- `app/rag/catalog/kpi_catalog.py` (`load_kpi_catalog`, `validate_kpi_catalog`)
  - Why: prevent malformed KPI catalog data from entering runtime routing.
  - What: validates required fields, enums (`status`, `time_grains`, optional `tier`), and active/blocked constraints.

- `app/rag/catalog/kpi_catalog.json`
  - Why: runtime source of truth for canonical KPI semantics.
  - What: stores KPI definitions, recipes, required joins, aliases, statuses, and missing dependencies.

- `app/llm/prompts.py` (`compose_sql_user_prompt`, `compose_fix_user_prompt`)
  - Why: keep prompt composition consistent and testable.
  - What: merges schema context, planner block, and optional KPI block into generation/fix prompts.

- `app/llm/generate_sql.py` (`generate_sql`, `fix_sql`)
  - Why: orchestrate end-to-end SQL generation and one-pass fix path.
  - What:
    - runs planner + KPI matcher,
    - injects KPI context for active matches,
    - returns `blocked_kpi_message` SQL for blocked matches,
    - otherwise executes schema-grounded LLM generation.

- `app/eval/run_planner_kpi_eval.py`
  - Why: detect routing regressions before runtime quality degrades.
  - What: validates expected planner output and KPI mapping against case assertions.

- `app/eval/planner_kpi_cases.json`
  - Why: versioned, human-readable regression scenarios.
  - What: contains active KPI, blocked KPI, and schema fallback cases with expected routing results.

- `docs/kpi_canonical_list_v1.md`
  - Why: human-facing explanation of canonical KPIs.
  - What: mirrors runtime catalog in readable form (not read by matcher at runtime).

- `docs/kpi_inventory_grouped_by_section.md`
  - Why: requirements traceability by dashboard/leaderboard section.
  - What: operational inventory with status, calculation, and source mapping.


## Execution Sequence
1. Retrieve schema context once via RAG retrieval.
2. Build deterministic plan (`intent`, `time_grain`, entities).
3. Match optional canonical KPI with confidence guardrails.
4. Compose final prompt (schema + plan + optional KPI block).
5. Generate SQL or blocked-dependency SQL response.
6. Evaluate planner/matcher behavior offline via eval harness.

## Important Guardrails
- KPI layer is optional and must not block broad schema coverage.
- Blocked KPIs stay explicit (`blocked_by_missing_data`) with dependency messaging.
- Leaderboard KPIs require ranking intent language.
