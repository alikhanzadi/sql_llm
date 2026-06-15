# Canonical KPI List v2

> **COMPANION / READER VIEW — NOT THE SOURCE OF TRUTH.**
> The authoritative, catalog-mappable definitions live in `kpi_canonical_list.md`.
> This file is a narrative overview for humans. Note: the **tier_1/tier_2 labels below are deprecated** — the runtime catalog is now **flat (no tiers)**; matcher priority is handled by aliases + per-cluster default-resolution. Treat tiering here as illustrative history only.

---


> **Status:** Draft for ratification. This rewrite is anchored to `athl_north_star_executive_dashboard_kpis.md` (the source of truth) and validated against the live schema (`athl_raw_tables_postgres.sql`) and the data generator (`generate_and_load_data_neon.ipynb`).
> **Supersedes:** `kpi_canonical_list_v1.md`.

---

## 0. What "canonical" means here

This is an NL-to-SQL system, not a BI dictionary. A KPI earns a place in `kpi_catalog.json` only when **schema-only LLM generation would get it wrong or inconsistent**, or when **the dashboard number must match the agent's answer exactly**. Three bars:

1. **Business priority** — it maps to an executive question in the north star.
2. **Computable** on the current schema.
3. **Trap risk** — non-obvious join, weighted ratio, business threshold, window rule, value-basis ambiguity, or a filter default the model would otherwise drop.

Pure single-table `COUNT`/`SUM` metrics fail bar 3: the model writes them correctly, and as catalog entries they mostly cause ambiguity collisions. Those move to inventory-only (Section 5).

---

## 0.5 Layer 1 build scope (reconciled with `implementation_scope.md`)

Per `implementation_scope.md`, the KPI layer is an **optional accelerator** over deterministic schema grounding, and Layer 1 keeps the canonical set **small (10–15 Tier A KPIs)**. The full set in Sections 2–3 is the **v2.1 semantic-layer target**; only the Tier A subset is built now.

**Tier A — canonical now (build in Layer 1):**
`gross_transaction_volume`, `total_token_revenue`, `issuer_revenue`, `amount_raised_vs_target`, `percent_supply_sold_30d`, `token_leaderboard_most_traded`, `token_holders_count`, `token_price_change_24h`, `verification_pass_rate`, `profile_completion_rate_by_issuer_type`, `platform_fee_revenue`, `issuer_activation_rate`.

**Tier B — schema-grounded now (documented in inventory, no catalog entry yet):** everything else in Sections 2–3 — `net_new_users`, `active_issuers`, `active_tradable_tokens`, `total_market_capitalization`, `monthly_active_traders`, `token_liquidity_velocity`, the granular id/social verification rates, the averages, wallet/holder distributions, `country_distribution`, etc. Promote to canonical in v2.1 **if** the SQL-correctness eval shows generation is unreliable. The trap-prone ones to watch first: `monthly_active_traders` (distinct count), `total_market_capitalization` (product of columns), `token_liquidity_velocity` (cross-table ratio).

**Tier C — deferred (blocked / event tables absent):** the blocked set in Section 4.

> **Confirm:** the Tier A membership above is the proposed Layer 1 cut. Open question — keep only combined `verification_pass_rate` in Tier A (current proposal), or also include the granular id/social rates that `implementation_scope.md` lists as Tier A candidates?

---

## 1. Revenue value-basis taxonomy (the centerpiece — root of Issue #5)

The generator builds three revenue numbers at **different scales**. Every revenue KPI MUST declare a `value_basis` so the agent never returns one when the user meant another (the gap is 20%).

