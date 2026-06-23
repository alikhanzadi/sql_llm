# LLM Function Flow

Both entrypoints (`app/main.py` CLI and `app/ui.py` / `app/ui_chat.py` Streamlit) share the same
orchestration: embed the question **once**, retrieve schema context, compute deterministic planning
+ KPI routing, generate SQL, validate, execute, and (on error) repair once.

```mermaid
flowchart TD
    subgraph CLI Path
        A[app/main.py] --> B[user_input from terminal]
        B --> C[embed_query_safe]
        C --> D[get_retrieval_context]
        C --> D2[build_sql_planning_context]
        D --> E[generate_sql]
        D2 --> E
        E --> F[validate_sql + enforce_limit]
        F --> G[run_query]
        G -->|error| H[fix_sql]
        H --> I[run_query fixed SQL]
        G -->|success| J[explain_results]
        I -->|success| J
    end

    subgraph Streamlit Path
        U[app/ui.py / app/ui_chat.py] --> V[user_input from chat box]
        V --> W[embed_query_safe]
        W --> X[get_retrieval_context]
        W --> X2[build_sql_planning_context]
        X --> Y[generate_sql]
        X2 --> Y
        Y --> Z[validate_sql + enforce_limit]
        Z --> AA[run_query]
        AA -->|error| AB[fix_sql]
        AB --> AC[run_query fixed SQL]
        AA -->|success| AD[explain_results]
        AC -->|success| AD
    end

    subgraph LLM internals
        D2 --> P1[plan_query]
        D2 --> P2[match_kpi]
        P2 --> P3[embedding shortlist + LLM judge / lexical fallback]

        E --> L0{blocked KPI?}
        L0 -->|yes| LB[return blocked_kpi_message SQL]
        L0 -->|no| L2[compose_sql_user_prompt + SYSTEM_PROMPT]
        L2 --> L3[OpenAI gpt-4o-mini SQL generation]
        L3 --> L4[clean_sql]

        H --> L6[compose_fix_user_prompt + SYSTEM_PROMPT]
        L6 --> L7[OpenAI gpt-4o-mini SQL fix]
        L7 --> L8[clean_sql]
    end
```

## Function Sequence

1. `embed_query_safe(...)` in `app/rag/embeddings.py`
   - Embeds the question once (`text-embedding-3-small`); the vector is shared with schema
     retrieval and KPI matching so the question is never re-embedded.
   - Returns `None` when OpenAI is unavailable (downstream paths fall back to lexical).
2. `get_retrieval_context(question, query_embedding=...)` in `app/rag/context_service.py`
   - Schema grounding: kNN over Neon `pgvector` `schema_embeddings`, formatted into the context text.
3. `build_sql_planning_context(question, query_embedding=...)` in `app/llm/generate_sql.py`
   - `plan_query(...)` in `app/llm/planner.py` — infers intent, time grain, entities, optional top-k.
   - `match_kpi(...)` in `app/llm/kpi_matcher.py` — embedding shortlist from `kpi_embeddings` +
     deterministic fast-path / `gpt-4o-mini` LLM judge; lexical fallback when OpenAI/Neon are down.
   - Returns a reusable `SqlPlanningContext(plan, kpi_decision)` used by both generate and fix.
4. `generate_sql(question, context, planning_context=...)` in `app/llm/generate_sql.py`
   - Blocked KPI → returns a safe `blocked_kpi_message` SELECT (no fabricated SQL).
   - Otherwise composes the prompt (`compose_sql_user_prompt` with plan + KPI blocks) and calls
     `gpt-4o-mini` (temperature 0), then `clean_sql`.
5. `clean_sql(...)` in `app/llm/generate_sql.py`
   - Removes markdown fences and trims whitespace.
6. `fix_sql(...)` in `app/llm/generate_sql.py` (error path)
   - Reuses the same `planning_context`; composes `compose_fix_user_prompt` with the failed SQL and
     DB error; returns corrected SQL from `gpt-4o-mini`.
7. `explain_results(...)` in `app/llm/explain_results.py`
   - Separate `gpt-4o-mini` call that explains query output in plain English.

## app/llm Only Flowchart

```mermaid
flowchart TD
    A[Caller: main.py / ui.py] --> B[build_sql_planning_context question]
    B --> C[plan_query question]
    B --> D[match_kpi question, plan, query_embedding]
    A --> E[generate_sql user_query, context, planning_context]
    C --> E
    D --> E
    E --> F{blocked KPI?}
    F -->|yes| FB[return blocked_kpi_message SQL]
    F -->|no| G[compose_sql_user_prompt plan_block + kpi_block]
    G --> H[OpenAI gpt-4o-mini with SYSTEM_PROMPT]
    H --> I[clean_sql]
    I --> J[SQL returned]

    J --> K[Caller executes SQL]
    K -->|error| L[fix_sql user_query, sql, error, context, planning_context]
    L --> M[compose_fix_user_prompt]
    M --> N[OpenAI gpt-4o-mini fix call]
    N --> O[clean_sql]
    O --> P[fixed SQL returned]

    K -->|success| Q[explain_results question, sql, results]
    Q --> R[OpenAI gpt-4o-mini explanation]
```

> See `module_call_graph.md` and `function_call_graph_rag.md` for the full module/function graphs,
> including the Neon `pgvector` backend and the offline embedding builds.
