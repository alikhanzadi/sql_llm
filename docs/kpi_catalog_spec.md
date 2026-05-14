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

## Entry Contract
Each KPI record in `kpis` must include:

- `kpi_id`, `name`, `category`, `status`, `owner_team`
- `business_definition`
- `time_grains`, `dimensions`
- `required_tables`, `required_columns`, `required_joins`
- `filters_defaults`
- `sql_recipe`
- `example_questions`
- `quality_notes`
- `source_refs`
- `missing_dependencies`
- optional `aliases`
- optional `tier` (`tier_1` or `tier_2`)

## Validation Rules
Implemented in `app/rag/catalog/kpi_catalog.py`:

1. `kpi_id` must be unique.
2. `status` must be one of `active`, `draft`, `blocked_by_missing_data`.
3. `tier` (if present) must be `tier_1` or `tier_2`.
4. `time_grains` must be subset of `day`, `week`, `month`, `all_time`.
5. Active KPIs require non-empty `required_tables`, `required_columns`, and `example_questions`.
6. `blocked_by_missing_data` requires non-empty `missing_dependencies`.

## Planner + Matcher Runtime Behavior
Execution order:
1. `plan_query()` in `app/llm/planner.py`
2. `match_kpi()` in `app/llm/kpi_matcher.py`
3. Prompt composition in `app/llm/prompts.py`
4. SQL generation/fix in `app/llm/generate_sql.py`

Matcher guardrails:
- Confidence threshold: `MATCH_THRESHOLD = 0.58`
- Ambiguity guard: `AMBIGUOUS_MARGIN = 0.03`
- Leaderboard guardrail: leaderboard KPIs only match ranking-style questions.
- Tier preference: `tier_1` gets slight positive bias; `tier_2` gets slight negative bias.

Routing outcomes:
- **No confident match** -> schema-only path.
- **Matched + active** -> inject KPI context (`definition`, joins, recipe).
- **Matched + blocked** -> return safe explanatory SQL row (`blocked_kpi_message`) instead of fabricated KPI SQL.

## Current Catalog Snapshot
Based on current `kpi_catalog.json`:

- `tier_1 active`: 12
- `tier_1 blocked_by_missing_data`: 6
- `tier_2 active`: 10
- total canonical KPIs: 28

## How To Extend Eval Cases (Short)
Offline harness:
- Runner: `app/eval/run_planner_kpi_eval.py`
- Cases: `app/eval/planner_kpi_cases.json`

To add a case:
1. Add a new object under `cases` with `id` and `question`.
2. Set expected fields:
   - `expected_intent`
   - `expected_time_grain`
   - `expected_kpi_id` (`null` for schema fallback)
   - optional `expected_kpi_status`
3. Run: `python app/eval/run_planner_kpi_eval.py`
4. Keep both positive (active/blocked KPI) and negative (fallback) cases.

## Versioning
- Treat this file as behavioral spec.
- Treat `kpi_catalog.json` as runtime truth.
- Update both when changing routing logic, thresholds, tiering policy, or entry contract.