| `value_basis` | Source of truth | Scale | Definition |
|---|---|---|---|
| `gtv` | `SUM(transactions.total_amount_usdc)` | gross (100%) | Gross marketplace throughput (all completed transactions) |
| `token_sales_gross` | `SUM(tokens.total_revenue)` | gross (100%) | Gross token sales; `tokens.total_revenue` is built as summed primary transactions per token, so it equals per-token GTV today and diverges only once secondary trading is enabled |
| `issuer_net` | `SUM(issuer_daily_revenue.total_amount_usdc)` | **net (80%)** | Issuer proceeds after an implied 20% platform take (generator multiplies by `0.8`) |
| `platform_fee` | `gtv − issuer_net` (= `0.2 × gtv` by construction) | derived | **Active (ratified):** computed as the constant until a backend fee ledger exists; flagged synthetic, not a real fee schedule |

**Issue #5 fix:** the dashboard "Total Token Revenue" card = `total_token_revenue` (`value_basis: token_sales_gross`), not a transaction-volume delta.

**Platform-fee caveat (ratified):** the 20% is a generator constant, not a modeled fee schedule. Per decision, `platform_fee_revenue` is computed now as the derived constant (`gtv − issuer_net`) and carries an explicit `quality_note` that it is synthetic and must be replaced when a real fee ledger lands. `net_platform_revenue` (fees minus costs) stays blocked.

---

## 2. Tier 1 — CEO headline KPIs

Anchored to the north star top strip + MVP-15. These get matcher priority.

