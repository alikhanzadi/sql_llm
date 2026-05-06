# KPI Catalog Specification (v1)

## Purpose
This catalog defines canonical business KPIs separately from schema docs.

- Schema docs answer: what data exists.
- KPI catalog answers: how business metrics are defined and computed.

This separation is the standard approach for maintainability and auditability.

## Scope
This v1 spec supports Layer 1:

- deterministic SQL generation remains schema-grounded by default
- KPI mapping is optional and only used when a query clearly matches a canonical KPI

## Entry Contract
Each KPI entry must include:

- `kpi_id`: stable snake_case identifier
- `name`: human-readable KPI name
- `category`: one of `onboarding`, `verification`, `trading`, `finance`, `leaderboard`, `security`, `referrals`
- `status`: one of `active`, `draft`, `blocked_by_missing_data`
- `owner_team`: business owner team label
- `business_definition`: plain-language definition
- `time_grains`: supported grains from `day`, `week`, `month`, `all_time`
- `dimensions`: allowed slice dimensions
- `required_tables`: minimum table list needed
- `required_columns`: minimum column list needed
- `required_joins`: explicit join requirements
- `filters_defaults`: default filters or assumptions
- `sql_recipe`: structured computation recipe (pattern + numerator/denominator/aggregation)
- `example_questions`: at least one NL question that should map to this KPI
- `quality_notes`: caveats and data quality assumptions
- `source_refs`: where the KPI came from (CSV/PDF references)
- `missing_dependencies`: required missing datasets (empty for active KPIs)
- `aliases`: optional synonym list for query matching

## Validation Rules

1. `kpi_id` must be unique.
2. `status` must be valid enum.
3. Active KPIs must have:
   - non-empty `required_tables`
   - non-empty `required_columns`
   - at least one `example_questions` item
4. `blocked_by_missing_data` must have non-empty `missing_dependencies`.
5. `time_grains` must include only valid values.
6. `required_joins` should be explicit table-column equalities when joins are needed.

## Lifecycle

- `draft`: definition exists, still being reviewed.
- `active`: approved for production query mapping.
- `blocked_by_missing_data`: approved conceptually, but cannot be computed reliably yet.

## How Prompt and Planner Should Use This Catalog

1. Planner first classifies query intent and extracts entities.
2. KPI matcher checks if query maps clearly to one canonical KPI:
   - exact/alias name hit, or
   - high-confidence semantic match plus compatible dimensions/time grain
3. If matched:
   - inject `business_definition`, `required_tables`, `required_joins`, and `sql_recipe` into SQL-generation context
4. If no clear match:
   - skip KPI layer and continue with schema-grounded generation

This prevents KPI coupling from blocking broad SQL coverage.

## Integration Guardrails and Examples

- KPI match should be opt-in by confidence.
- If confidence is low, do not force KPI route.
- Never allow KPI context to override hard schema constraints.
- For blocked KPIs, avoid generating fabricated SQL for unavailable data.
- Log mapping decisions for debugging (`matched_kpi_id`, confidence, fallback reason).

Example behavior:

- Query: "What is ID verification pass rate by provider?"
  - Expected path: KPI matched (`id_verification_pass_rate`) and used to guide SQL.
- Query: "Show login attempts by day"
  - Expected path: KPI matched but blocked (`login_attempt_volume`) -> return dependency warning.
- Query: "Top tokens traded in the last 7 days"
  - Expected path: KPI matched (`token_leaderboard_most_traded`) or schema fallback if confidence is low.

## Versioning

- Store catalog in `app/rag/catalog/kpi_catalog.json`.
- Keep spec and changelog in git.
- Changes to formulas or required joins should increment a catalog version field.
