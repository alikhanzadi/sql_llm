# LLM Function Flow

```mermaid
flowchart TD
    subgraph CLI Path
        A[app/main.py] --> B[user_input from terminal]
        B --> C[run_ingest]
        C --> D[get_retrieval_context]
        D --> E[generate_sql]
        E --> F[validate_sql + enforce_limit]
        F --> G[run_query]
        G -->|error| H[fix_sql]
        H --> I[run_query fixed SQL]
        G -->|success| J[explain_results]
        I -->|success| J
    end

    subgraph Streamlit Path
        U[app/ui.py] --> V[user_input from text box]
        V --> W[run_ingest]
        W --> X[get_retrieval_context]
        X --> Y[generate_sql]
        Y --> Z[validate_sql + enforce_limit]
        Z --> AA[run_query]
        AA -->|error| AB[fix_sql]
        AB --> AC[run_query fixed SQL]
        AA -->|success| AD[explain_results]
        AC -->|success| AD
    end

    subgraph LLM internals
        E --> L1[plan_query]
        L1 --> L2[compose_sql_user_prompt + SYSTEM_PROMPT]
        L2 --> L3[OpenAI SQL generation]
        L3 --> L4[clean_sql]

        H --> L5[plan_query]
        L5 --> L6[compose_fix_user_prompt]
        L6 --> L7[OpenAI SQL fix]
        L7 --> L8[clean_sql]
    end
```

## Function Sequence

1. `generate_sql(...)` in `app/llm/generate_sql.py`
   - Main SQL generation entrypoint.
   - Calls planner, composes prompt, calls LLM, normalizes SQL text.
2. `plan_query(...)` in `app/llm/planner.py`
   - Lightweight parser of the question.
   - Infers intent, time grain, entities, and optional top-k hint.
3. `QueryPlan.to_prompt_block(...)` in `app/llm/planner.py`
   - Converts plan output into a text block added to the prompt.
4. `compose_sql_user_prompt(...)` in `app/llm/prompts.py`
   - Builds SQL-generation user prompt from context + plan + question.
5. LLM generation call in `generate_sql(...)`
   - Uses `SYSTEM_PROMPT` plus composed user prompt.
6. `clean_sql(...)` in `app/llm/generate_sql.py`
   - Removes markdown fences and trims whitespace.
7. `fix_sql(...)` in `app/llm/generate_sql.py` (error path)
   - Repeats planning + prompt composition with failed SQL and DB error.
   - Returns corrected SQL from the LLM.
8. `explain_results(...)` in `app/llm/explain_results.py`
   - Separate LLM call that explains query output in plain English.

## app/llm Only Flowchart

```mermaid
flowchart TD
    A[Caller: main.py or ui.py] --> B[generate_sql user_query context]
    B --> C[plan_query question]
    C --> D[to_prompt_block]
    D --> E[compose_sql_user_prompt]
    E --> F[OpenAI chat.completions with SYSTEM_PROMPT]
    F --> G[clean_sql]
    G --> H[SQL returned]

    H --> I[Caller executes SQL]
    I -->|error| J[fix_sql user_query sql error context]
    J --> K[plan_query question]
    K --> L[to_prompt_block]
    L --> M[compose_fix_user_prompt]
    M --> N[OpenAI chat.completions fix call]
    N --> O[clean_sql]
    O --> P[fixed SQL returned]

    I -->|success| Q[explain_results question sql results]
    Q --> R[OpenAI explanation]
```
