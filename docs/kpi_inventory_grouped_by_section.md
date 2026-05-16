# KPI Inventory Grouped by Section

Status legend:
- `active`: computable with current schema
- `partial`: computable with caveats
- `blocked`: not currently operational (missing data/events)
- `deprecated`: intentionally removed from runtime catalog

Canonical legend:
- `canonical tier_1`: KPI exists in `app/rag/catalog/kpi_catalog.json` with `tier = tier_1`
- `canonical tier_2`: KPI exists in `app/rag/catalog/kpi_catalog.json` with `tier = tier_2`
- If a KPI is not listed below, it is currently non-canonical inventory coverage only.

## Canonical KPIs Included In This Inventory

### Verification and Trust
- `id_verification_opt_in_rate` - canonical tier_1, active
- `id_verification_pass_rate` - canonical tier_1, active
- `id_verification_completion_rate` - canonical tier_1, active
- `manual_review_rate` - canonical tier_1, active
- `social_verification_success_rate` - canonical tier_1, active
- `social_verification_retry_rate` - canonical tier_1, active
- `login_attempt_volume` - canonical tier_1, blocked
- `session_timeout_rate` - canonical tier_1, blocked
- `mfa_success_rate` - canonical tier_1, blocked
- `anomaly_detection_rate` - canonical tier_1, blocked
- `support_contact_rate` - canonical tier_1, blocked

### Trading, Revenue, and Token Performance
- `amount_raised_vs_target` - canonical tier_1, active
- `percent_supply_sold_30d` - canonical tier_1, active
- `issuer_daily_revenue` - canonical tier_1, active
- `token_leaderboard_most_traded` - canonical tier_1, active
- `total_platform_revenue` - canonical tier_2, active
- `active_trading_users` - canonical tier_2, active
- `participation_rate` - canonical tier_2, active
- `average_transaction_size_usdc` - canonical tier_2, active
- `average_tokens_per_transaction` - canonical tier_2, active
- `token_number_of_buyers` - canonical tier_2, active
- `average_selling_price` - canonical tier_2, active
- `total_purchases_by_user` - canonical tier_2, active

### Issuer and Supply
- `issuer_type_distribution` - canonical tier_1, active
- `profile_completion_rate_by_issuer_type` - canonical tier_1, active
- `tokens_issued_count` - canonical tier_2, active
- `total_supply_issued` - canonical tier_2, active

### Referral and Growth
- `referral_link_click_conversion` - canonical tier_1, blocked

## Deprecated Runtime Items
- `waitlist_approval_rate` - deprecated (removed from runtime catalog)
- `issuer_activation_rate` - deprecated (removed from runtime catalog)

## Dashboards Product Analytics

### Fan Journey Analytics 
**Blocked**
- `fan_signup_funnel_conversion` - non-canonical
  - Calculation: stepwise conversion `step_users(n)/step_users(n-1)` across `landing -> email -> OAuth -> KYC -> purchase`.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Fan Journey Analytics`).
- `onboarding_dropoff_rate_by_step` - non-canonical
  - Calculation: `1 - (next_step_users/prior_step_users)` for each funnel step.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Fan Journey Analytics`).
- `visitor_to_wallet_connect_conversion` - non-canonical
  - Calculation: `wallet_connect_users / unique_visitors`.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Fan Journey Analytics`).
- `time_to_first_token_purchase` - non-canonical
  - Calculation: `first_purchase_ts - signup_ts` (median/avg).
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Fan Journey Analytics`).
- `homepage_to_purchase_funnel_conversion` - non-canonical
  - Calculation: `purchase_sessions / homepage_sessions` with ordered path `Homepage -> ATHLScan -> Issuer -> Purchase`.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Fan Journey Analytics`).
- `feature_click_metrics` - non-canonical
  - Calculation: event counts or CTR for `Add to Watchlist`, `Share Profile`, `View Perks`, referral click.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Fan Journey Analytics`).
