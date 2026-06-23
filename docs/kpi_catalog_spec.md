# KPI Catalog Specification (v2)

## Purpose
This spec defines the runtime contract for canonical KPI routing in ATHL NL-to-SQL.

- Schema docs answer: what data exists.
- KPI catalog answers: how business metrics are defined and when to route to them.
- Planner + matcher decide whether KPI context should be injected or skipped.

Runtime source of truth:
- `app/rag/catalog/kpi_catalog.json`

Runtime validator:
- `app/rag/catalog/kpi_catalog.py`

## Scope
Layer-1 behavior:
- SQL generation is schema-grounded by default.
- KPI mapping is optional and confidence-gated.
- Blocked KPIs must never generate fabricated business SQL.

The catalog is **flat — there are no tiers.** Matcher priority among look-alike
metrics is handled by deliberate aliases/examples plus per-cluster default-resolution
and a specificity tiebreak (see Matcher Runtime Behavior), not by a tier field.

## Entry Contract
Each KPI record in `kpis` must include:

- `kpi_id`, `name`, `category`, `section`, `status`, `owner_team`
- `business_definition`
- `time_grains`, `dimensions`
- `required_tables`, `required_columns`, `required_joins`
- `filters_defaults`
- `sql_recipe`
- `example_questions`
- `quality_notes`
- `source_refs`
- `missing_dependencies`
- `value_basis` — **required for active `finance` KPIs**; optional elsewhere
- optional `aliases`
- optional `multi_table_rationale` — required for multi-table active KPIs that
  declare no `required_joins` (e.g. aggregate-difference metrics)

Field notes:
- `section` ∈ `{A, B, C, D, E}` — the north star executive section. This is the
  **authoritative grouping** consumed by `generate_kpi_docs.py`; `kpi_canonical_list.md`
  and `kpi_canonical_overview.md` must agree with it.
- `category` is an orthogonal tag that drives runtime rules: `finance` requires a
  `value_basis`; `leaderboard` activates the ranking guardrail. It is **not** the
  section and must not be used for grouping.
- `value_basis` ∈ `{token_revenue_gross, issuer_net, platform_fee}` — prevents
  gross/net/fee revenue confusion. See the revenue family in `kpi_canonical_overview.md`.

## Validation Rules
Implemented in `app/rag/catalog/kpi_catalog.py`:

1. `kpi_id` must be unique.
2. `status` must be one of `active`, `draft`, `blocked_by_missing_data`.
3. `section` must be one of `A`, `B`, `C`, `D`, `E`.
4. `time_grains` must be a subset of `day`, `week`, `month`, `all_time`.
5. Active KPIs require non-empty `required_tables`, `required_columns`, and `example_questions`.
6. `blocked_by_missing_data` requires non-empty `missing_dependencies`.
7. `value_basis` (if present) must be valid; active `finance` KPIs must declare one.
8. A multi-table active KPI must declare `required_joins` or a `multi_table_rationale`.

## Planner + Matcher Runtime Behavior
Execution order:
1. `plan_query()` in `app/llm/planner.py`
2. `match_kpi()` in `app/llm/kpi_matcher.py`
3. Prompt composition in `app/llm/prompts.py`
4. SQL generation/fix in `app/llm/generate_sql.py`

`match_kpi()` is **embedding-first** with a lexical fallback:

Primary — embedding shortlist + LLM judge:
1. Embed the question once (`text-embedding-3-small`), shared with schema retrieval.
2. Retrieve the `KPI_TOPK = 8` nearest KPIs from the Neon `pgvector` `kpi_embeddings`
   table (cosine). Recall@8 ≈ 98% on the held-out paraphrase set.
3. **Similarity gate** `SIMILARITY_GATE = 0.30`: if the top candidate is below it, return
   schema-only (tuned against `paraphrase_cases.json` / `negative_cases.json`).
4. **Deterministic fast-path** — if any candidate's name/alias appears literally in the
   question (canonical vocabulary), resolve among candidates within `SIMILARITY_MARGIN = 0.03`
   of the top by specificity (longest exact substring) → revenue-cluster default → otherwise
   the top candidate. **No LLM call.**
