# KPI Inventory — Grouped by Section

> Auto-generated from `app/rag/catalog/kpi_catalog.json` (version 2.0.0).  
> Do not hand-edit — run `python app/rag/catalog/generate_kpi_docs.py` to regenerate.

**62 KPIs total** (62 active, 0 blocked)

---

## A. Marketplace Health & Liquidity

_17 KPIs — 17 active, 0 blocked_

### `total_token_revenue`
**Total Token Revenue**  ✓ active

Total USDC value of completed transactions, platform-wide. Group by token_id for per-token revenue. This is the same number sometimes called GTV; it is revenue, not a trade count or quantity.

- **value_basis:** `token_revenue_gross`
- **tables:** `transactions`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** time_grain, token_id, issuer_id
- **recipe pattern:** `sum_grouped`
- **example:** 'What is total token revenue this month?'

### `total_transactions`
**Total Transactions**  ✓ active

Count of completed transactions platform-wide.

- **tables:** `transactions`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** time_grain, token_id
- **recipe pattern:** `count_grouped`
- **example:** 'How many transactions were completed this month?'

### `average_transaction_size_usdc`
**Average Transaction Size (USDC)**  ✓ active

Average USDC value per completed transaction.

- **tables:** `transactions`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** time_grain, token_id
- **recipe pattern:** `average`
- **example:** 'What is the average transaction size in USDC?'

### `average_token_price`
**Average Token Price**  ✓ active

Average current_price across all tokens. current_price is a bonding-curve function of total_sold, not an independent market price.

- **tables:** `tokens`
- **dimensions:** issuer_type
- **recipe pattern:** `average`
- **example:** 'What is the average token price across the platform?'

### `token_price_growth_rate`
**Token Price Growth Rate**  ✓ active

Price change per token over a window, derived from ending_price ordered by timestamp. Powers top-gainers view. No price-history table — reconstruct from transactions.

- **tables:** `transactions`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** token_id
- **recipe pattern:** `raw_sql`
- **example:** 'Which tokens have gained the most in price this week?'

### `active_tradable_tokens`
**Active Tradable Tokens**  ✓ active

Tokens with paused_sales = false and at least one completed transaction.

- **tables:** `tokens`, `transactions`
- **joins:** `tokens.token_id = transactions.token_id`
- **default filters:** `tokens.paused_sales = false`, `lower(transactions.status) = 'completed'`
- **dimensions:** time_grain
- **recipe pattern:** `count_grouped`
- **example:** 'How many tokens are actively tradable?'

### `tokens_with_no_trading_activity`
**Tokens With No Trading Activity**  ✓ active

Tokens with zero completed transactions.

- **tables:** `tokens`, `transactions`
- **dimensions:** issuer_type
- **recipe pattern:** `raw_sql`
- **example:** 'How many tokens have never been traded?'

### `total_market_capitalization`
**Total Market Capitalization**  ✓ active

SUM(current_price x total_sold) across all tokens. Circulating supply = total_sold (never current_supply_minted which is always 0).

- **tables:** `tokens`
- **dimensions:** issuer_type
- **recipe pattern:** `sum_grouped`
- **example:** 'What is the total market cap of all tokens?'

### `token_liquidity_velocity`
**Token Liquidity Velocity**  ✓ active

Traded quantity divided by total_sold per token. Measures turnover rate.

- **tables:** `transactions`, `tokens`
- **joins:** `transactions.token_id = tokens.token_id`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** token_id
- **recipe pattern:** `ratio`
- **example:** 'What is the trading velocity for each token?'

### `token_holders_count`
**Token Holders Count**  ✓ active

Distinct holders per token (users with quantity > 0). Powers ATHLScan holders view and most-holders leaderboard.

- **tables:** `user_token_wallet`
- **default filters:** `user_token_wallet.quantity > 0`
- **dimensions:** token_id
- **recipe pattern:** `count_grouped`
- **example:** 'How many holders does each token have?'

