# Canonical KPI List v1

## Selection Notes
- This list prioritizes KPIs requested in product requirement docs.
- KPIs are split into executable now vs blocked by missing event datasets.
- The active set is intentionally small and stable.

## Active KPIs (Computable with Current Schema)

1. `issuer_type_distribution`
- Definition: count of issuers by `issuer_type`.
- Core tables: `issuers`.
- Dimensions: `issuer_type`, `country`, `level`.

2. `profile_completion_rate_by_issuer_type`
- Definition: share of issuers with profile completion above threshold by issuer type.
- Core tables: `issuers`, `athlete_profile`, `creator_profile`.
- Dimensions: `issuer_type`, `sport`, `creator_category`.

3. `id_verification_opt_in_rate`
- Definition: ratio of identity verification records opted in vs total eligible issuers.
- Core tables: `identity_verification`, `issuers`.
- Dimensions: `issuer_type`, `country`.

4. `id_verification_pass_rate`
- Definition: ratio of passed identity checks to completed identity checks.
- Core tables: `identity_verification`.
- Dimensions: `provider`, `level`.

5. `id_verification_completion_rate`
- Definition: ratio of checks with `completed_at` present vs initiated checks.
- Core tables: `identity_verification`.
- Dimensions: `provider`, `issuer_type`.

6. `manual_review_rate`
- Definition: ratio of identity checks in manual review status vs initiated checks.
- Core tables: `identity_verification`.
- Dimensions: `provider`, `issuer_type`.

7. `social_verification_success_rate`
- Definition: successful social verifications divided by total social verification attempts.
- Core tables: `social_verification`.
- Dimensions: `platform`, `issuer_type`.

8. `social_verification_retry_rate`
- Definition: average attempts per social verification flow.
- Core tables: `social_verification`.
- Dimensions: `platform`, `issuer_type`.

9. `waitlist_approval_rate`
- Definition: approved waitlist entries divided by total waitlist entries.
- Core tables: `waitlist`.
- Dimensions: `status`, `issuer_type`.

10. `issuer_activation_rate`
- Definition: activated waitlist entries divided by total approved entries.
- Core tables: `waitlist`, `issuers`.
- Dimensions: `issuer_type`, `country`.

11. `amount_raised_vs_target`
- Definition: raised capital compared against issuer target raise.
- Core tables: `transactions`, `issuer_preferences`, `tokens`, `issuers`.
- Dimensions: `issuer_type`, `sport`, `creator_category`.

12. `percent_supply_sold_30d`
- Definition: tokens sold as a percentage of initial supply in first 30 days after mint.
- Core tables: `tokens`, `transactions`.
- Dimensions: `issuer_type`, `token_symbol`.

13. `issuer_daily_revenue`
- Definition: daily revenue totals per issuer from revenue table.
- Core tables: `issuer_daily_revenue`.
- Dimensions: `date`, `issuer_id`.

14. `token_leaderboard_most_traded`
- Definition: ranking of tokens by trading volume or transaction count over a selected window.
- Core tables: `transactions`, `tokens`.
- Dimensions: `time_window`, `token_id`, `issuer_type`.

## Blocked KPIs (Defined, Not Yet Executable)

1. `login_attempt_volume`
- Missing dependency: authentication event table with per-attempt records.

2. `session_timeout_rate`
- Missing dependency: session lifecycle events with timeout reason.

3. `mfa_success_rate`
- Missing dependency: MFA challenge/response audit events.

4. `anomaly_detection_rate`
- Missing dependency: risk engine output table with anomaly flags and timestamps.

5. `support_contact_rate`
- Missing dependency: support ticket/contact events keyed to user.

6. `referral_link_click_conversion`
- Missing dependency: referral clickstream events and attribution logs.

## Source Anchors
- KPI names and intent: `- for me/ATHL KPI Framework - KPI.csv`.
- Dashboard priorities: `- for me/ATHL Data Infrastructure Blueprint_ Internal - Ali Dashboards.pdf`.
- Leaderboard priorities: `- for me/ATHL Data Infrastructure Blueprint_ Internal - Ali Leaderboard.pdf`.