- `embed_usage_and_conversion` - non-canonical
  - Calculation: `embed_clicks/embed_impressions` plus downstream `signup/purchase` attribution.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Fan Journey Analytics`).

### Issuer Activation and Engagement Analytics
**Active**
- `profile_completion_rate_by_issuer_type` - canonical tier_1
  - Calculation: `COUNT(issuers_with_completion>=threshold) / COUNT(issuers)` by issuer type.
  - Source: `app/rag/catalog/kpi_catalog.json`, `ATHL KPI Framework - KPI.csv`, `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf`.

**Blocked**
- `issuer_dashboard_login_frequency` - non-canonical
  - Calculation: login event count per issuer post-launch.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Issuer Activation & Engagement Analytics`).
- `issuer_referral_funnel_conversion` - non-canonical
  - Calculation: `referral_clicks -> signups -> purchases` conversion by issuer.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Issuer Activation & Engagement Analytics`).
- `issuer_feature_adoption_metrics` - non-canonical
  - Calculation: usage counts for embeds, media uploads, perk updates, social share.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Issuer Activation & Engagement Analytics`).

**Deprecated**
- `waitlist_approval_rate` - non-canonical
  - Calculation: `approved_waitlist / total_waitlist`.
  - Source: `ATHL KPI Framework - KPI.csv`.
- `issuer_activation_rate` - non-canonical
  - Calculation: `activated_waitlist / approved_waitlist`.
  - Source: `ATHL KPI Framework - KPI.csv`.

### Trading Behavior and Token Lifecycle
**Partial**
- `repeat_buyers_per_token` - non-canonical
  - Calculation: `COUNT(DISTINCT buyer_id where buy_count > 1)` per token.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Trading Behavior & Token Lifecycle`).

**Blocked**
- `average_token_holding_time` - non-canonical
  - Calculation: average `(exit_ts - first_buy_ts)` per lot/holder.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Trading Behavior & Token Lifecycle`).
- `sell_side_time_to_exit` - non-canonical
  - Calculation: average time from first buy to first sell/full exit.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Trading Behavior & Token Lifecycle`).
- `price_drop_before_sell` - non-canonical
  - Calculation: price delta in lookback window before sell event.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Trading Behavior & Token Lifecycle`).
- `price_volatility_vs_engagement` - non-canonical
  - Calculation: correlation(`volatility`, `engagement_metric`) by token/window.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Trading Behavior & Token Lifecycle`).
- `token_page_visits_vs_actions` - non-canonical
  - Calculation: compare/ratio of page visits to purchases/watchlist adds.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Trading Behavior & Token Lifecycle`).

### Product Usage by Platform and Segment
**Blocked**
- `active_sessions_by_device` - non-canonical
  - Calculation: `COUNT(DISTINCT session_id)` grouped by device.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Product Usage by Platform & Segment`).
- `conversion_rate_by_cohort` - non-canonical
  - Calculation: `converted_users / cohort_users` by source/segment/device.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Product Usage by Platform & Segment`).
- `session_length_by_page` - non-canonical
  - Calculation: avg `(session_end - session_start)` by route/page.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Product Usage by Platform & Segment`).
- `bounce_rate_by_page` - non-canonical
  - Calculation: `single_page_sessions / entry_sessions` by page.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Product Usage by Platform & Segment`).
- `wallet_connection_abandonment_rate` - non-canonical
  - Calculation: `(wallet_connect_started - wallet_connect_completed)/wallet_connect_started` by device.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Product Usage by Platform & Segment`).

### Experimentation and Growth Optimization
**Blocked**
- `ab_test_lift_issuer_page_layout` - non-canonical
  - Calculation: `conversion_treatment - conversion_control`.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Experimentation & Growth Optimization`).
- `ab_test_lift_buy_cta_copy` - non-canonical
  - Calculation: buy conversion lift by CTA variant.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Experimentation & Growth Optimization`).
- `social_proof_badge_conversion_lift` - non-canonical
  - Calculation: conversion delta with vs without social proof badge.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Experimentation & Growth Optimization`).
