# Retrieval Test Checklist

> **🗄️ ARCHIVED (2026-06-23) — superseded by the automated eval suite.** Routing/retrieval
> regression is now covered by `app/eval/run_sql_correctness_eval.py`, `app/eval/run_paraphrase_eval.py`
> (+ `paraphrase_cases.json`, `negative_cases.json`), and `app/eval/run_planner_kpi_eval.py`. Also note
> the "Blocked KPI route" case below is no longer valid — the catalog currently has **0 blocked KPIs**
> (62/62 active). Kept only as a manual smoke-test reference.

Use this checklist to validate retrieval and routing behavior before changing retriever logic.

## How To Run
- Run each question through the app.
- Capture:
  - retrieved context (tables/metrics)
  - generated SQL (tables/joins/aggregations)
  - routing outcome (schema fallback vs active KPI vs blocked KPI)

## Test Queries

1) **Active KPI route**
- Question: `What is ID verification pass rate by provider this month?`
- Expect:
  - KPI match: `id_verification_pass_rate` (`active`)
  - tables centered on `identity_verification` (plus issuer join context if used)

2) **Blocked KPI route**
- Question: `Show login attempts by day`
- Expect:
  - KPI match: `login_attempt_volume` (`blocked_by_missing_data`)
  - blocked dependency response path (no fabricated event table SQL)

3) **Leaderboard query**
- Question: `Top tokens traded in the last 7 days`
- Expect:
  - ranking intent detected
  - leaderboard-compatible routing/query pattern with explicit window

4) **Non-leaderboard volume trend**
- Question: `How much token trading volume do we have by day?`
- Expect:
  - schema-grounded trend query
  - not forced into leaderboard route unless ranking language is explicit

5) **Schema fallback lookup**
- Question: `List issuers with their country and level`
- Expect:
  - no KPI mapping
  - clean lookup-style SQL with minimal joins

6) **Ambiguous metric wording**
- Question: `How many tokens traded per day?`
- Expect:
  - metric interpretation is consistent (units vs trade count)
  - aggregation matches question semantics

7) **Multi-table finance query**
- Question: `How much has each issuer raised versus target?`
- Expect:
  - correct cross-table join path
  - grouping at issuer level
  - no invented columns

8) **Low-signal prompt**
- Question: `Show performance details`
- Expect:
  - safe fallback behavior
  - no hallucinated tables/columns

## Pass / Fail Rubric
- **Pass**:
  - correct tables and join keys
  - correct KPI/fallback route
  - correct aggregation/time grain for intent
- **Fail**:
  - hallucinated schema
  - wrong KPI route (especially blocked KPI handling)
  - metric semantics mismatch