### `token_holder_distribution`
**Token Holder Distribution**  ✓ active

Distribution of holdings within a token across holders.

- **tables:** `user_token_wallet`
- **default filters:** `user_token_wallet.quantity > 0`
- **dimensions:** token_id
- **recipe pattern:** `sum_grouped`
- **example:** 'How are token holdings distributed among holders?'

### `wallet_concentration_ratio`
**Wallet Concentration Ratio**  ✓ active

Share of holdings held by top wallets per token — whale concentration detection.

- **tables:** `user_token_wallet`
- **default filters:** `user_token_wallet.quantity > 0`
- **dimensions:** token_id
- **recipe pattern:** `raw_sql`
- **example:** 'What is the wallet concentration for each token?'

### `top_tokens_share_of_volume`
**Top Tokens Share of Volume**  ✓ active

Share of total transaction volume held by the top-N tokens. Volume concentration risk metric.

- **tables:** `transactions`, `tokens`
- **joins:** `transactions.token_id = tokens.token_id`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** token_id
- **recipe pattern:** `raw_sql`
- **example:** 'What share of volume do the top 10 tokens account for?'

### `token_leaderboard_most_traded`
**Top Tokens by Volume**  ✓ active

Token ranking by traded volume or transaction count in a time window. Leaderboard guardrail: only matches ranking-style questions.

- **tables:** `transactions`, `tokens`
- **joins:** `transactions.token_id = tokens.token_id`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** token_id, issuer_type, time_window
- **recipe pattern:** `raw_sql`
- **example:** 'What are the top 10 tokens by trading volume this week?'

### `buy_vs_sell_ratio`
**Buy vs Sell Ratio**  ✓ active

Ratio of buy-side to sell-side transaction activity. Degenerate on current data — all transactions are primary sales.

- **tables:** `transactions`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** time_grain
- **recipe pattern:** `ratio`
- **example:** 'What is the buy to sell ratio?'

### `secondary_market_share`
**Secondary Market Share**  ✓ active

Share of volume from secondary (peer-to-peer) trading. Currently 0% — no secondary trading exists.

- **tables:** `transactions`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** time_grain
- **recipe pattern:** `ratio`
- **example:** 'What percentage of volume is from secondary trading?'

### `failed_reversed_transactions`
**Failed or Reversed Transactions**  ✓ active

Count of failed or reversed transactions. Currently 0 — none generated in current data.

- **tables:** `transactions`
- **dimensions:** time_grain
- **recipe pattern:** `count_grouped`
- **example:** 'How many transactions failed or were reversed?'

## B. User Growth & Engagement

_12 KPIs — 12 active, 0 blocked_

### `net_new_users`
**Net New Users**  ✓ active

New registered users by time grain, using users.created_at.

- **tables:** `users`
- **dimensions:** time_grain, country
- **recipe pattern:** `count_grouped`
- **example:** 'How many new users signed up this week?'

### `total_registered_users`
**Total Registered Users**  ✓ active

Total count of all registered users.

- **tables:** `users`
- **dimensions:** country, user_role
- **recipe pattern:** `count_grouped`
- **example:** 'How many total registered users do we have?'

### `user_growth_rate`
**User Growth Rate**  ✓ active

Period-over-period growth in registered users.

- **tables:** `users`
- **dimensions:** time_grain
- **recipe pattern:** `raw_sql`
- **example:** 'What is the month over month user growth rate?'

### `active_traders`
**Active Traders**  ✓ active

Distinct users who completed a transaction in the period (buyer_id only). MAT = month grain. seller_id excluded — equals issuer user_id on all primary sales.

- **tables:** `transactions`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** time_grain
- **recipe pattern:** `count_grouped`
- **example:** 'How many active traders did we have this month?'

### `active_sellers`
**Active Sellers**  ✓ active

Distinct sellers in the period. In current data, sellers = issuers (all transactions are primary sales).

