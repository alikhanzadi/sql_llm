# System Processing Flow (current — implemented)

> The whole "Ask the Data" pipeline, one question → one answer, at module altitude.
> The question is embedded **once** (`embed_query_safe`) and that vector is shared by both
> Neon `pgvector` reads — schema retrieval (`schema_embeddings`) and KPI matching
> (`kpi_embeddings`). Each dashed box is one subsystem. Compare with
> `kpi_processing_flow.md` (the KPI slice in detail).

```mermaid
%%{init: {'theme':'base','themeVariables':{'background':'#ffffff','primaryColor':'#ffffff','primaryBorderColor':'#888','lineColor':'#9aa0a6','fontSize':'13px','clusterBkg':'#fbfbfa','clusterBorder':'#d4d4d0'},'flowchart':{'htmlLabels':true,'curve':'basis','nodeSpacing':34,'rankSpacing':46}}}%%
flowchart TD
  Q([User question]):::io
  EMB["embed_query_safe()<br/>embed once · text-embedding-3-small"]:::io
  Q --> EMB

  subgraph SR["RAG · Schema Retrieval"]
    direction TB
    RET["retrieve_relevant_docs()"]:::rag
    SEMB[("Neon pgvector<br/>schema_embeddings")]:::store
    CTX["Schema context block"]:::rag
    RET --> SEMB --> CTX
    RET -. offline .-> LEXR["lexical table-doc fallback"]:::rag
    LEXR --> CTX
  end

  subgraph PL["Planning"]
    PLN["plan_query()<br/>intent · time · entities"]:::plan
  end

  subgraph KM["KPI Matching"]
    direction TB
    MK["match_kpi()<br/>top-8 from kpi_embeddings"]:::kpi
    KEMB[("Neon pgvector<br/>kpi_embeddings")]:::store
    GATE{"similarity ≥ 0.30 ?"}:::kpi
    LIT{"literal KPI name<br/>in question ?"}:::kpi
    DET["_deterministic_winner()<br/>specificity · cluster default"]:::kpi
    JUDGE["_llm_judge() over top-5<br/>gpt-4o-mini: pick / NONE"]:::kpi
    DEC{"KPI decision"}:::kpi
    KEMB --> MK --> GATE
    GATE -- no --> DEC
    GATE -- yes --> LIT
    LIT -- yes --> DET --> DEC
    LIT -- no --> JUDGE --> DEC
    MK -. offline .-> LEXK["_lexical_match_kpi()"]:::kpi
    LEXK --> DEC
  end

  EMB --> RET
  EMB --> MK
  Q --> PLN

  subgraph GEN["SQL Generation"]
    direction TB
    PRM["compose_sql_user_prompt()"]:::gen
    GS["generate_sql()<br/>gpt-4o-mini"]:::gen
    PRM --> GS
  end

  CTX --> PRM
  PLN --> PRM
  DEC -- "matched → inject recipe" --> PRM
  DEC -- "below gate / NONE → schema-only" --> PRM
  DEC -- "blocked KPI" --> GS

  subgraph SAFE["Safety / Validation"]
    VAL["validate_sql()<br/>enforce_limit()"]:::safe
  end
  GS --> VAL

  subgraph EX["Execution"]
    direction TB
    RUN["run_query()<br/>PostgreSQL · read-only"]:::exec
    PG[("PostgreSQL<br/>ATHL data tables")]:::store
    RUN --> PG
  end
  VAL -- valid --> RUN
  VAL -- unsafe --> ERR["Safe error message"]:::io

  RUN -- "DB error" --> FIX["fix_sql()<br/>retry once"]:::gen
  FIX --> VAL

  subgraph XP["Explanation"]
    EXP["explain_results()<br/>gpt-4o-mini"]:::expl
  end
  RUN -- rows --> EXP
  EXP --> ANS([Answer to user]):::io
  ERR --> ANS

  subgraph SUP["Support · always on"]
    CACHE["cache.py<br/>SQL & result cache"]:::sup
    LOG["logger.py<br/>query.log"]:::sup
  end
  GS -. cache .-> CACHE
  ANS -. log .-> LOG

  subgraph OFF["Offline builds — run after catalog / schema edits"]
    direction TB
    CAT["kpi_catalog.json<br/>62 KPIs"]:::off
    SDOC["schema_docs/*.json"]:::off
    EK["embed_kpis.py"]:::off
    ES["embed_schema.py"]:::off
    NEON["app/db/neon.py<br/>get_neon_conn"]:::off
    CAT --> EK
    SDOC --> ES
  end
  EK --> KEMB
  ES --> SEMB
  NEON -. shared connection .-> SEMB
  NEON -. shared connection .-> KEMB

  classDef io fill:#ECECEC,stroke:#555,color:#111;
  classDef rag fill:#E6F1FB,stroke:#378ADD,color:#0C447C;
  classDef plan fill:#EEEDFE,stroke:#7F77DD,color:#3C3489;
  classDef kpi fill:#FAECE7,stroke:#D85A30,color:#712B13;
  classDef gen fill:#EAF3DE,stroke:#639922,color:#27500A;
  classDef safe fill:#FAEEDA,stroke:#BA7517,color:#633806;
  classDef exec fill:#E1F5EE,stroke:#1D9E75,color:#085041;
  classDef expl fill:#FBEAF0,stroke:#D4537E,color:#72243E;
  classDef sup fill:#F1EFE8,stroke:#888,color:#2C2C2A;
  classDef off fill:#F4F4F2,stroke:#999,color:#2C2C2A;
  classDef store fill:#ffffff,stroke:#555,color:#111,stroke-dasharray:4 3;
```

