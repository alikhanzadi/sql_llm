# ATHL North Star Executive Dashboard Handoff

Use this document to resume the ATHL executive dashboard project in another Codex session or on another computer.

## Current Goal

Create and refine a minimal, modern, CEO-level North Star dashboard for ATHL. The dashboard should surface the most important business health metrics from the currently available static data. It should avoid unsupported metrics that require missing product-event, revenue-ledger, treasury, support, or order-book systems.

## Business Context

ATHL is a fan-token marketplace for athletes and creators. The executive dashboard should focus on:

- Marketplace liquidity and transaction activity
- User growth and trader participation
- Issuer ecosystem health
- Token economics and revenue momentum
- Trust, verification, and platform risk

The current best North Star metric is **Token Economic Activity (TEA)**:

```text
TEA = SUM(transactions.total_amount_usdc)
WHERE status = 'completed'
AND timestamp is within the selected period
```

In the implemented dashboard, TEA is shown as latest-30-day completed USDC transaction volume.

## Source Documents Used

The product documents are in `ATHL-16/`.

Most relevant inputs:

- `ATHL-16/ATHL Platform Wiki (v2).pdf`
- `ATHL-16/ATHL Core Products Roadmap.pdf`
- `ATHL-16/ATHL Product List - Scoping.rtf`
- `ATHL-16/ATHL Data Infrastructure Blueprint_ Internal - Ali.pdf`
- `ATHL-16/ATHL KPI Framework.xlsx`
- `ATHL-16/Athl North Star Executive Dashboard Kpis.pdf`

The key source for the dashboard was `Athl North Star Executive Dashboard Kpis.pdf`, especially section `6. PRIORITIZED MVP KPI LIST FOR THE FIRST VERSION`.

Phase 1 MVP KPIs from that document:

1. Gross Transaction Volume
2. Monthly Active Traders
3. Total Token Revenue
4. Active Tokens
5. Net New Users
6. Active Issuers
7. Verification Pass Rate
8. Daily Transactions
9. Repeat Buyer Rate
10. Token Liquidity Velocity
11. Top Tokens by Volume
12. Wallet Funding Rate
13. Issuer Revenue Trend
14. Revenue Concentration
15. Suspended Accounts

## Available Data

The project currently uses static dummy CSV data in:

```text
data/tables/
```

Important tables:

- `transactions.csv`
- `tokens.csv`
- `users.csv`
- `issuers.csv`
- `issuer_daily_revenue.csv`
- `user_wallet.csv`
- `user_token_wallet.csv`
- `identity_verification.csv`
- `social_verification.csv`
- `issuer_post_signup.csv`
- `issuer_preferences.csv`
- `athlete_profile.csv`

Reference schema files:

- `data/sql_create_tables/athl_raw_tables_postgres.sql`
- `data/neondb/generate_and_load_data_neon.py`
- `data/neondb/generate_and_load_data_neon.ipynb`

Important limitation: the current dashboard is intentionally built from static CSVs, not live production data.

## Implemented Files

Main implementation:

```text
app/ui.py
```

Important anchors in `app/ui.py`:

- `_executive_dashboard_data()` starts around line 328.
- `render_executive_dashboard()` starts around line 733.
- Sidebar page list includes `Executive Dashboard` around line 1200.
- Page routing renders `render_executive_dashboard()` around line 1214.

The dashboard was added as the first/default navigation item:

```text
Executive Dashboard
Data Overview
Schema Explorer
ERD and Lineage
Metric Definitions
Ask the Data
Onboarding Guide
```

## KPI Implementation Details

The dashboard calculates metrics in `_executive_dashboard_data()` using `pandas` and local CSV tables.

Period logic:

- Finds `latest_date` from `transactions.timestamp`.
- Defines latest 30 days as `latest_date - 29 days` through `latest_date`.
- Defines prior 30 days as the immediately preceding 30-day window.
- Shows deltas vs prior 30 days where possible.
- Filters incomplete partial-month buckets out of monthly trend charts to avoid misleading visual cliffs.

Current KPI definitions:

| KPI | Current implementation |
| --- | --- |
| Token Economic Activity / Gross Transaction Volume | Sum of completed `transactions.total_amount_usdc`, latest 30 days |
| Monthly Active Traders | Distinct buyers and sellers in completed transactions, latest 30 days |
| Total Token Revenue | Sum of `tokens.total_revenue` |
| Active Tokens | Distinct tokens with completed trading, latest 30 days |
| Net New Users | Distinct users created in latest 30 days |
| Active Issuers | Distinct token issuers with traded tokens in latest 30 days |
| Verification Pass Rate | Passed identity checks / completed identity checks |
| Daily Transactions | Average completed transactions per day, latest 30 days |
| Repeat Buyer Rate | Buyers with more than one completed transaction / active buyers |
| Token Liquidity Velocity | Latest-30-day traded quantity / total held token quantity |
| Top Tokens by Volume | Top 10 token symbols by latest-30-day completed volume |
| Wallet Funding Rate | Funded wallets / total users |
| Issuer Revenue Trend | Daily platform-wide sum from `issuer_daily_revenue` |
| Revenue Concentration | Top 10 tokens' share of latest-30-day GTV |
| Suspended Accounts | Count of users with `SUSPENDED`, `LOCKED`, or `DISABLED` account status |

## Dashboard Layout

The page is intentionally executive-level and sparse:

1. Header and operating-window explanation
2. North Star band for Token Economic Activity
3. KPI card grid
4. Marketplace Momentum charts
5. Growth Engine and Issuer Ecosystem charts
6. Issuer Revenue Trend and Trust/Risk charts
7. Current Data Coverage section with caveats

The CSS for this view is embedded in `CUSTOM_CSS` in `app/ui.py`.

Design direction:

- Minimal, clean, executive BI feel
- White/neutral base
- Teal, blue, gold, coral, and muted purple accents
- No marketing hero or decorative background
- No nested cards
- Cards only for KPI summaries

## Known Data Caveats

Do not overstate these metrics as production truth.

Known caveats:

- Data is dummy/static.
- The latest transaction date in the dummy data is used as the dashboard clock.
- Platform revenue is not truly available because there is no platform revenue ledger.
- Retention, DAU/WAU/MAU, session behavior, funnels, feature adoption, support, and product engagement are blocked by missing event instrumentation.
- Margin, treasury, runway, fee revenue, and accounting metrics are blocked by missing financial infrastructure.
- Marketplace spread, slippage, depth, and order-book quality are blocked by missing order-book or AMM data.
- Social/community virality and referral effectiveness are blocked or partial because attribution/event tables are missing.

## Verification Already Performed

Commands run:

```bash
codex14-venv/bin/python -m py_compile app/ui.py
codex14-venv/bin/streamlit run app/ui.py --server.port 8501 --server.headless true
```

The Streamlit server required sandbox escalation for local port binding in Codex Desktop.

Browser QA performed:

- Opened `http://localhost:8501`.
- Confirmed `Executive Dashboard` is the default selected navigation page.
- Confirmed KPI cards render.
- Confirmed charts render.
- Confirmed the artificial partial-month chart cliff was removed.
- Confirmed no horizontal overflow at desktop width.

## How To Run Locally

From the project root:

```bash
codex14-venv/bin/streamlit run app/ui.py --server.port 8501 --server.headless true
```

Then open:

```text
http://localhost:8501
```

If the venv is not present on the new computer, install dependencies first:

```bash
python3 -m venv codex14-venv
codex14-venv/bin/pip install -r requirements.txt
codex14-venv/bin/streamlit run app/ui.py --server.port 8501 --server.headless true
```

## Suggested Next Steps

High-priority refinements:

1. Add an explicit period selector:
   - Latest 7 days
   - Latest 30 days
   - Latest 90 days
   - All time
2. Add a compact KPI methodology expander so each metric is auditable.
3. Add a small "blocked executive metrics" panel for missing production data systems.
4. Add stronger mobile QA; Streamlit columns stack, but visual spacing should be checked on narrow viewports.
5. Add a deterministic test or smoke script for `_executive_dashboard_data()`.

Data-model improvements needed before this can become a mature executive dashboard:

1. Product analytics event tracking, such as Segment, RudderStack, PostHog, or Mixpanel.
2. Platform revenue ledger for fees, margin, and actual monetization.
3. Treasury and accounting layer.
4. Marketplace order-book or AMM/liquidity-depth data.
5. Community, referral, and engagement attribution layer.

## Prompt For Another Codex Session

You can paste this into another Codex session:

```text
You are resuming the ATHL North Star Executive Dashboard project.

Read docs/executive_dashboard_handoff.md first. Then inspect app/ui.py, especially _executive_dashboard_data() and render_executive_dashboard().

Do not replace the dashboard with a generic landing page. Keep it CEO-level, minimal, visually clean, and grounded in the static CSV data under data/tables/.

The primary source KPI list is section 6 of ATHL-16/Athl North Star Executive Dashboard Kpis.pdf. The current implementation already maps the Phase 1 MVP KPIs to available data.

Your next job is to refine and harden the dashboard without inventing unsupported metrics. Preserve the existing documentation, schema explorer, lineage, metric catalog, and Ask the Data pages.
```