- **tables:** `transactions`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** time_grain
- **recipe pattern:** `count_grouped`
- **example:** 'How many active sellers are there?'

### `buyer_to_seller_ratio`
**Buyer to Seller Ratio**  ✓ active

Ratio of distinct active buyers to distinct active sellers in a period.

- **tables:** `transactions`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** time_grain
- **recipe pattern:** `ratio`
- **example:** 'What is the ratio of buyers to sellers?'

### `repeat_buyer_rate`
**Repeat Buyer Rate**  ✓ active

Share of buyers who made more than one completed transaction.

- **tables:** `transactions`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** time_grain
- **recipe pattern:** `raw_sql`
- **example:** 'What percentage of buyers made more than one purchase?'

### `multi_token_ownership_rate`
**Multi-Token Ownership Rate**  ✓ active

Share of token holders who hold more than one distinct token.

- **tables:** `user_token_wallet`
- **default filters:** `user_token_wallet.quantity > 0`
- **recipe pattern:** `raw_sql`
- **example:** 'What share of users hold more than one token?'

### `average_wallet_balance`
**Average Wallet Balance**  ✓ active

Average USDC wallet balance per user. usdc_balance is cost-basis, not mark-to-market.

- **tables:** `user_wallet`
- **dimensions:** user_role
- **recipe pattern:** `average`
- **example:** 'What is the average wallet balance?'

### `funded_wallet_rate`
**Funded Wallet Rate**  ✓ active

Share of wallets with a positive USDC balance.

- **tables:** `user_wallet`
- **recipe pattern:** `ratio`
- **example:** 'What share of wallets have a positive balance?'

### `mfa_adoption_rate`
**MFA Adoption Rate**  ✓ active

Share of users with MFA enabled. Currently 0% — mfa_enabled = false for all rows in current data.

- **tables:** `users`
- **dimensions:** user_role
- **recipe pattern:** `ratio`
- **example:** 'What is the MFA adoption rate?'

### `verified_email_rate`
**Verified Email Rate**  ✓ active

Share of users with a verified email address.

- **tables:** `users`
- **dimensions:** user_role, country
- **recipe pattern:** `ratio`
- **example:** 'What percentage of users have verified their email?'

## C. Issuer Ecosystem Health

_22 KPIs — 22 active, 0 blocked_

### `total_issuers`
**Total Issuers**  ✓ active

Count of all issuers on the platform.

- **tables:** `issuers`
- **dimensions:** issuer_type, level, country
- **recipe pattern:** `count_grouped`
- **example:** 'How many total issuers are on the platform?'

### `verified_issuers`
**Verified Issuers**  ✓ active

Count of issuers with status = 'PASSED' (fully verified).

- **tables:** `issuers`
- **default filters:** `issuers.status = 'PASSED'`
- **dimensions:** issuer_type
- **recipe pattern:** `count_grouped`
- **example:** 'How many issuers are fully verified?'

### `verification_pass_rate`
**Verification Pass Rate**  ✓ active

Fully-verified issuers (status='PASSED') divided by all issuers. The single executive-level verification KPI.

- **tables:** `issuers`
- **dimensions:** issuer_type
- **recipe pattern:** `ratio`
- **example:** 'What is the issuer verification pass rate?'

### `id_verification_pass_rate`
**ID Verification Pass Rate**  ✓ active

Share of completed identity checks that passed.

- **tables:** `identity_verification`, `issuers`
- **joins:** `identity_verification.issuer_id = issuers.issuer_id`
- **default filters:** `identity_verification.completed_at IS NOT NULL`
- **dimensions:** provider, level, issuer_type
- **recipe pattern:** `ratio`
- **example:** 'What is the ID verification pass rate by provider?'

### `id_verification_opt_in_rate`
**ID Verification Opt-In Rate**  ✓ active

Share of issuers who opted into identity verification.

- **tables:** `identity_verification`, `issuers`
- **joins:** `identity_verification.issuer_id = issuers.issuer_id`
- **dimensions:** issuer_type, provider, country
- **recipe pattern:** `ratio`
- **example:** 'What is the ID verification opt-in rate?'

