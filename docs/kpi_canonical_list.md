# Canonical KPI List

## Selection Notes
- **Canonical set = the full north star *active* KPI set** (`athl_north_star_executive_dashboard_kpis.md`). Every entry here gets a row in `app/rag/catalog/kpi_catalog.json`.
- **No tiers.** The catalog is flat. Matcher priority among look-alike metrics is handled by deliberate aliases/examples and per-cluster default-resolution (Claude Code), not by a tier field.
- **Precedence.** This file is authoritative for KPI selection, definitions, and sizing. It **supersedes the sizing and tiering** in the archived `docs/archive/implementation_scope.md` (whose architecture rationale remains historically accurate but predates the north star). The JSON catalog is generated from / linted against this file.
- **`status`** is the only status distinction: `active` here; blocked KPIs are tracked separately and omitted from this list for now.
- **`value_basis`** is required on every revenue KPI to prevent gross/net confusion (see Revenue Family below).
- Validated against `athl_raw_tables_postgres.sql` (schema) and `generate_and_load_data_neon.ipynb` (data semantics).
- Runtime uses the JSON catalog only; this file is the human-mappable source of truth that the JSON is generated from / linted against.
- Format per block mirrors the JSON: `kpi_id`, Definition, Core tables, Dimensions, (Value basis), (Notes).

---

## How to read this

The KPI layer is an **optional accelerator** over deterministic schema grounding: canonical KPIs give the executive view *one* blessed definition and keep the agent's answers consistent with the dashboard. The five sections below map to the north star's five executive questions:

| Section | Executive question |
|---|---|
| A. Marketplace Health & Liquidity | Is liquidity and trading activity healthy? |
| B. User Growth & Engagement | Is the platform growing? |
| C. Issuer Ecosystem Health | Are issuers succeeding? |
| D. Financial & Business | Is the ecosystem financially sustainable? |
| E. Compliance, Trust & Risk | Are trust, compliance, and activation improving? |

Disambiguation among look-alike metrics is deterministic (deliberate aliases + per-cluster defaults), so a single-turn question resolves without a clarifying question.

---

## Revenue Family (read before the entries)

All platform revenue derives from one base: **`SUM(transactions.total_amount_usdc)` where `lower(status) = 'completed'`.** The same sum at different groupings / splits:

- **Token revenue** = that sum, grouped by token. Equals `tokens.total_revenue` by construction (eval should assert equality).
- **Total token revenue** = that sum, platform-wide (no token grouping). *(This is the number sometimes called "GTV".)*
- **Issuer revenue** = `0.8 ×` that sum, grouped by issuer (synthetic 80/20 split until a real ledger/secondary market exists).
- **Platform revenue** = `0.2 ×` that sum (synthetic; flagged).

`value_basis` values: `token_revenue_gross` (token-level and platform-wide), `issuer_net`, `platform_fee`.

**Disambiguation (for alias authoring):**
- bare **"revenue"** (no qualifier) → `total_token_revenue` (platform-wide). *Cluster default.*
- **"token revenue" / "sales of token X" / "revenue for token X"** → `total_token_revenue` grouped by `token_id`.
- **"issuer revenue / earnings / per-issuer / creator revenue"** → `issuer_revenue`.
- **"platform revenue / platform fees / what the platform makes / take rate"** → `platform_fee_revenue`.
- the word **"volume"** is **not** claimed by the revenue cluster (reserved for any future quantity/count metric) so it cannot pull "revenue" intent.

---

## A. Marketplace Health & Liquidity

- `total_token_revenue`
  - Definition: total USDC value of completed transactions, platform-wide; group by `token_id` for per-token revenue.
  - Core tables: `transactions`
  - Dimensions: `time_grain`, `token_id`, `issuer_id`
  - Value basis: `token_revenue_gross`
  - Notes: filter `lower(status)='completed'`. Equals `SUM(tokens.total_revenue)`. Covers GTV and daily/monthly transaction volume (by grain). Do not alias to "volume".
- `total_transactions`
  - Definition: count of completed transactions.
  - Core tables: `transactions`
  - Dimensions: `time_grain`, `token_id`
- `average_transaction_size_usdc`
  - Definition: average completed transaction notional in USDC.
  - Core tables: `transactions`
  - Dimensions: `time_grain`, `token_id`
- `average_token_price`
  - Definition: average token price across the ecosystem.
  - Core tables: `tokens`
  - Dimensions: `issuer_type`
  - Notes: `current_price` is a bonding-curve function of `total_sold`, not an independent market price.
- `token_price_growth_rate`
  - Definition: price change per token over a window (powers "top gainers").
  - Core tables: `transactions`
  - Dimensions: `token_id`, `time_window`
  - Notes: no price-history table — reconstruct from `ending_price` ordered by `timestamp` per token (window logic).