- `notification_or_gamification_lift` - non-canonical
  - Calculation: retention/purchase lift after nudge or gamified alert exposure.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Experimentation & Growth Optimization`).

### Retention Analysis
**Blocked**
- `retention_by_segment_d1_d7_d30` - non-canonical
  - Calculation: retained users at day `1/7/30` over cohort size by segment.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Retention Analysis`).
- `activation_behavior_retention_correlation` - non-canonical
  - Calculation: retention differences by activation behaviors (e.g., add 3+ tokens).
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Retention Analysis`).
- `reactivation_nudge_effectiveness` - non-canonical
  - Calculation: reactivated users after nudge / nudged users.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`2-1 Retention Analysis`).

## Dashboards Customer-Facing Dashboards

### Fan Dashboard
**Active**
- `wallet_balance_snapshot` - non-canonical
  - Calculation: current balances from `user_wallet` plus token holdings value.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-1 Fan Dashboard`), `docs/database_schema_taxonomy.md`.
- `holdings_table_core_metrics` - non-canonical
  - Calculation: per token `quantity`, `price`, `value = quantity * price`, and change%.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-1 Fan Dashboard`).

**Partial**
- `wallet_balance_growth_timeseries` - non-canonical
  - Calculation: portfolio value over selected windows (`24h`, `1w`, `1m`, etc.).
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-1 Fan Dashboard`).
- `referral_summary_metrics` - non-canonical
  - Calculation: referred signups and rewards earned per user.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-1 Fan Dashboard`).

**Blocked**
- `watchlist_interaction_metrics` - non-canonical
  - Calculation: watchlist adds/removes and trend over time.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-1 Fan Dashboard`).
- `suggested_tokens_effectiveness` - non-canonical
  - Calculation: recommendation CTR and purchase uplift.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-1 Fan Dashboard`).

### Issuer-Specific Purchase Page
**Active**
- `current_token_price` - non-canonical
  - Calculation: latest token price from `tokens.current_price` or latest trade `ending_price`.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-2`), `docs/database_schema_taxonomy.md`.
- `token_price_history` - non-canonical
  - Calculation: time-series of token trade prices by timestamp.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-2`).
- `total_tokens_sold` - non-canonical
  - Calculation: `SUM(transactions.quantity)` per token.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-2`), `docs/database_schema_taxonomy.md`.
- `total_raised_usd` - non-canonical
  - Calculation: `SUM(transactions.total_amount_usdc)` per token/issuer.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-2`), `docs/database_schema_taxonomy.md`.
- `supply_remaining` - non-canonical
  - Calculation: `initial_supply - total_sold`.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-2`), `docs/database_schema_taxonomy.md`.
- `purchase_history_user_level` - non-canonical
  - Calculation: transaction list with timestamp, price, quantity, total value per user.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-2`).

**Partial**
- `daily_price_change_pct` - non-canonical
  - Calculation: `(price_now - price_24h_ago)/price_24h_ago`.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-2`).

### Issuer Dashboard
**Active**
- `amount_raised_vs_target` - canonical tier_1
  - Calculation: `SUM(total_amount_usdc) / raise_target_usd` by issuer.
  - Source: `app/rag/catalog/kpi_catalog.json`, `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-3`).
- `issuer_daily_revenue` - canonical tier_1
  - Calculation: daily `SUM(total_amount_usdc)` by issuer/date.
  - Source: `app/rag/catalog/kpi_catalog.json`, `docs/database_schema_taxonomy.md`, `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-3`).
- `holder_concentration_top10_share` - non-canonical
  - Calculation: `(sum quantity of top 10 holders)/(total quantity held)` per token.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-3`).

**Partial**
- `revenue_source_breakdown` - non-canonical
  - Calculation: split revenue by primary sales, secondary fees, referrals.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-3`).
- `referral_click_to_signup_to_purchase_funnel` - non-canonical
  - Calculation: multi-step referral conversion chain.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-3`).

**Blocked**
- `perks_delivered_rate` - non-canonical
  - Calculation: `delivered_perks / eligible_perks`.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-3`).