### `id_verification_completion_rate`
**ID Verification Completion Rate**  ✓ active

Share of initiated identity checks that reached completion.

- **tables:** `identity_verification`, `issuers`
- **joins:** `identity_verification.issuer_id = issuers.issuer_id`
- **default filters:** `identity_verification.initiated_at IS NOT NULL`
- **dimensions:** provider, issuer_type
- **recipe pattern:** `ratio`
- **example:** 'What is the identity verification completion rate?'

### `manual_review_rate`
**Manual Review Rate**  ✓ active

Share of identity verification checks that required manual review.

- **tables:** `identity_verification`, `issuers`
- **joins:** `identity_verification.issuer_id = issuers.issuer_id`
- **dimensions:** provider, issuer_type
- **recipe pattern:** `ratio`
- **example:** 'What percent of ID checks go to manual review?'

### `social_verification_pass_rate`
**Social Verification Pass Rate**  ✓ active

Successful social verifications divided by total social verification attempts.

- **tables:** `social_verification`, `issuers`
- **joins:** `social_verification.issuer_id = issuers.issuer_id`
- **dimensions:** platform, issuer_type
- **recipe pattern:** `ratio`
- **example:** 'What is the social verification pass rate?'

### `social_verification_retry_rate`
**Social Verification Retry Rate**  ✓ active

Average number of attempts per social verification flow.

- **tables:** `social_verification`, `issuers`
- **joins:** `social_verification.issuer_id = issuers.issuer_id`
- **default filters:** `social_verification.attempts IS NOT NULL`
- **dimensions:** platform, issuer_type
- **recipe pattern:** `average`
- **example:** 'How many retries do issuers need for social verification?'

### `issuer_activation_rate`
**Issuer Activation Rate**  ✓ active

Issuers with a live token and at least one completed sale divided by all issuers. Old waitlist definition is retired.

- **tables:** `issuers`, `tokens`, `transactions`
- **joins:** `tokens.issuer_id = issuers.issuer_id`, `transactions.token_id = tokens.token_id`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** issuer_type
- **recipe pattern:** `raw_sql`
- **example:** 'What share of issuers have made at least one sale?'

### `token_launch_success_rate`
**Token Launch Success Rate**  ✓ active

Issuers with a live token (paused_sales = false) divided by issuers who created any token record.

- **tables:** `issuers`, `tokens`
- **joins:** `tokens.issuer_id = issuers.issuer_id`
- **dimensions:** issuer_type
- **recipe pattern:** `raw_sql`
- **example:** 'What is the token launch success rate?'

### `issuer_revenue`
**Issuer Revenue**  ✓ active

Revenue per issuer, net of the platform take (~80% of gross). Source: issuer_daily_revenue.total_amount_usdc. FK issuer_daily_revenue.issuer_id -> issuers.issuer_id is clean.

- **value_basis:** `issuer_net`
- **tables:** `issuer_daily_revenue`
- **dimensions:** issuer_id, date
- **recipe pattern:** `sum_grouped`
- **example:** 'How much did each issuer earn?'

### `average_revenue_per_issuer`
**Average Revenue Per Issuer**  ✓ active

Mean issuer net revenue across all issuers.

- **value_basis:** `issuer_net`
- **tables:** `issuer_daily_revenue`
- **dimensions:** issuer_type
- **recipe pattern:** `raw_sql`
- **example:** 'What is the average revenue per issuer?'

### `top_issuer_revenue_share`
**Top Issuer Revenue Share**  ✓ active

Share of total issuer net revenue held by the top-N issuers.

- **value_basis:** `issuer_net`
- **tables:** `issuer_daily_revenue`
- **dimensions:** issuer_type
- **recipe pattern:** `raw_sql`
- **example:** 'What share of revenue do the top 10 issuers generate?'

### `issuer_revenue_growth`
**Issuer Revenue Growth**  ✓ active