- `active_tradable_tokens`
  - Definition: tokens with `paused_sales = false` and at least one completed transaction.
  - Core tables: `tokens`, `transactions`
  - Dimensions: `time_grain`
- `tokens_with_no_trading_activity`
  - Definition: tokens with zero completed transactions.
  - Core tables: `tokens`, `transactions`
  - Dimensions: `issuer_type`
- `total_market_capitalization`
  - Definition: `SUM(current_price × total_sold)` across tokens.
  - Core tables: `tokens`
  - Dimensions: `issuer_type`
  - Notes: circulating supply = `total_sold`; never `current_supply_minted` (always 0 in data).
- `token_liquidity_velocity`
  - Definition: turnover = traded quantity ÷ supply sold (per token or aggregate).
  - Core tables: `transactions`, `tokens`
  - Dimensions: `token_id`, `time_window`
  - Notes: join on `token_id`. Covers "trading velocity per token".
- `token_holders_count`
  - Definition: distinct holders per token (powers ATHLScan "holders" and leaderboard "most holders").
  - Core tables: `user_token_wallet`
  - Dimensions: `token_id`
  - Notes: `COUNT(DISTINCT user_id) WHERE quantity > 0`.
- `token_holder_distribution`
  - Definition: distribution/concentration of holdings within a token.
  - Core tables: `user_token_wallet`
  - Dimensions: `token_id`
- `wallet_concentration_ratio`
  - Definition: share of holdings held by top wallets (whale detection).
  - Core tables: `user_token_wallet`
  - Dimensions: `token_id`
- `top_tokens_share_of_volume`
  - Definition: share of total volume held by the top-N tokens (concentration risk).
  - Core tables: `transactions`, `tokens`
  - Dimensions: `time_window`
- `token_leaderboard_most_traded`
  - Definition: token ranking by traded volume/count in a window.
  - Core tables: `transactions`, `tokens`, `issuers`
  - Dimensions: `token_id`, `issuer_type`, `time_window`
  - Notes: leaderboard guardrail — only match ranking-style questions. Name "Top Tokens by Volume".
- `buy_vs_sell_ratio`
  - Definition: ratio of buy-side to sell-side activity.
  - Core tables: `transactions`
  - Dimensions: `time_grain`
  - Notes: degenerate on current data (all transactions are primary).
- `secondary_market_share`
  - Definition: share of volume from secondary trading.
  - Core tables: `transactions`
  - Dimensions: `time_grain`
  - Notes: 0% until secondary trading exists.
- `failed_reversed_transactions`
  - Definition: count/share of failed or reversed transactions.
  - Core tables: `transactions`
  - Dimensions: `time_grain`
  - Notes: 0 in current data (none generated).

---

## B. User Growth & Engagement

- `net_new_users`
  - Definition: new registered users by grain.
  - Core tables: `users`
  - Dimensions: `time_grain`, `country`
  - Notes: `users.created_at`. Covers "new users per day/week/month".
- `total_registered_users`
  - Definition: count of registered users.
  - Core tables: `users`
  - Dimensions: `country`, `user_role`
- `user_growth_rate`
  - Definition: period-over-period growth in registered users.
  - Core tables: `users`
  - Dimensions: `time_grain`
