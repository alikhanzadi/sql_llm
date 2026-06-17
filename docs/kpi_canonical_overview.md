# Canonical KPI Overview

> **Reader companion — NOT the source of truth.** This is a hand-maintained, human-readable view of the canonical KPI set. The authoritative, catalog-mappable definitions live in **`kpi_canonical_list.md`**, and the runtime truth is **`app/rag/catalog/kpi_catalog.json`**. On any conflict, those win. The mechanically generated inventory (grouped by the catalog's `section` field) is **`kpi_inventory_grouped_by_section.md`**; this overview stays hand-written so it can carry the narrative "what it answers / notes" context that the catalog does not encode.
>
> Scope: **62 active KPIs**, the full north star active set. The catalog is **flat — there are no tiers.** Blocked KPIs are omitted for now.

---

## How to read this

The KPI layer is an **optional accelerator** over deterministic schema grounding: canonical KPIs exist to give the executive view *one* blessed definition and to keep the agent's answers consistent with the dashboard. The five sections below map to the north star's five executive questions:

| Section | Executive question |
|---|---|
| A. Marketplace Health & Liquidity | Is liquidity and trading activity healthy? |
| B. User Growth & Engagement | Is the platform growing? |
| C. Issuer Ecosystem Health | Are issuers succeeding? |
| D. Financial & Business | Is the ecosystem financially sustainable? |
| E. Compliance, Trust & Risk | Are trust, compliance, and activation improving? |

Disambiguation among look-alike metrics is deterministic (deliberate aliases + per-cluster defaults), so a single-turn question resolves without a clarifying question.

---

## Revenue family (read this first)

All platform revenue comes from **one base**: the sum of completed transaction amounts (`SUM(transactions.total_amount_usdc)` where `lower(status)='completed'`). The "different" revenue metrics are just that sum at different groupings or splits, tagged with a `value_basis` so gross and net can never be confused:

| Concept | What it is | `value_basis` |
|---|---|---|
| Total token revenue | the base sum, platform-wide (the number sometimes called "GTV") | `token_revenue_gross` |
| Token revenue | the base sum grouped by token (= `tokens.total_revenue`) | `token_revenue_gross` |
| Issuer revenue | `0.8 ×` the base, per issuer — **net** (synthetic 80/20 split) | `issuer_net` |
| Platform fee revenue | `0.2 ×` the base — **synthetic**, flagged | `platform_fee` |

**Plain-language routing:** bare "revenue" → total token revenue (the default); "issuer revenue / earnings" → issuer revenue (net); "platform revenue / fees / take rate" → platform fee. The word **"volume" is never revenue** — it's reserved for quantity/count metrics.

---

## A. Marketplace Health & Liquidity

| KPI | What it answers | Notes |
|---|---|---|
| `total_token_revenue` | Total completed transaction value (platform-wide or per token) | Basis: `token_revenue_gross`. Equals `SUM(tokens.total_revenue)`. Not "volume". |
| `total_transactions` | How many completed transactions | — |
| `average_transaction_size_usdc` | Typical transaction notional | — |
| `average_token_price` | Aggregate ecosystem pricing level | `current_price` is a bonding-curve function of `total_sold`, not a market price |
| `token_price_growth_rate` | Price momentum per token (powers "top gainers") | No price history — reconstruct from `ending_price` over time (window) |
| `active_tradable_tokens` | How many tokens are live and trading | `paused_sales=false` and ≥1 completed tx |
| `tokens_with_no_trading_activity` | Dead marketplace inventory | — |
| `total_market_capitalization` | Total token ecosystem value | `SUM(current_price × total_sold)`; use `total_sold`, never `current_supply_minted` (0) |
| `token_liquidity_velocity` | How fast tokens turn over | Turnover = traded quantity ÷ supply sold |
| `token_holders_count` | Distinct holders per token | `COUNT(DISTINCT user_id) WHERE quantity > 0` |
| `token_holder_distribution` | How concentrated a token's ownership is | — |
| `wallet_concentration_ratio` | Whale ownership detection | — |
| `top_tokens_share_of_volume` | Concentration risk across tokens | Top-N share of volume |
| `token_leaderboard_most_traded` | Top tokens by traded volume (ranking) | Leaderboard — matches ranking-style questions only |
| `buy_vs_sell_ratio` | Market buy/sell balance | Degenerate now (all transactions primary) |
| `secondary_market_share` | Share of volume from secondary trading | 0% until secondary trading exists |
| `failed_reversed_transactions` | Reliability/trust signal | 0 in current data |

## B. User Growth & Engagement

| KPI | What it answers | Notes |
|---|---|---|
| `net_new_users` | New users acquired by period | Covers new users per day/week/month |
| `total_registered_users` | Total user base | — |
| `user_growth_rate` | User growth momentum | — |
| `active_traders` | Distinct users trading in a period | Distinct `buyer_id`; MAT = month grain |
| `active_sellers` | Distinct sellers in a period | Sellers = issuers in current data (primary sales) |
| `buyer_to_seller_ratio` | Marketplace balance | Confounded until secondary trading |
| `repeat_buyer_rate` | Early engagement / stickiness | Buyers with >1 completed transaction |
| `multi_token_ownership_rate` | Ecosystem exploration | Holders owning >1 token |
| `average_wallet_balance` | User financial participation | Wallet values are cost-basis, not mark-to-market |
| `funded_wallet_rate` | Share of wallets with a positive balance | — |
| `mfa_adoption_rate` | Security adoption | 0% in current data (`mfa_enabled=False` for all) |
| `verified_email_rate` | Trust / activation | — |

## C. Issuer Ecosystem Health

| KPI | What it answers | Notes |
|---|---|---|
| `total_issuers` | How many issuers exist | — |
| `verified_issuers` | How many issuers are fully verified | `status='PASSED'` (real enum: PASSED/PENDING/FAILED) |
| `verification_pass_rate` | Share of issuers fully verified | Combined identity + social; the executive card |
| `id_verification_pass_rate` | Passed ÷ completed identity checks | — |
| `id_verification_opt_in_rate` | Opt-in to identity verification | — |
| `id_verification_completion_rate` | Completed ÷ initiated identity checks | — |
| `manual_review_rate` | Checks routed to manual review | — |
| `social_verification_pass_rate` | Successful ÷ total social verifications | — |
| `social_verification_retry_rate` | Avg social verification attempts per flow | — |
| `issuer_activation_rate` | Issuers with a live token + sales | Redefined (no waitlist) |
| `token_launch_success_rate` | Issuers who successfully launched a token | — |
| `issuer_revenue` | Revenue per issuer (net of platform take) | Basis: `issuer_net`. Source for the derivatives below |
| `average_revenue_per_issuer` | Mean issuer revenue | Basis: `issuer_net` |
| `top_issuer_revenue_share` | Concentration on top issuers | Basis: `issuer_net` |
| `issuer_revenue_growth` | Issuer revenue momentum | Basis: `issuer_net` |
| `issuers_with_zero_revenue` | Supply-side quality issue | Basis: `issuer_net` |
| `athlete_vs_creator_split` | Strategic supply composition | By `issuer_type` |
| `social_reach_verified_issuers` | Follower reach of verified issuers | Sum `followers_count` where verified |
| `profile_completion_rate_by_issuer_type` | Profile completeness by type | Athlete-only now (`creator_profile` unpopulated) |
| `issuer_onboarding_completion_rate` | Onboarding funnel completion | — |
| `wallet_provisioning_success_rate` | Wallet provisioned during onboarding | — |
| `oauth_verification_completion_rate` | Issuers verifying ≥2 platforms | `oauth_verified_min2` |

## D. Financial & Business

| KPI | What it answers | Notes |
|---|---|---|
| `amount_raised_vs_target` | Raised vs issuer target | Basis: `token_revenue_gross`. Target is random in dummy data |
| `percent_supply_sold_30d` | First-30-day sell-through | Sold ÷ initial supply |
| `supply_remaining` | Unsold supply per token | `initial_supply − total_sold` |
| `average_revenue_per_token` | Token monetization efficiency | Basis: `token_revenue_gross` |
| `revenue_growth_rate` | Total revenue momentum | Basis: `token_revenue_gross` |
| `revenue_concentration` | Dependence on top issuers/tokens | Basis: `issuer_net` |
| `platform_fee_revenue` | What the platform earns in fees | Basis: `platform_fee`. **Synthetic** (0.2 × revenue) until a real ledger exists — flag in output |

## E. Compliance, Trust & Risk

| KPI | What it answers | Notes |
|---|---|---|
| `suspended_accounts` | Restricted/suspended accounts | 0 in current data (all `account_status='ACTIVE'`) |
| `failed_identity_checks` | Fraud/risk signal | — |
| `high_risk_wallet_concentration` | High-risk holding concentration | Heuristic |
| `country_distribution` | Geographic compliance view | — |

---

## Known data caveats (current dummy data)

A `0` or flat reading on these is **correct**, not a bug — the generator simply has no variation yet: `mfa_adoption_rate` (0%), `suspended_accounts` (0), `failed_reversed_transactions` (0), `secondary_market_share` (0%), anything using `current_supply_minted` (0). Also: `creator_profile` is empty (profile KPI is athlete-only), `seller_id` is the issuer's user on every primary sale, and `issuers.status` uses `PASSED/PENDING/FAILED`.

## Source anchors
- Authoritative definitions: `kpi_canonical_list.md`
- Runtime catalog: `app/rag/catalog/kpi_catalog.json` (validated by `kpi_catalog.py`)
- Business priority source: `athl_north_star_executive_dashboard_kpis.md`
- Schema: `athl_raw_tables_postgres.sql` · Data semantics: `generate_and_load_data_neon.ipynb`
