# KPI Processing Flow — Phase 1.7 (IMPLEMENTED 2026-06-22)

> **Status: DELIVERED.** The convergence work described here is implemented. The current,
> authoritative flow is `kpi_processing_flow.md`. This file is kept as the design record and
> a list of remaining (smaller) future ideas.

## What was delivered
1. **Embed the question once** and share it across schema retrieval and KPI matching
   (`embed_query` / `embed_query_safe`; threaded as a `query_embedding` through
   `get_retrieval_context`, `retrieve_relevant_docs`, `match_kpi`, `build_sql_planning_context`).
   Embedding calls per question: **2 → 1**.
2. **Single backend** — schema docs migrated to Neon `pgvector` (`schema_embeddings`, built by
   `embed_schema.py`). **Chroma removed entirely** (`vector_store.py`, `ingest.py`,
   `retriever_experimental.py` deleted; `chromadb` dropped; no more Streamlit cold-start re-embed).
3. **LLM judge over the shortlist** — `gpt-4o-mini` picks one of the top-5 or NONE, fired only
   when there is no literal name/alias signal (ambiguous-only). Closes both gaps the numeric
   gate could not: precision **72.6% → 93.5%** and schema-exploration abstention **5/12 → 12/12**.

Also delivered (prerequisite): **shared Neon resolver** `app/db/neon.py` resolving
`DATABASE_URL` → `st.secrets["postgres_neon"]`, which closed a Streamlit Cloud gap where the
matcher silently fell back to lexical (~4.8%) because `DATABASE_URL` was not in `os.environ`.

## Remaining future ideas (not in scope of Phase 1.7)
- **Precision ceiling**: 4 paraphrase misses remain (3 genuine near-synonyms; 1 outside top-5).
  Raising `JUDGE_TOPK` or improving `embed_text` could lift the recall@k ceiling.
- **Legacy metric docs**: the 30 metric docs in `schema_docs` predate the 62-KPI canonical
  catalog and are still matched lexically; review whether to retire/fold/embed them.
- **Catalog→eval coupling**: optionally fold an `issuers`-style "decorative table" lint into the
  catalog validator so recipe/required_tables drift is caught without an LLM eval run.
