# Layer 1 Implementation Scope (Step 1 Restart)

## Goal
Build a reliable NL-to-SQL layer with broad schema coverage by grounding SQL generation in deterministic schema context (tables, columns, joins), while treating KPIs as optional semantic accelerators.

## Inputs Used for This Step 1
- `- for me/ATHL KPI Framework - KPI.csv` (parsed and included).
- `data/neondb/sql_create_tables/athl_raw_tables_postgres.sql` (source-of-truth schema for current table coverage).
- `- for me/ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (parsed).
- `- for me/ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (parsed).

## Confirmed Architecture Decisions
- Deterministic schema grounding is the core path.
- KPI retrieval is optional, not required for baseline SQL generation.
- Keep canonical KPI ontology small in Layer 1 (high-value metrics only).
- Keep full canonical KPI semantic layer for v2.1.

## Layer 1 Deliverables
1. Single retrieval/context pass (already implemented in Step 2):
   - one retrieval call per question,
   - one context payload reused by generate/fix/debug.
2. Detailed schema docs generated from DDL (`athl_raw_tables_postgres.sql`):
   - table metadata,
   - typed columns,
   - PKs/FKs/unique keys,
   - join graph,
   - time columns and status enums (where inferable).
3. Prompt redesign for deterministic SQL grounding + query intent patterning.
4. Lightweight query intent planner:
   - count/sum/avg-per-entity/top-k/trend/cohort/join-lookup.
5. Offline eval harness for SQL correctness.

## KPI Strategy (Layer 1)
- Tier A (canonical now): high-value, correctness-critical KPIs with explicit definitions.
- Tier B (supported via schema grounding): broad analytics questions without KPI-specific ontology.
- Tier C (not yet measurable): KPIs requiring event/log tables that do not yet exist.

## Product-Driven Priority KPIs (from Dashboard + Leaderboard docs)

### Priority 1: customer-facing token and issuer analytics (implement first)
- Token overview metrics for ATHLScan and issuer purchase pages:
  - current price, 24h price change, volume, holders, launch date.
- Issuer performance metrics:
  - total raised, total sold, supply remaining, revenue trend.
- Fan dashboard metrics:
  - wallet balances, holdings value trends, referral rewards summary.
- Token leaderboard metrics:
  - most traded, top gainers, most holders, time-window views.

### Priority 2: onboarding and verification analytics
- Funnel progression and conversion metrics:
  - signup start/completion, waitlist progression, issuer activation.
- Verification metrics:
  - social verification success/retry/failure reasons,
  - identity verification opt-in/pass/completion/manual review.

### Priority 3: engagement and personalization inputs
- Athlete discovery and momentum signals:
  - follower growth velocity, profile views, watchlist interactions.
- Leaderboard scoring components:
  - token performance, engagement signals, profile activity, consistency.

### Priority 4: ops/risk event-heavy analytics (deferred until event tables exist)
- Login/MFA/security anomaly dashboards.
- Incident/outage/job pipeline metrics.
- Compliance audit event timelines and support workflow metrics.

## KPI Availability Snapshot from Current Schema

### Tier A candidates (tables exist; good for canonical KPI definitions now)
- Identity verification: opt-in, pass/completion, manual review, alias confidence.
- Social verification: completion/success by platform, retry counts, failure reasons.
- Onboarding/waitlist: signups over time, approval rate, activation rate, waitlist conversion.
- Issuer segmentation: issuer type distribution, profile completion by type/sport/category.
- Finance/trading basics: amount raised vs target, percent supply sold, daily revenue trends.

### Tier C gaps (likely need future tables/events)
- Login/session metrics: login attempts, failures by reason, session duration, timeout rate.
- MFA flow metrics: success/lockout/recovery/backup-code usage.
- Referral link funnel metrics: link creation/click source/active links (if no event table).
- Support contact rate and anomaly detection events (if no dedicated event logs).

## Leaderboard Implications for Layer 1 SQL
- Support default leaderboard query templates first:
  - overall top, trending (time-window momentum), earnings-based, category/sport.
- Use deterministic SQL patterns for leaderboard outputs:
  - fixed time windows (24h, 7d, 30d, all-time),
  - explicit ranking (`ROW_NUMBER`/`RANK`) over grounded metrics,
  - explicit filters for sport/team/region/issuer type.
- Defer full personalized/gamified ranking to v2.1+ where event and behavior data are richer.

## Query Intent Categories (Layer 1)
- `count`: totals and entity counts.
- `sum`: additive business values (revenue, payout, quantity).
- `avg_per_entity`: two-stage aggregation (e.g., average actions per issuer).
- `top_k`: rankings by metric.
- `trend`: daily/weekly/monthly grouped metrics.
- `cohort`: progression by signup or onboarding phase.
- `join_lookup`: enrichment/filter joins across issuer/profile/token/transaction domains.

## Success Criteria
- One retrieval/context build per user question in runtime path.
- SQL generation and SQL fix path use the same context string.
- Eval suite in place with baseline category-level pass rates.
- KPI layer only activates for approved Tier A canonical KPIs.
- Priority-1 dashboard and leaderboard query classes are covered in offline eval.

## Next-Step Dependencies
- Define final Tier A canonical KPI list (10-15 KPIs) with exact formulas and ownership.
- Confirm which event streams/tables will exist in Layer 1 vs deferred to v2.1.

## Initial Eval Harness Requirements (next phase)
- 40-60 NL questions spanning all intent categories.
- Assertion-based validation (semantic, not exact SQL text):
  - required tables,
  - required join keys,
  - required filters,
  - required aggregation pattern,
  - optional time grain expectation.

# From the chat:

Suggested execution order (practical)
Step 1 (requirements + old docs extraction)
Step 2 (single-context refactor)
Step 3 (schema-doc generator)
Step 5 (prompt rewrite)
Step 4 (planner integration)
Step 6 (optional KPI layer)
Step 7–8 (eval + tuning)
Step 9 (docs)