- `community_engagement_metrics` - non-canonical
  - Calculation: page views, watchlist adds/removes, shares/mentions trends.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-3`).
- `top_referrers` - non-canonical
  - Calculation: rank referrers by downstream signups/purchases.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-3`).

### ATHLScan Public Token Explorer
**Active**
- `live_trade_feed_core_metrics` - non-canonical
  - Calculation: show each transaction with timestamp, quantity/value, execution price, buyer/seller.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-4`).
- `token_overview_current_price_volume_holders_launch_date` - non-canonical
  - Calculation: combine `current_price`, daily volume, holders count, launch date.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-4`).
- `token_leaderboard_most_traded` - canonical tier_1
  - Calculation: rank by trade volume or transaction count in selected window.
  - Source: `app/rag/catalog/kpi_catalog.json`, `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-4`), `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf`.
- `token_leaderboard_top_gainers` - non-canonical
  - Calculation: rank by highest `% price increase` over selected period.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-4`).
- `token_leaderboard_most_holders` - non-canonical
  - Calculation: rank by `COUNT(DISTINCT holder)` per token.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-4`).

**Partial**
- `token_price_change_24h_pct` - non-canonical
  - Calculation: `(price_now - price_24h_ago)/price_24h_ago`.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-4`).

**Blocked**
- `watchlist_popularity` - non-canonical
  - Calculation: rank by watchlist add counts.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-4`).
- `trade_reversal_rate` - non-canonical
  - Calculation: reversed transactions / all transactions.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-4`).
- `suspicious_trade_flag_rate` - non-canonical
  - Calculation: flagged suspicious trades / all trades.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf` (`3-4`).

## Leaderboard Document

### Generic Leaderboard
**Partial**
- `token_demand_subscore` - non-canonical
  - Calculation: weighted mint volume, buy/sell volume, and price movement.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`2 Ranking Logic`).
- `earnings_based_leaderboard` - non-canonical
  - Calculation: rank by revenue/earnings/reward payouts where available.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`2 Earnings-Based`).

**Blocked**
- `overall_athlete_composite_score` - non-canonical
  - Calculation: weighted blend of token demand, engagement, participation, social growth.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`2`).
- `engagement_subscore` - non-canonical
  - Calculation: weighted likes/saves/comments/shares/video interactions.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`2 Ranking Logic`).
- `community_participation_subscore` - non-canonical
  - Calculation: AMA/challenge participation weighted score.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`2`).
- `social_growth_subscore` - non-canonical
  - Calculation: follower velocity and social growth over selected window.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`2`).
- `trending_score` - non-canonical
  - Calculation: short-window momentum score from 24h/48h spikes.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`2 Trending`).
- `fan_favorites_score` - non-canonical
  - Calculation: weighted votes/likes/cheers/boosts with reset period.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`2 Fan Favorites`).

### Ranking Logic and Scoring
**Partial**
- `token_performance_component` - non-canonical
  - Calculation: weighted minted tokens, trade volume, and price movement.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`Ranking Logic & Scoring`).

**Blocked**
- `profile_activity_component` - non-canonical
  - Calculation: weighted daily active fans, new followers, profile views.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`Ranking Logic & Scoring`).
- `consistency_component` - non-canonical
  - Calculation: weighted posting frequency and challenge participation.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`Ranking Logic & Scoring`).

### Success Metrics
**Partial**
- `mint_volume_uplift` - non-canonical
  - Calculation: delta in mint/trade volume before vs after leaderboard interactions.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`Success Metrics`).

**Blocked**
- `athlete_discovery_profile_views` - non-canonical
  - Calculation: change in profile views after leaderboard exposure.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`Success Metrics`).
- `fan_engagement_per_athlete` - non-canonical
  - Calculation: interactions per athlete per time window.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`Success Metrics`).
- `athlete_posting_frequency` - non-canonical
  - Calculation: posts per athlete per time window.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`Success Metrics`).
- `fan_and_athlete_retention` - non-canonical
  - Calculation: returning cohort percentage for fans/athletes by period.
  - Source: `ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf` (`Success Metrics`).