Period-over-period growth in issuer net revenue.

- **value_basis:** `issuer_net`
- **tables:** `issuer_daily_revenue`
- **dimensions:** issuer_id
- **recipe pattern:** `raw_sql`
- **example:** 'What is the month over month issuer revenue growth?'

### `issuers_with_zero_revenue`
**Zero Revenue Issuers**  ✓ active

Count and share of issuers with no revenue in issuer_daily_revenue.

- **value_basis:** `issuer_net`
- **tables:** `issuers`, `issuer_daily_revenue`
- **dimensions:** issuer_type
- **recipe pattern:** `raw_sql`
- **example:** 'How many issuers have made zero revenue?'

### `athlete_vs_creator_split`
**Athlete vs Creator Split**  ✓ active

Distribution of issuers by issuer_type (athlete vs creator).

- **tables:** `issuers`
- **dimensions:** issuer_type, level
- **recipe pattern:** `count_grouped`
- **example:** 'What is the split between athletes and creators?'

### `social_reach_verified_issuers`
**Social Reach of Verified Issuers**  ✓ active

Aggregate follower count across verified social accounts of issuers.

- **tables:** `social_verification`, `issuers`
- **joins:** `social_verification.issuer_id = issuers.issuer_id`
- **default filters:** `social_verification.status = 'SUCCESS'`
- **dimensions:** platform, issuer_type
- **recipe pattern:** `sum_grouped`
- **example:** 'What is the total social reach of verified issuers?'

### `profile_completion_rate_by_issuer_type`
**Profile Completion Rate by Issuer Type**  ✓ active

Share of issuers with profile_completion >= 80%, split by issuer_type. Athlete-only in current data — creator_profile is unpopulated.

- **tables:** `issuers`, `athlete_profile`
- **joins:** `issuers.issuer_id = athlete_profile.issuer_id`
- **dimensions:** issuer_type, sport
- **recipe pattern:** `ratio`
- **example:** 'What is the profile completion rate for athletes vs creators?'

### `issuer_onboarding_completion_rate`
**Issuer Onboarding Completion Rate**  ✓ active

Share of issuers who completed onboarding tracked in issuer_post_signup.

- **tables:** `issuer_post_signup`, `issuers`
- **joins:** `issuer_post_signup.issuer_id = issuers.issuer_id`
- **dimensions:** issuer_type
- **recipe pattern:** `ratio`
- **example:** 'What is the issuer onboarding completion rate?'

### `wallet_provisioning_success_rate`
**Wallet Provisioning Success Rate**  ✓ active

Share of issuers with a successfully provisioned wallet.

- **tables:** `issuer_post_signup`
- **dimensions:** issuer_type
- **recipe pattern:** `ratio`
- **example:** 'What is the wallet provisioning success rate?'

### `oauth_verification_completion_rate`
**OAuth Verification Completion Rate**  ✓ active

Share of issuers who verified at least 2 social platforms (oauth_verified_min2 = true).

- **tables:** `issuer_post_signup`
- **dimensions:** issuer_type
- **recipe pattern:** `ratio`
- **example:** 'What is the OAuth verification completion rate?'

## D. Financial & Business

_7 KPIs — 7 active, 0 blocked_

### `amount_raised_vs_target`
**Amount Raised vs Target**  ✓ active

Total raised (gross completed transactions) vs issuer raise target from issuer_preferences. raise_target_usd is randomly generated in dummy data.

- **value_basis:** `token_revenue_gross`
- **tables:** `transactions`, `tokens`, `issuer_preferences`
- **joins:** `transactions.token_id = tokens.token_id`, `tokens.issuer_id = issuer_preferences.issuer_id`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** issuer_type
- **recipe pattern:** `ratio`
- **example:** 'How much has each issuer raised versus their target?'

### `percent_supply_sold_30d`
**Percent Supply Sold (30d)**  ✓ active

Tokens sold in first 30 days after mint divided by initial_supply.

