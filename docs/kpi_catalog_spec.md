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

Matcher guardrails:
- Confidence threshold: `MATCH_THRESHOLD = 0.58`
- Ambiguity guard: `AMBIGUOUS_MARGIN = 0.03`
- Leaderboard guardrail: leaderboard KPIs only match ranking-style questions
  (`requires_ranking` or leaderboard language).

Ambiguity resolution (when candidates fall within `AMBIGUOUS_MARGIN`):
1. **Specificity tiebreak** — among all candidates within the margin, the one whose
   longest exact name/alias substring appears in the question wins (handles the 0.99
   score cap collapsing several strong matches).
2. **Revenue cluster default** — if the near-tie is inside the revenue cluster
   (`total_token_revenue`, `issuer_revenue`, `platform_fee_revenue`) or the top two
   differ in `value_basis`, resolve to the cluster default `total_token_revenue`
   (bare "revenue").
3. Otherwise fall back to the schema-only path.

There is **no tier-based score bias** (removed with the flat-catalog migration).

Routing outcomes:
- **No confident match** -> schema-only path.
- **Matched + active** -> inject KPI context (`definition`, joins, recipe, `value_basis`).
- **Matched + blocked** -> return safe explanatory SQL row (`blocked_kpi_message`) instead of fabricated KPI SQL.

## Current Catalog Snapshot
Based on current `kpi_catalog.json` (version 2.0.0):

- total canonical KPIs: **62** (all `active`)
- by section: A 17, B 12, C 22, D 7, E 4
- `value_basis` in use: `token_revenue_gross`, `issuer_net`, `platform_fee`

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
4. Keep both positive (active KPI) and negative (fallback) cases.

## Doc Generation (anti-drift)
- `app/rag/catalog/generate_kpi_docs.py` renders `docs/kpi_inventory_grouped_by_section.md`
  from the catalog, grouped by the `section` field. Re-run after any catalog edit.
- `kpi_canonical_list.md` (source of truth) and `kpi_canonical_overview.md` (reader
  companion, hand-maintained) must agree with the catalog's `section` assignments.

## Versioning
- Treat this file as behavioral spec.
- Treat `kpi_catalog.json` as runtime truth.
- Update both when changing routing logic, thresholds, resolution behavior, or the entry contract.