5. **LLM judge** (`JUDGE_MODEL = gpt-4o-mini`, `JUDGE_TOPK = 5`) — when there is no literal
   signal (a paraphrase) or the question may be non-KPI, the judge picks one of the top-5 or
   NONE: `pick` → that KPI; `NONE` → schema-only (this abstains on schema-exploration
   questions the numeric gate cannot separate); judge unavailable → deterministic winner.

Fallback — lexical (`_lexical_match_kpi`, used when OpenAI/Neon are unavailable):
- Token-overlap scoring with `MATCH_THRESHOLD = 0.58`, `AMBIGUOUS_MARGIN = 0.03`, and the
  same specificity/cluster resolution. There is **no tier-based score bias** (removed with
  the flat-catalog migration).

Guardrails (both paths):
- Leaderboard guardrail: leaderboard KPIs only match ranking-style questions
  (`requires_ranking` or leaderboard language).

Routing outcomes:
- **No confident match / below gate** -> schema-only path.
- **Matched + active** -> inject KPI context (`definition`, joins, recipe, `value_basis`, `raw_sql`).
- **Matched + blocked** -> return safe explanatory SQL row (`blocked_kpi_message`) instead of fabricated KPI SQL.

## Embedding Indexes (Neon pgvector — single backend)
- `kpi_embeddings(kpi_id, section, model, embedding vector(1536), embed_text, content_hash, updated_at)`
  — KPI routing index. Build: `app/rag/catalog/embed_kpis.py` (`embed_text` = name +
  definition + aliases + example_questions per KPI, hash-gated). Re-run after catalog edits.
- `schema_embeddings(table_name, model, embedding vector(1536), embed_text, content_hash, updated_at)`
  — schema-grounding index (the 13 table docs). Build: `app/rag/catalog/embed_schema.py`
  (`embed_text` = the formatted table block, hash-gated). Re-run after schema-doc edits.
- Connection: `app/db/neon.py` resolves `DATABASE_URL` → else `st.secrets["postgres_neon"]`,
  so the matcher and schema retrieval work in CLI and on Streamlit Cloud (this closed a gap
  where the cloud matcher silently fell back to lexical).
- Persistent (survives Streamlit Cloud restarts), unlike the former local Chroma store
  (removed in Phase 1.7).

## Current Catalog Snapshot
Based on current `kpi_catalog.json` (version 2.0.0):

- total canonical KPIs: **62** (all `active`)
- by section: A 17, B 12, C 22, D 7, E 4
- `value_basis` in use: `token_revenue_gross`, `issuer_net`, `platform_fee`

## Eval Harnesses
- `app/eval/run_planner_kpi_eval.py` (+ `planner_kpi_cases.json`) — planner intent/grain
  and KPI routing regression on canonical-vocabulary questions.
- `app/eval/run_sql_correctness_eval.py` — catalog-driven, asserts generated SQL uses the
  required tables/joins/filters/aggregation per KPI (runs the real pipeline).
- `app/eval/run_paraphrase_eval.py` (+ `paraphrase_cases.json`, `negative_cases.json`) —
  held-out matcher precision on paraphrases and abstention on non-KPI questions
  (`--negatives`). Current: precision **93.5%** (with the LLM judge; was 72.6% deterministic-only)
  and negatives abstention **12/12**. Note: the embedding + judge path requires OpenAI + Neon,
  so run it with the project venv; the bare-env run exercises the lexical fallback.

To add a planner routing case: add `{id, question, expected_intent, expected_time_grain,
expected_kpi_id (null for fallback), optional expected_kpi_status}` and run the runner.

## Doc Generation (anti-drift)
- `app/rag/catalog/generate_kpi_docs.py` renders `docs/kpi_inventory_grouped_by_section.md`
  from the catalog, grouped by the `section` field. Re-run after any catalog edit.
- `kpi_canonical_list.md` (source of truth) and `kpi_canonical_overview.md` (reader
  companion, hand-maintained) must agree with the catalog's `section` assignments.

## Versioning
- Treat this file as behavioral spec.
- Treat `kpi_catalog.json` as runtime truth.
- Update both when changing routing logic, thresholds, resolution behavior, or the entry contract.
