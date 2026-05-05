# Module Call Graph

This high-level diagram shows which modules call into other modules.

```mermaid
flowchart LR
  M0["app.main"] --> M1["app.cache"]
  M0 --> M2["app.db.query_runner"]
  M0 --> M3["app.db.validator"]
  M0 --> M9["app.db.schema"]
  M0 --> M4["app.llm.generate_sql"]
  M0 --> M5["app.llm.explain_results"]
  M0 --> M6["app.logger"]
  M0 --> M7["app.rag.context_service"]
  M0 --> M8["app.rag.ingest"]

  M2 --> M9

  M7 --> M11["app.rag.retriever"]
  M8 --> M12["app.rag.embeddings"]
  M8 --> M13["app.rag.vector_store"]
  M8 --> M9

  M11 --> M12
  M11 --> M13

  M14["app.rag.retriever_experimental"] --> M12
  M14 --> M13

  M12 --> M9
  M13 --> M9
```

## Notes

- Scope: module-to-module calls discovered from `app/**/*.py`.
- This is intended for architecture-level discussion and presentations.