- `active_traders`
  - Definition: distinct users who transacted in the period (MAT = month grain).
  - Core tables: `transactions`
  - Dimensions: `time_grain`
  - Notes: distinct `buyer_id` only (seller-union deferred — `seller_id` is the issuer's user on every primary sale).
- `active_sellers`
  - Definition: distinct sellers in the period.
  - Core tables: `transactions`
  - Dimensions: `time_grain`
  - Notes: in current data sellers = issuers (primary sales), not peer sellers.
- `buyer_to_seller_ratio`
  - Definition: ratio of active buyers to active sellers.
  - Core tables: `transactions`
  - Dimensions: `time_grain`
  - Notes: confounded until secondary trading (sellers = issuers).
- `repeat_buyer_rate`
  - Definition: buyers with more than one completed transaction ÷ distinct buyers.
  - Core tables: `transactions`
  - Dimensions: `time_grain`
- `multi_token_ownership_rate`
  - Definition: share of holders owning more than one token.
  - Core tables: `user_token_wallet`
  - Dimensions: —
- `average_wallet_balance`
  - Definition: average USDC / total wallet value per user.
  - Core tables: `user_wallet`
  - Dimensions: `user_role`
  - Notes: `total_value`/`usdc_balance` are cost-basis, not mark-to-market.
- `funded_wallet_rate`
  - Definition: share of wallets with a positive balance.
  - Core tables: `user_wallet`
  - Dimensions: —
- `mfa_adoption_rate`
  - Definition: share of users with MFA enabled.
  - Core tables: `users`
  - Dimensions: `user_role`
  - Notes: 0% in current data (`mfa_enabled=False` for all rows).
- `verified_email_rate`
  - Definition: share of users with a verified email.
  - Core tables: `users`
  - Dimensions: `user_role`, `country`

---

## C. Issuer Ecosystem Health

- `total_issuers`
  - Definition: count of issuers.
  - Core tables: `issuers`
  - Dimensions: `issuer_type`, `level`, `country`
- `verified_issuers`
  - Definition: count of issuers with `status='PASSED'`.
  - Core tables: `issuers`
  - Dimensions: `issuer_type`
  - Notes: real enum is `{PASSED, PENDING, FAILED}` (not the DDL-commented `ACTIVE/...`).
- `verification_pass_rate`
  - Definition: fully-verified issuers (`status='PASSED'`) ÷ all issuers.
  - Core tables: `issuers`
  - Dimensions: `issuer_type`
  - Notes: combined identity+social pass; the single executive "Verification Pass Rate" card.
- `id_verification_pass_rate`
  - Definition: passed identity checks ÷ completed identity checks.
  - Core tables: `identity_verification`, `issuers`
  - Dimensions: `provider`, `level`, `issuer_type`
- `id_verification_opt_in_rate`
  - Definition: share of issuers who opted into identity verification.
  - Core tables: `identity_verification`, `issuers`
  - Dimensions: `issuer_type`, `provider`, `country`
- `id_verification_completion_rate`
  - Definition: completed identity checks ÷ initiated identity checks.
  - Core tables: `identity_verification`, `issuers`
  - Dimensions: `provider`, `issuer_type`
- `manual_review_rate`
  - Definition: checks in manual review ÷ all identity checks.
  - Core tables: `identity_verification`, `issuers`
  - Dimensions: `provider`, `issuer_type`
- `social_verification_pass_rate`
  - Definition: successful social verifications ÷ total social verification attempts.
  - Core tables: `social_verification`, `issuers`
  - Dimensions: `platform`, `issuer_type`
- `social_verification_retry_rate`
  - Definition: average social verification attempts per flow.
  - Core tables: `social_verification`, `issuers`
  - Dimensions: `platform`, `issuer_type`
- `issuer_activation_rate`
  - Definition: issuers with a live token and at least one completed sale ÷ all issuers.
  - Core tables: `issuers`, `tokens`, `transactions`
  - Dimensions: `issuer_type`
  - Notes: redefined (no waitlist); old waitlist definition is retired.
- `token_launch_success_rate`
  - Definition: issuers who successfully minted/launched a live token ÷ issuers who attempted.
  - Core tables: `issuers`, `tokens`
  - Dimensions: `issuer_type`
- `issuer_revenue`
  - Definition: revenue per issuer (net of the platform take).
  - Core tables: `issuer_daily_revenue`
  - Dimensions: `issuer_id`, `date`
  - Value basis: `issuer_net`
  - Notes: net 80%; joins cleanly to `issuers.issuer_id`. Source for the issuer-revenue derivatives below.
- `average_revenue_per_issuer`
  - Definition: mean issuer revenue across issuers.
  - Core tables: `issuer_daily_revenue`, `issuers`
  - Dimensions: `issuer_type`, `time_grain`
  - Value basis: `issuer_net`
- `top_issuer_revenue_share`
  - Definition: share of issuer revenue held by the top-N issuers.
  - Core tables: `issuer_daily_revenue`, `issuers`
  - Dimensions: `issuer_type`, `time_window`
  - Value basis: `issuer_net`
- `issuer_revenue_growth`
  - Definition: period-over-period growth in issuer revenue.
  - Core tables: `issuer_daily_revenue`
  - Dimensions: `issuer_id`, `time_grain`
  - Value basis: `issuer_net`
- `issuers_with_zero_revenue`
  - Definition: count/share of issuers with no revenue.
  - Core tables: `issuers`, `issuer_daily_revenue`
  - Dimensions: `issuer_type`
  - Value basis: `issuer_net`
- `athlete_vs_creator_split`
  - Definition: distribution of issuers by `issuer_type`.
  - Core tables: `issuers`
  - Dimensions: `issuer_type`, `level`
- `social_reach_verified_issuers`
  - Definition: aggregate follower reach of verified issuers.
  - Core tables: `social_verification`, `issuers`
  - Dimensions: `platform`, `issuer_type`
  - Notes: sum `followers_count` where verified.
- `profile_completion_rate_by_issuer_type`
  - Definition: share of issuers with profile completion above threshold by type.
  - Core tables: `issuers`, `athlete_profile`, `creator_profile`
  - Dimensions: `issuer_type`, `sport`, `creator_category`
  - Notes: athlete-only in current data (`creator_profile` is unpopulated).
- `issuer_onboarding_completion_rate`
  - Definition: share of issuers who completed onboarding.
  - Core tables: `issuer_post_signup`, `issuers`
  - Dimensions: `issuer_type`
- `wallet_provisioning_success_rate`
  - Definition: share of issuers with a provisioned wallet.
  - Core tables: `issuer_post_signup`
  - Dimensions: `issuer_type`
- `oauth_verification_completion_rate`
  - Definition: share of issuers who verified ≥2 platforms (`oauth_verified_min2`).
  - Core tables: `issuer_post_signup`
  - Dimensions: `issuer_type`

---

## D. Financial & Business

- `amount_raised_vs_target`
  - Definition: amount raised compared to issuer target raise.
  - Core tables: `transactions`, `tokens`, `issuer_preferences`, `issuers`
  - Dimensions: `issuer_type`, `sport`, `creator_category`
  - Value basis: `token_revenue_gross`
  - Notes: `raise_target_usd` is random in dummy data — structurally valid, not meaningful yet.
- `percent_supply_sold_30d`
  - Definition: quantity sold in first 30 days ÷ initial supply.
  - Core tables: `tokens`, `transactions`
  - Dimensions: `token_id`, `issuer_type`, `token_symbol`
- `supply_remaining`
  - Definition: `initial_supply − total_sold` per token.
  - Core tables: `tokens`
  - Dimensions: `token_id`, `issuer_id`
- `average_revenue_per_token`
  - Definition: mean revenue per token.
  - Core tables: `tokens`
  - Dimensions: `issuer_id`
  - Value basis: `token_revenue_gross`
- `revenue_growth_rate`
  - Definition: period-over-period growth in total token revenue.
  - Core tables: `transactions`
  - Dimensions: `time_grain`
  - Value basis: `token_revenue_gross`
- `revenue_concentration`
  - Definition: dependence of revenue on top issuers/tokens.
  - Core tables: `issuer_daily_revenue`, `issuers`
  - Dimensions: `issuer_type`, `time_window`
  - Value basis: `issuer_net`
- `platform_fee_revenue`
  - Definition: platform take = total token revenue × 0.2 (equivalently total minus issuer net).
  - Core tables: `transactions`, `issuer_daily_revenue`
  - Dimensions: `time_grain`
  - Value basis: `platform_fee`
  - Notes: SYNTHETIC constant until a real fee ledger / secondary market exists; flag in any output. Aggregate difference, not a row join.

---

## E. Compliance, Trust & Risk

- `suspended_accounts`
  - Definition: count/share of suspended or restricted accounts.
  - Core tables: `users`
  - Dimensions: `user_role`, `country`
  - Notes: 0 in current data (all `account_status='ACTIVE'`).
- `failed_identity_checks`
  - Definition: count/share of failed identity checks (fraud/risk signal).
  - Core tables: `identity_verification`, `issuers`
  - Dimensions: `provider`, `issuer_type`
- `high_risk_wallet_concentration`
  - Definition: concentration heuristic flagging high-risk holding concentration.
  - Core tables: `user_token_wallet`
  - Dimensions: `token_id`
- `country_distribution`
  - Definition: geographic distribution of users/issuers (compliance view).
  - Core tables: `users`, `issuers`
  - Dimensions: `country`, `user_role`, `issuer_type`

---

## Known Data Caveats (current dummy data)

A `0` or flat reading on these is **correct**, not a bug — the generator simply has no variation yet: `mfa_adoption_rate` (0%), `suspended_accounts` (0), `failed_reversed_transactions` (0), `secondary_market_share` (0%), and anything using `current_supply_minted` (always 0). Also: `creator_profile` is empty (the profile-completion KPI is athlete-only), `seller_id` is the issuer's user on every primary sale, and `issuers.status` uses `PASSED/PENDING/FAILED`.

---

## Source Anchors
- Primary source of truth: `athl_north_star_executive_dashboard_kpis.md` (active set).
- Schema: `athl_raw_tables_postgres.sql`.
- Data semantics: `generate_and_load_data_neon.ipynb`.
- Runtime catalog: `app/rag/catalog/kpi_catalog.json` (validated by `kpi_catalog.py`).
- Mechanically generated inventory (grouped by `section`): `kpi_inventory_grouped_by_section.md`.
- This file absorbed the former `kpi_canonical_overview.md` reader companion (now `docs/archive/`).
