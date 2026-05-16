# Canonical KPI List v1

## Selection Notes
- Any entry in `app/rag/catalog/kpi_catalog.json` is canonical.
- Canonical KPIs are tiered:
  - `tier_1`: business-critical KPIs preferred by planner/matcher.
  - `tier_2`: operational KPIs that are canonical, but lower-priority for broad matching.
- Schema-level metric dictionary coverage lives in `app/rag/catalog/schema_docs/v2_schema_docs.json`.
- Runtime processing uses JSON catalog only; this markdown file is documentation for humans.

## Tier 1 Canonical KPIs

### Active
- `issuer_type_distribution`
  - Definition: distribution of issuers by `issuer_type`.
  - Core tables: `issuers`
  - Dimensions: `issuer_type`, `country`, `level`
- `profile_completion_rate_by_issuer_type`
  - Definition: share of issuers with profile completion above threshold by type.
  - Core tables: `issuers`, `athlete_profile`, `creator_profile`
  - Dimensions: `issuer_type`, `sport`, `creator_category`
- `id_verification_opt_in_rate`
  - Definition: share of issuers who opted into identity verification.
  - Core tables: `identity_verification`, `issuers`
  - Dimensions: `issuer_type`, `provider`, `country`
- `id_verification_pass_rate`
  - Definition: passed identity checks / completed identity checks.
  - Core tables: `identity_verification`, `issuers`
  - Dimensions: `provider`, `level`, `issuer_type`
- `id_verification_completion_rate`
  - Definition: completed identity checks / initiated identity checks.
  - Core tables: `identity_verification`, `issuers`
  - Dimensions: `provider`, `issuer_type`
- `manual_review_rate`
  - Definition: checks in manual review / all identity checks.
  - Core tables: `identity_verification`, `issuers`
  - Dimensions: `provider`, `issuer_type`
- `social_verification_success_rate`
  - Definition: successful social verifications / total social verification attempts.
  - Core tables: `social_verification`, `issuers`
  - Dimensions: `platform`, `issuer_type`
- `social_verification_retry_rate`
  - Definition: average social verification attempts per flow.
  - Core tables: `social_verification`, `issuers`
  - Dimensions: `platform`, `issuer_type`
- `amount_raised_vs_target`
  - Definition: raised amount compared to issuer target raise.
  - Core tables: `transactions`, `tokens`, `issuer_preferences`, `issuers`
  - Dimensions: `issuer_type`, `sport`, `creator_category`
- `percent_supply_sold_30d`
  - Definition: quantity sold in first 30 days / initial supply.
  - Core tables: `tokens`, `transactions`
  - Dimensions: `token_id`, `issuer_type`, `token_symbol`
- `issuer_daily_revenue`
  - Definition: daily revenue totals per issuer.
  - Core tables: `issuer_daily_revenue`
  - Dimensions: `issuer_id`, `date`
- `token_leaderboard_most_traded`
  - Definition: token ranking by trade volume or trade count in selected window.
  - Core tables: `transactions`, `tokens`, `issuers`
  - Dimensions: `token_id`, `issuer_type`, `time_window`

### Blocked by missing data
- `login_attempt_volume`
  - Definition: total login attempts per day.
  - Core tables: `auth_login_events`
  - Dimensions: `platform`, `country`
  - Missing dependencies: `auth_login_events table`
- `session_timeout_rate`
  - Definition: sessions ending by timeout / all ended sessions.
  - Core tables: `auth_session_events`
  - Dimensions: `platform`
  - Missing dependencies: `auth_session_events table`
- `mfa_success_rate`
  - Definition: successful MFA challenges / all MFA challenges.
  - Core tables: `mfa_challenge_events`
  - Dimensions: `challenge_type`
  - Missing dependencies: `mfa_challenge_events table`
- `anomaly_detection_rate`
  - Definition: flagged anomaly events / all monitored events.
  - Core tables: `risk_anomaly_events`
  - Dimensions: `anomaly_type`, `platform`
  - Missing dependencies: `risk_anomaly_events table`
- `support_contact_rate`
  - Definition: users contacting support / active users in period.
  - Core tables: `support_contacts`, `users`
  - Dimensions: `contact_reason`, `user_role`
  - Missing dependencies: `support_contacts table`
- `referral_link_click_conversion`
  - Definition: referral clicks that convert to signup or purchase / all referral clicks.
  - Core tables: `referral_click_events`, `users`, `transactions`
  - Dimensions: `channel`, `referrer_type`
  - Missing dependencies: `referral_click_events table`, `referral attribution model`

## Tier 2 Canonical KPIs

### Active
- `total_platform_revenue`
  - Definition: total completed transaction revenue across platform.
  - Core tables: `transactions`
  - Dimensions: `time_grain`
- `active_trading_users`
  - Definition: distinct buyers with at least one transaction in period.
  - Core tables: `transactions`
  - Dimensions: `time_grain`
- `participation_rate`
  - Definition: distinct trading users / distinct users.
  - Core tables: `transactions`, `users`
  - Dimensions: `time_grain`
- `average_transaction_size_usdc`
  - Definition: average transaction notional in USDC.
  - Core tables: `transactions`
  - Dimensions: `time_grain`
- `average_tokens_per_transaction`
  - Definition: average quantity purchased per transaction.
  - Core tables: `transactions`
  - Dimensions: `time_grain`
- `tokens_issued_count`
  - Definition: count of tokens issued per issuer.
  - Core tables: `tokens`
  - Dimensions: `issuer_id`
- `total_supply_issued`
  - Definition: sum of `initial_supply` per issuer.
  - Core tables: `tokens`
  - Dimensions: `issuer_id`, `token_symbol`
- `token_number_of_buyers`
  - Definition: distinct buyers per token.
  - Core tables: `transactions`, `tokens`
  - Dimensions: `token_id`, `token_symbol`
- `average_selling_price`
  - Definition: `SUM(total_amount_usdc) / SUM(quantity)` by token.
  - Core tables: `transactions`, `tokens`
  - Dimensions: `token_id`, `issuer_id`
- `total_purchases_by_user`
  - Definition: total purchase value by buyer.
  - Core tables: `transactions`
  - Dimensions: `buyer_id`

## Deprecated / Removed from Runtime Catalog

- ~~`waitlist_approval_rate`~~
- ~~`issuer_activation_rate`~~
- Reason: waitlist dataset/table is no longer present in active database.
- Policy: removed from `kpi_catalog.json` so matcher cannot route to unavailable data.

## Source Anchors
- KPI names and intent: `- for me/ATHL KPI Framework - KPI.csv`.
- Dashboard priorities: `- for me/ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf`.
- Leaderboard priorities: `- for me/ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf`.
