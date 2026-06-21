# KPI Processing Flow (current — implemented)

> KPI matching is embedding-first: each canonical KPI is embedded into a Neon `pgvector`
> table (`kpi_embeddings`); at runtime the question is embedded and the nearest KPIs are
> retrieved, then resolved by deterministic rules. A lexical scorer is the fallback when
> OpenAI/Neon are unavailable. The planned unification (single backend, one embedding call,
> optional LLM judge) is in `kpi_processing_flow_future.md`.

```mermaid
flowchart TD
    A[User NL Question] --> B[app/rag/retriever.py<br/>retrieve_relevant_docs()]
    B --> C[chroma: schema_docs<br/>vector search]
    C --> D[Schema Context Block]

    A --> E[app/llm/planner.py<br/>plan_query()]
    E --> F[QueryPlan]

    A --> G[app/llm/kpi_matcher.py<br/>match_kpi()]
    F --> G
    G --> T[embed question<br/>text-embedding-3-small]
    T --> U[(Neon pgvector<br/>kpi_embeddings: top-8 kNN)]
    U --> V[Top-k KPI candidates]
    V --> W[_resolve_candidates<br/>similarity gate 0.30 · specificity<br/>revenue-cluster default · leaderboard guardrail]
    W --> J{KPI decision}

    G -. OpenAI/Neon unavailable .-> GL[_lexical_match_kpi<br/>token-overlap fallback]
    GL --> J

    J -- below_gate / no_match --> K[Schema-only prompt]
    J -- matched_active --> L[Inject Canonical KPI Context<br/>recipe + value_basis + raw_sql]
    J -- matched_blocked --> M[Return blocked_kpi_message SQL]

    D --> K
    D --> L
    K --> N[app/llm/prompts.py<br/>compose_sql_user_prompt()]
    L --> N
    N --> O[app/llm/generate_sql.py<br/>LLM SQL generation]
    O --> P[SQL output]

    H[app/rag/catalog/kpi_catalog.py<br/>load + validate] --> I[app/rag/catalog/kpi_catalog.json]
    I --> X[app/rag/catalog/embed_kpis.py<br/>build_embed_text + embed, hash-gated]
    X --> U

    Q1[app/eval/run_sql_correctness_eval.py] --> R1[SQL-correctness report]
    Q2[app/eval/run_paraphrase_eval.py] --> R2[matcher precision + abstention]
    Q3[app/eval/run_planner_kpi_eval.py] --> R3[routing regression report]
```

## File Responsibilities
- `app/llm/planner.py` (`plan_query`)
  - Deterministic intent/time-grain/entity extraction; handles `last 7 days`, `past 30 days`.

- `app/llm/kpi_matcher.py` (`match_kpi`, `_embedding_candidates`, `_resolve_candidates`, `_lexical_match_kpi`)
  - Embeds the question, retrieves top-k KPIs from Neon `pgvector`, applies the similarity
    gate, then the deterministic resolver (specificity, revenue-cluster default, leaderboard
    guardrail). Falls back to lexical token-overlap scoring if the vector store is
    unavailable. Returns `KpiMatchDecision`.

- `app/rag/catalog/embed_kpis.py`
  - Offline build of the KPI embedding index in Neon (hash-gated). `embed_text` = name +
    definition + aliases + example questions, sourced from `kpi_catalog.json`.

- `app/rag/catalog/kpi_catalog.py` / `kpi_catalog.json`
  - Runtime source of truth and validated entry contract; the content the embeddings derive from.

- `app/llm/prompts.py` / `app/llm/generate_sql.py`
  - Compose schema + plan + KPI block; inject the directive recipe (`value_basis`, filters,
    `raw_sql`); handle the blocked-KPI route. Unchanged by the embedding upgrade.

- `app/eval/run_planner_kpi_eval.py` / `run_sql_correctness_eval.py` / `run_paraphrase_eval.py`
  - Routing regression; catalog-driven SQL-correctness assertions; held-out matcher precision
    and abstention.

## Execution Sequence
1. Retrieve schema context once via RAG retrieval (`chroma: schema_docs`).
2. Build deterministic plan (`intent`, `time_grain`, entities).
3. Embed the question; retrieve top-k KPI candidates from Neon `pgvector` (or lexical fallback).
4. Resolve candidates (similarity gate → specificity / cluster default / guardrail) → `KpiMatchDecision`.
5. Compose the final prompt (schema + plan + optional KPI block) and generate SQL (or blocked-dependency SQL).
6. Evaluate matcher precision and SQL correctness offline via the eval harnesses.

## Important Guardrails
- KPI layer is optional; the similarity gate lets generic questions fall back to schema-only.
- Blocked KPIs stay explicit (`blocked_by_missing_data`) with dependency messaging.
- Leaderboard KPIs require ranking intent language.
- The catalog is flat (no tiers); priority among look-alikes is handled by the resolver.
- KPI vectors are catalog-derived and env-independent (read from Neon regardless of `DB_ENV`).

## Known limitation
- The similarity gate rejects out-of-domain questions but cannot separate schema-exploration
  questions (e.g. "sample the issuers table"), which overlap the KPI band. The planned fix is
  an LLM judge over the top-k shortlist with a NONE option (see `kpi_processing_flow_future.md`).