- **tables:** `tokens`, `transactions`
- **joins:** `transactions.token_id = tokens.token_id`
- **default filters:** `lower(transactions.status) = 'completed'`, `transactions.timestamp <= tokens.mint_timestamp + INTERVAL '30 days'`
- **dimensions:** token_id, issuer_type
- **recipe pattern:** `ratio`
- **example:** 'What percent of supply was sold in the first 30 days?'

### `supply_remaining`
**Supply Remaining**  ✓ active

initial_supply minus total_sold per token. Never use current_supply_minted — always 0 in current data.

- **tables:** `tokens`
- **dimensions:** token_id, issuer_id
- **recipe pattern:** `raw_sql`
- **example:** 'How much supply remains for each token?'

### `average_revenue_per_token`
**Average Revenue Per Token**  ✓ active

Mean gross revenue per token using tokens.total_revenue.

- **value_basis:** `token_revenue_gross`
- **tables:** `tokens`
- **dimensions:** issuer_id
- **recipe pattern:** `average`
- **example:** 'What is the average revenue per token?'

### `revenue_growth_rate`
**Revenue Growth Rate**  ✓ active

Period-over-period growth in total gross token revenue.

- **value_basis:** `token_revenue_gross`
- **tables:** `transactions`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** time_grain
- **recipe pattern:** `raw_sql`
- **example:** 'What is revenue growth rate month over month?'

### `revenue_concentration`
**Revenue Concentration**  ✓ active

Share of platform issuer net revenue from the top-N issuers. Concentration risk metric.

- **value_basis:** `issuer_net`
- **tables:** `issuer_daily_revenue`, `issuers`
- **joins:** `issuer_daily_revenue.issuer_id = issuers.issuer_id`
- **dimensions:** issuer_type
- **recipe pattern:** `raw_sql`
- **example:** 'What is revenue concentration among top issuers?'

### `platform_fee_revenue`
**Platform Fee Revenue (synthetic)**  ✓ active

Platform take = gross token revenue minus issuer net revenue (~0.2 x gross). SYNTHETIC until a real fee ledger exists.

- **value_basis:** `platform_fee`
- **tables:** `transactions`, `issuer_daily_revenue`
- **default filters:** `lower(transactions.status) = 'completed'`
- **dimensions:** time_grain
- **recipe pattern:** `raw_sql`
- **example:** 'What is the platform fee revenue?'

## E. Compliance, Trust & Risk

_4 KPIs — 4 active, 0 blocked_

### `suspended_accounts`
**Suspended Accounts**  ✓ active

Count of suspended or restricted user accounts. Currently 0 — all accounts are ACTIVE in current data.

- **tables:** `users`
- **dimensions:** user_role, country
- **recipe pattern:** `count_grouped`
- **example:** 'How many accounts are suspended?'

### `failed_identity_checks`
**Failed Identity Checks**  ✓ active

Count of failed identity verification checks. Fraud and risk signal.

- **tables:** `identity_verification`, `issuers`
- **joins:** `identity_verification.issuer_id = issuers.issuer_id`
- **dimensions:** provider, issuer_type
- **recipe pattern:** `count_grouped`
- **example:** 'How many identity checks failed?'

### `high_risk_wallet_concentration`
**High Risk Wallet Concentration**  ✓ active

Tokens where the top wallet holds more than 50% of circulating supply — concentration risk heuristic.

- **tables:** `user_token_wallet`
- **default filters:** `user_token_wallet.quantity > 0`
- **dimensions:** token_id
- **recipe pattern:** `raw_sql`
- **example:** 'Which tokens have high wallet concentration risk?'

### `country_distribution`
**Country Distribution**  ✓ active

Geographic distribution of users and issuers by country. Compliance view.

- **tables:** `users`, `issuers`
- **dimensions:** country, user_role, issuer_type
- **recipe pattern:** `raw_sql`
- **example:** 'What is the country distribution across users and issuers?'