| `kpi_id` | Definition | `value_basis` | Core tables | Data-reality note |
|---|---|---|---|---|
| `gross_transaction_volume` | Total completed transaction volume by grain (**rename of `total_platform_revenue`**) | `gtv` | `transactions` | Filter `lower(status) = 'completed'` |
| `total_token_revenue` *(new)* | Gross token sales revenue | `token_sales_gross` | `tokens` | The Issue #5 card |
| `platform_fee_revenue` *(new, ratified)* | Platform take = gross minus issuer net | `platform_fee` | `transactions`, `issuer_daily_revenue` | Computed as constant `gtv − issuer_net` (≈0.2×gtv) until a real fee ledger; flagged synthetic |
| `issuer_revenue` | Revenue per issuer over time (**elevated from `issuer_daily_revenue`**) | `issuer_net` | `issuer_daily_revenue` | Net 80%; joins cleanly to `issuers.issuer_id` (Issue #4 resolved) |
| `monthly_active_traders` | Distinct active traders per month (**redefine of `active_trading_users`**) | — | `transactions` | Distinct `buyer_id` (ratified); seller-union deferred until secondary trades exist |
| `net_new_users` | New registered users by grain | — | `users` | `users.created_at` |
| `active_issuers` | Issuers with a live token and completed sales | — | `issuers`, `tokens`, `transactions` | Define against real enum `status='PASSED'`, **not** the DDL-documented `'ACTIVE'` |
| `active_tradable_tokens` | Tokens with ≥1 completed transaction and `paused_sales = false` | — | `tokens`, `transactions` | — |
| `total_market_capitalization` | `SUM(current_price × total_sold)` | — | `tokens` | Circulating = `total_sold`; **never** `current_supply_minted` (always 0) |
| `token_liquidity_velocity` | Token turnover (see Decision 2) | — | `transactions`, `tokens` | Formula needs ratification |
| `verification_pass_rate` | Fully-verified issuers / all issuers | — | `issuers` | `status='PASSED'` (= identity + social both passed) |
| `top_tokens_by_volume` | Token ranking by volume in window (**= `token_leaderboard_most_traded`**) | — | `transactions`, `tokens`, `issuers` | Leaderboard guardrail: ranking language required |
| `amount_raised_vs_target` | Raised vs `issuer_preferences.raise_target_usd` | `gtv` | `transactions`, `tokens`, `issuer_preferences`, `issuers` | Target is random in dummy data — ratio is structurally valid but not meaningful yet |
| `percent_supply_sold_30d` | First-30-day sold / `initial_supply` | — | `tokens`, `transactions` | — |
| `token_holders_count` *(new, customer-facing)* | Distinct holders per token | — | `user_token_wallet` | `COUNT(DISTINCT user_id) WHERE quantity > 0`; powers ATHLScan "holders" + leaderboard "most holders" |
| `token_price_change_24h` *(new, customer-facing)* | 24h price change / top gainers | — | `transactions` | No price-history table — reconstruct from `ending_price` ordered by `timestamp` per token (window trap) |
| `supply_remaining` *(new, customer-facing)* | `initial_supply − total_sold` per token | — | `tokens` | Borderline Tier B; pairs with `percent_supply_sold_30d` |

> **Token Economic Activity (TEA)** — the north star's designated north-star metric — is **`gross_transaction_volume` at month grain**, not a separate recipe. Documented as a named view of GTV to avoid a second source of truth.
>
> **Note:** this table is the **v2.1 headline set**. Layer 1 builds only the Tier A subset named in §0.5; the rest are Tier B (schema-grounded) until promoted.

---

## 3. Tier 2 — operational / trap-prone / business-defined

Still canonical and built; lower matcher priority.

**Verification & trust** (demoted from v1 tier_1 — operational, not executive):
`id_verification_pass_rate`, `id_verification_opt_in_rate`, `id_verification_completion_rate`, `manual_review_rate`, `social_verification_success_rate`, `social_verification_retry_rate`, `mfa_adoption_rate` *(caveat: 0% — `mfa_enabled=False` for all rows)*, `verified_email_rate`, `suspended_accounts` *(caveat: 0 — no restricted accounts generated)*, `country_distribution`.

**Pricing / averages (trap-prone):**
`average_selling_price` *(weighted ratio `SUM(amount)/SUM(quantity)` — guards against `AVG(price)`)*, `average_transaction_size_usdc`, `average_tokens_per_transaction`, `token_number_of_buyers`, `average_revenue_per_token`.

**Issuer ecosystem:**
`profile_completion_rate_by_issuer_type` *(caveat: **athlete-only** — `creator_profile` is never populated by the generator)*, `athlete_vs_creator_split`, `social_reach_verified_issuers`, `token_launch_success_rate`, `issuer_onboarding_completion_rate`, `wallet_provisioning_success_rate`, `oauth_verification_completion_rate`, `issuer_activation_rate` *(**un-deprecated**, redefined: issuer with live token + activity; old waitlist definition stays dead)*.

**Issuer revenue derivatives** (all `value_basis: issuer_net`):
`average_revenue_per_issuer`, `top_issuer_revenue_share`, `issuer_revenue_growth`, `issuers_with_zero_revenue`, `revenue_concentration`.

**Marketplace structure:**
`repeat_buyer_rate`, `participation_rate`, `multi_token_ownership_rate`, `funded_wallet_rate`, `average_wallet_balance` *(caveat: `total_value`/`usdc_balance` are cost-basis, not mark-to-market)*, `tokens_with_no_trading_activity`, `wallet_concentration_ratio`, `token_holder_distribution`, `top10_tokens_share_of_volume`, `failed_reversed_transactions` *(caveat: 0 — none generated)*, `buy_vs_sell_ratio` *(caveat: degenerate — all transactions are primary)*, `secondary_market_share` *(caveat: 0% — no secondary trades yet)*.

---

## 4. Blocked (curated, CEO-askable) — aligned to north star

Honest "blocked because X" beats hallucinated SQL. Trimmed to what the north star actually flags as blocked; **made tier-neutral** so a blocked KPI can't win an ambiguous match just to return "blocked."

| `kpi_id` | Missing dependency |
|---|---|
| `net_platform_revenue` | No expense/cost model (fees minus costs). `platform_fee_revenue` itself is now **active** as a derived constant — see Tier 1 |
| `revenue_per_active_user` | Depends on real platform revenue. *Derivable now from the synthetic fee constant if desired — left blocked to avoid propagating the constant.* |
| `retention_rate_30d_90d` | No event/session model (behavioral). *Note: a transaction-based repeat-activity proxy is computable and could be a separate active KPI if desired.* |
| `dau_wau_mau` | No event tracking |
| `referral_conversion_rate` | `referral_id` is null for all users; no referral graph / events |

**Retire from catalog** (old v1 blocked KPIs absent from the north star — remove to cut matcher noise): `session_timeout_rate`, `anomaly_detection_rate`, `support_contact_rate`, `login_attempt_volume`, `mfa_success_rate`. Document in inventory only.

---

## 5. Demote to inventory-only (remove from runtime catalog)

Trivial single-table metrics the model generates correctly; kept as documented metrics, not catalog entries:
`issuer_type_distribution`, `tokens_issued_count`, `total_supply_issued`, `total_purchases_by_user`, plus plain counts (`total_registered_users`, `total_transactions`, `total_issuers`).

---

## 6. Known data-reality caveats (carry into recipes + eval assertions)

These are correctness landmines the schema alone hides; the generator confirms them:

1. **Transaction status case** — data writes `status = 'completed'` (lowercase). Any recipe or doc using `'COMPLETED'` returns **zero rows**. The north star formula and v1 docs use uppercase; standardize on `lower(status) = 'completed'` everywhere and harden the soft "when available" filter notes.
2. **Issuer status enum** — DDL comments say `{ACTIVE, SUSPENDED, ARCHIVED}`; generator writes `{PASSED, PENDING, FAILED}`. Define "active/verified issuer" against the real values.
3. **`creator_profile` is empty** — only `athlete_profile` is generated. Any issuer-profile KPI is athlete-only until creator profiles exist.
4. **Degenerate-on-dummy-data (valid recipe, no signal yet, so `0` ≠ bug):** MFA adoption (0%), suspended accounts (0), reversed transactions (0), secondary market share (0%), anything using `current_supply_minted` (0).
5. **Pipeline smell** — notebook cell 16 re-COPYs `issuer_daily_revenue` after cell 15; the `(issuer_id, date)` PK should reject the duplicate, but clean it up.
6. **Internal scale inconsistency** — `user_wallet.usdc_balance` credits issuers ~gross, while `issuer_daily_revenue` is net 80%. Don't cross-reference the two as the same revenue figure.

---

## 7. Decisions — RATIFIED

**Resolved:** (1) MAT = distinct `buyer_id` only for now. (2) `token_liquidity_velocity` = traded quantity ÷ `total_sold`. (3) **Amended** — `platform_fee_revenue` computed as the derived constant (`gtv − issuer_net`) until a backend ledger exists, flagged synthetic. (4) `verification_pass_rate` = issuers `status='PASSED'` ÷ all issuers; granular id/social rates stay tier_2. (5) Demotions approved. (6) Retirements approved.

Original options, for the record:

1. **MAT scope:** distinct `buyer_id` only (recommended now), or `buyer_id ∪ seller_id`? In the data `seller_id` = the issuer's `user_id` on every primary sale, so the union folds all issuers into "traders" and inflates the metric.
2. **`token_liquidity_velocity` formula:** proposed = period traded quantity ÷ `total_sold` (turnover). Confirm or specify alternative.
3. **Platform fee revenue:** keep blocked/caveated (recommended), or expose `0.2 × gtv` despite it being a synthetic constant?
4. **`verification_pass_rate`:** single card = issuers `status='PASSED'` ÷ all issuers, with the granular id/social rates staying tier_2 — confirm.
5. **Demotions (Section 5):** OK to remove those four+ trivial KPIs from the runtime catalog?
6. **Retirements (Section 4):** OK to drop the non-north-star blocked security KPIs?

---

## 8. Source anchors

- **Primary source of truth:** `athl_north_star_executive_dashboard_kpis.md`
- **Schema:** `athl_raw_tables_postgres.sql`
- **Data semantics:** `generate_and_load_data_neon.ipynb`
- **Runtime catalog:** `app/rag/catalog/kpi_catalog.json` (validated by `kpi_catalog.py`)