## Subsystems (the boxes)
- **RAG · Schema Retrieval** (`retriever.py`, `embeddings.py`) — finds the few relevant table
  docs from Neon `schema_embeddings`; lexical token-overlap fallback when offline.
- **Planning** (`planner.py`) — rules-only `intent` / `time_grain` / `entities` (no model call).
- **KPI Matching** (`kpi_matcher.py`) — top-8 from `kpi_embeddings`, similarity gate, then either
  the deterministic resolver (literal KPI name present) or the **LLM judge** over the top-5
  (paraphrases), which can also answer **NONE** to fall back to schema-only.
- **SQL Generation** (`prompts.py`, `generate_sql.py`) — composes schema + plan + KPI recipe and
  generates one SELECT (`gpt-4o-mini`).
- **Safety / Validation** (`validator.py`) — SELECT/WITH only, blocks writes, appends `LIMIT`.
- **Execution** (`query_runner.py`) — runs read-only on PostgreSQL; returns rows or an error.
- **Explanation** (`explain_results.py`) — turns rows into a plain-English answer.
- **Support** (`cache.py`, `logger.py`) — SQL/result cache and the query log; always on.
- **Offline builds** (`embed_kpis.py`, `embed_schema.py`, `kpi_catalog.json`, `neon.py`) —
  hash-gated builds of the two pgvector indexes; persistent, so restarts don't re-embed.

## Execution sequence
1. Embed the question **once** and share the vector with both pgvector reads.
2. Retrieve schema context from Neon `schema_embeddings` (lexical fallback offline).
3. Build the deterministic plan (`intent`, `time_grain`, entities).
4. Retrieve top-8 KPI candidates; apply the 0.30 similarity gate.
5. Resolve: literal KPI name → deterministic winner; otherwise the LLM judge picks one of the
   top-5 or NONE; judge unavailable → deterministic winner. Apply the leaderboard guardrail.
6. Compose the prompt (schema + plan + optional KPI recipe) and generate SQL — or a blocked
   message for blocked KPIs.
7. Validate + `LIMIT`, execute read-only; on a DB error, `fix_sql()` retries once.
8. Explain the rows in plain English and return the answer.

## Reduced detail (kept off this diagram)
- Per-function helpers inside each module (e.g. `_pgvector_table_docs`, `_resolve_candidates`,
  `_get_pool`) — see the interactive System Map for the function-level drill-down.
- The eval harnesses (`app/eval/*`) and Streamlit documentation tabs are out of scope here.
