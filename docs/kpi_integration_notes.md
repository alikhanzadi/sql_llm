# KPI Integration Notes (Prompt and Planner)

## Goal
Use canonical KPIs as an optional accelerator, without making KPI mapping a hard dependency for SQL generation.

## Recommended Flow

1. Retrieve schema context (current default path).
2. Run intent planner to classify query pattern and entities.
3. Attempt KPI match against `app/rag/catalog/kpi_catalog.json`:
   - match by `kpi_id`, `name`, or `aliases`
   - require confidence threshold and compatible dimensions/time grain
4. If matched and KPI status is `active`:
   - inject KPI definition, required joins, and sql recipe into LLM context
5. If unmatched or blocked KPI:
   - fall back to schema-grounded generation only
   - if blocked KPI, return a clear explanation about missing data dependencies

## Prompt Composition Guidance

- Keep a separate prompt section for KPI context:
  - `Canonical KPI: <name>`
  - `Definition: <business_definition>`
  - `Required Joins: <required_joins>`
  - `Recipe: <sql_recipe>`
- Never allow KPI context to override hard schema constraints.
- For blocked KPIs, avoid fabricated SQL that pretends data exists.

## Guardrails

- KPI match should be opt-in by confidence.
- If confidence is low, do not force KPI route.
- Ensure every active KPI has at least one offline eval case.
- Log KPI mapping decisions for debugging (`matched_kpi_id`, confidence, fallback reason).

## Example Behavior

- Query: "What is ID verification pass rate by provider?"
  - Expected path: KPI matched (`id_verification_pass_rate`) -> guided SQL.

- Query: "Show login attempts by day"
  - Expected path: KPI matched but blocked (`login_attempt_volume`) -> explain missing event table.

- Query: "Top tokens traded in the last 7 days"
  - Expected path: KPI matched (`token_leaderboard_most_traded`) or schema fallback if confidence low.
