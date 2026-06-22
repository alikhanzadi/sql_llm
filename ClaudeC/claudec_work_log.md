# ClaudeC Work Log

## What This File Is For

This is the project-wide human-readable work log for ClaudeC sessions. Keep it updated whenever we discuss an approach, decide priorities, or make meaningful changes.

Use this file for:

- Task intros: the problem, agreed approach, and scope before implementation.
- High-level change notes: what changed and why.
- Verification notes: what was run and what passed or failed.
- Follow-up context: known remaining work, risks, and next steps.

Do not use this file for raw terminal transcripts. Raw commands and command outputs belong in `ClaudeC/claudec_command_log.txt`, following its existing command-log format.

## 2026-06-16: KPI Comprehension Pipeline Revamp

### Task Intro

The app's KPI catalog held the wrong/old metric set (28 KPIs). The north star executive dashboard was used to build a new canonical list (`docs/kpi_canonical_list.md`, 62 KPIs across five executive sections). The goal of this pass was to update the entire KPI comprehension pipeline to match that canonical list, per the handoff `docs/kpi_sources/claude_code_handoff_kpi_revamp.md`.

Agreed scope:

- Rebuild `app/rag/catalog/kpi_catalog.json` as a flat (no-tier) catalog of the full north star active set, with `value_basis` on revenue KPIs and verified recipes.
- Update `app/rag/catalog/kpi_catalog.py` to validate `value_basis` and multi-table rules; drop tier handling.
- Update `app/llm/kpi_matcher.py` with cluster default-resolution and a `value_basis` guardrail; remove tier-boost.
- Eliminate `app/llm/metric_resolver.py` (redundant with, and contradictory to, the KPI matcher).
- Update `app/eval/planner_kpi_cases.json` (remove retired-KPI cases, add new routing cases).
- Generate `docs/kpi_inventory_grouped_by_section.md` from the catalog (anti-drift, Part G).

Pre-implementation decisions from the user:

- Renames: `issuer_daily_revenue` → `issuer_revenue`, `social_verification_success_rate` → `social_verification_pass_rate`, `issuer_type_distribution` → `athlete_vs_creator_split`.
- Drop all current KPIs not in the canonical list.
- Keep KPI matching lexical (no Chroma embeddings for KPIs); fix the catalog first. Part C (re-embedding) is a no-op because KPI matching is lexical, not vector-based.

### High-Level Changes

- Rebuilt `kpi_catalog.json` to version 2.0.0: 62 KPIs, flat structure, all active finance KPIs carry `value_basis` (`token_revenue_gross` / `issuer_net` / `platform_fee`). Added a `revenue_cluster` block declaring `total_token_revenue` as the bare-"revenue" default with non-overlapping member aliases.

- Updated the validator (`kpi_catalog.py`): removed tier handling, added `VALID_VALUE_BASIS`, required `value_basis` on active finance KPIs, and required either `required_joins` or a `multi_table_rationale` on multi-table active KPIs.

- Reworked `kpi_matcher.py`:
  - Removed tier-boost scoring.
  - Added a revenue-cluster default (`total_token_revenue`) and a `_resolve_ambiguous` helper.
  - Added a `_longest_match_in_question` specificity signal and a wide-margin resolver: when several candidates tie within `AMBIGUOUS_MARGIN` (the 0.99 score cap collapses strong matches), the candidate with the longest exact name/alias substring in the question wins. This breaks 5-way ties correctly.
  - Reordered resolution rules so specificity is tried before the value_basis cluster-default fallback.

- Fixed the catalog routing surface: added targeted aliases / fixed example questions across ~20 KPIs so each KPI's representative question routes to itself. Removed a redundant self-alias on `issuer_revenue` (double-scoring), and renamed `Issuers With Zero Revenue` → `Zero Revenue Issuers` to remove a spurious `"with"` token overlap that hijacked generic "issuers with ..." questions.

- Deleted `app/llm/metric_resolver.py` and removed all references: dropped its import/call from `generate_sql.py`, removed `metric_resolution` from `SqlPlanningContext` and its debug logging, and removed the `metric_block` parameter and "Metric Resolution block" language from `prompts.py`.

- Updated `app/eval/planner_kpi_cases.json`: removed the two retired-KPI cases (`active_waitlist_approval`, `blocked_login_attempts`), added seven Part E routing cases with intents/grains corrected to the planner's actual output, and replaced a now-colliding fallback case.

- Added `app/rag/catalog/generate_kpi_docs.py` (Part G) which renders `docs/kpi_inventory_grouped_by_section.md` from the catalog, grouped by the five north star executive sections. Stops hand-maintaining the inventory.

### Verification Notes

- Catalog validates: `OK: 62 KPIs loaded`, version 2.0.0.
- Per-KPI routing precision pass: `62/62` representative questions route to their own `kpi_id` (started at 42/62 before alias/resolver fixes).
- Revenue-cluster + leaderboard smoke tests pass (bare "revenue" → `total_token_revenue`; generic "what are all the tokens" does not match the leaderboard KPI).
- `app/eval/run_planner_kpi_eval.py`: `11 passed / 0 failed`.
- `generate_sql` pipeline builds context end-to-end without the LLM call (`intent=sum`, `kpi=total_token_revenue` for a revenue question).
- `grep -r metric_resolver --include=*.py` returns no references.

### Follow-Up Context

- Part F (Neon verification) is outstanding on the user's side: run the seven SQL checks from the handoff against the live DB to confirm data facts (status case = lowercase `completed`, issuer net ≈ 0.80 of gross, `tokens.total_revenue` equals summed completed transactions per token, `current_supply_minted` = 0, `creator_profile` empty, issuer status enum = {PASSED, PENDING, FAILED}, and each tricky recipe returns rows).
- All changes are uncommitted working-tree edits; nothing has been committed.
- Optional Part G item not yet done: add a CI lint asserting every catalog `kpi_id` appears in the generated inventory, every active finance KPI has a `value_basis`, and every multi-table active KPI has `required_joins` or `multi_table_rationale`.

## 2026-06-16: ClaudeC Logging Setup

### Task Intro

Mirror the codex logging convention under a new `ClaudeC/` folder so ClaudeC sessions keep the same two-record structure: a raw terminal command log and a readable work log, plus the chat-prompt capture.

### High-Level Changes

- Created `ClaudeC/` with three files mirroring the codex folder: `chat prompt.md`, `claudec_work_log.md`, and `claudec_command_log.txt`.
- `claudec_command_log.txt` follows the codex `$ command` → output → `[exit N]` format with "Command log continued:" timestamps. Outputs longer than 50 lines are trimmed with an explicit marker (plain `.txt` cannot collapse; a markdown variant can be substituted if collapsing is preferred).
- Recorded the KPI revamp session's key terminal activity and decisions in the command log and this work log.

## 2026-06-16: Full Project Review + Phased Roadmap

### Task Intro

User requested a complete project review (current state, immediate issues, product-readiness assessment, next steps) followed by a reprioritized phased plan. Priorities, in the user's words: Phase 1 (bleeding into Phase 2) is **SQL correctness + KPI comprehension**; second priority is a **conversational chat feature** (follow-up questions + user correction of the LLM). Security, testing/CI, and observability are explicitly deferred.

### High-Level Changes

No code changes. Produced:
- A full review (architecture snapshot, prioritized issues table, product scorecard).
- A 3-phase roadmap: P1 SQL correctness & KPI comprehension; P2 conversational chat (follow-ups + correction), overlapping P1; P3 hardening/operability (deferred items).

### Review Findings (summary)

- Strengths: clean deterministic scaffolding around the LLM (planner + flat KPI catalog + sqlparse SELECT-only validator + read-only pooled execution); 62/62 routing; 11/11 planner eval; no secrets leaked.
- Top gaps: no SQL-correctness eval (only routing eval exists); no tests; PII rows sent to the explainer LLM; retriever embeds on every query; empty-result cache bug; keyword-only SQL blocklist.

## 2026-06-16: Pre-Phase-1 Audit (docs + modules conform to revamped KPI structure)

### Task Intro

Before starting Phase 1, the user asked to confirm complete component-level and holistic understanding, verify every KPI app/document reflects the revamped (flat, 62-KPI, value_basis) structure, answer whether `generate_kpi_docs`/`run_planner_kpi_eval` need running, and advise (without changing anything yet) on combining `kpi_catalog_spec.md` + `kpi_canonical_overview.md` + `implementation_scope.md`.

### Audit Results

Actual catalog facts (verified): version 2.0.0, 62 KPIs, all `active`, flat (no `tier` field), value_basis ∈ {`token_revenue_gross`, `issuer_net`, `platform_fee`}, revenue_cluster default = `total_token_revenue`. Categories: marketplace 17, growth 12, finance 11, trust 11, issuer 10, leaderboard 1.

Document conformance:
- `kpi_canonical_list.md` — current (source of truth). No change needed.
- `kpi_inventory_grouped_by_section.md` — IN SYNC; re-running `generate_kpi_docs.py` produced no diff.
- `kpi_catalog_spec.md` — **STALE**: still documents `tier`/`tier_1`/`tier_2`, tier-boost matcher bias, "28 KPIs"; missing value_basis, multi_table_rationale, cluster default-resolution, specificity resolver.
- `kpi_canonical_overview.md` — **STALE (companion, not source of truth)**: deprecated tier framing, value_basis names `gtv`/`token_sales_gross` (catalog uses `token_revenue_gross`), and 6 stale kpi_ids absent from the catalog (`gross_transaction_volume`, `monthly_active_traders`, `active_issuers`, `top_tokens_by_volume`, `token_price_change_24h`, `average_selling_price`); contains unresolved "Confirm"/open-question prompts.
- `implementation_scope.md` — header already flags sizing/tiering as superseded; architecture + intent taxonomy + the "40–60 question assertion-based eval" remain valid and are the Phase 1 target.

Module conformance (all confirmed consistent with revamped structure): `kpi_matcher.py`, `generate_sql.py`, `prompts.py`, `kpi_catalog.json`, `kpi_catalog.py`, `planner_kpi_cases.json`.

Run-or-not answers:
- `generate_kpi_docs.py`: NOT needed now (inventory already in sync); re-run only after future catalog edits.
- `run_planner_kpi_eval.py`: writes nothing (verification only); currently 11/11. Run to confirm regressions, not to sync state.

### Consolidation Recommendation (pending user approval — no changes made)

Do NOT merge all three. They have different purposes and change-rates:
- KPI definitions (business): `kpi_canonical_list.md` (source of truth) + `kpi_canonical_overview.md` (narrative) genuinely overlap → fold the overview's evergreen parts (value-basis taxonomy, data-reality caveats, ratified decisions) into the canonical list and retire the duplicated/stale tier tables.
- Runtime contract (engineering, code-coupled): `kpi_catalog_spec.md` stays separate; UPDATE it to the flat/value_basis/cluster model.
- Architecture/scope: `implementation_scope.md` stays separate (or split evergreen architecture into its own file); keep the superseded header.
Rationale: merging a code-coupled contract and an architecture rationale into a business definitions doc couples three independent change-rates into one file → churn and rot.

## 2026-06-17: Decisions Locked + Section-Field Fix

### Decisions (user-ratified)

- **No doc merging.** Keep two distinct KPI docs: `kpi_canonical_list.md` = clean, list-like source of truth; `kpi_canonical_overview.md` = reader-friendly context companion. `implementation_scope.md` stays separate; `kpi_catalog_spec.md` stays separate (and gets updated).
- **`kpi_canonical_overview.md` was replaced by the user with a non-stale version — reviewed and APPROVED.** Verified: 62/62 exact ID match with the catalog (none missing, none orphaned), tiers removed, value_basis names corrected to `token_revenue_gross`/`issuer_net`/`platform_fee`, all "Confirm?" open questions resolved.

### Section-placement finding (the real issue)

The auto-generated `kpi_inventory_grouped_by_section.md` disagrees with both human docs on 15 KPIs because the generator infers section from the catalog `category` field. Ground truth:

| KPI | canonical_list (truth) | overview (hand) | inventory (generated) |
|---|---|---|---|
| `total_token_revenue` | A. Marketplace | A. Marketplace | **D. Financial** (wrong) |
| `issuer_revenue` | C. Issuer | C. Issuer | **D. Financial** (wrong) |

The list and overview agree (correct); the generated inventory is the outlier (groups by `category=finance`→D). Fix = add an explicit `section` field (A–E) to the catalog and group by it. `category` is retained (drives the `finance`→value_basis and `leaderboard`→guardrail rules).

## 2026-06-17: Phase Roadmap (reprioritized — agreed)

Priorities: **P1 = SQL correctness + KPI comprehension** (bleeds into P2); **P2 = conversational chat** (follow-ups + user correction); **P3 = hardening** (security, tests/CI, observability — explicitly deferred).

### Phase 1.0 — Doc-truing (do first; foundation for the eval)

| ID | Task | Files | Done-when |
|---|---|---|---|
| T0.1 | Add `section` (A–E) to all 62 KPIs, sourced from canonical_list; keep `category` | `app/rag/catalog/kpi_catalog.json` | every KPI has a valid section |
| T0.2 | Validate `section` ∈ {A,B,C,D,E}; add to required fields | `app/rag/catalog/kpi_catalog.py` | validator enforces it |
| T0.3 | Group generator by `section` (drop `CAT2SEC` guess) | `app/rag/catalog/generate_kpi_docs.py` | groups by section |
| T0.4 | Regenerate inventory; confirm it matches list+overview; re-run planner eval | `docs/kpi_inventory_grouped_by_section.md` | inventory matches; 11/11 eval |
| T0.5 | Update stale spec: drop tiers/tier-boost/"28"; add value_basis, multi_table_rationale, section, cluster + specificity resolution, refreshed counts | `docs/kpi_catalog_spec.md` | spec matches code+catalog |
| T0.6 | Reword overview header (stays hand-maintained, not auto-generated) | `docs/kpi_canonical_overview.md` | header accurate |

### Phase 1.1 — SQL-correctness eval harness

| ID | Task | Files |
|---|---|---|
| T1.1a | Build assertion-based eval: 1 NL question per active KPI (40–60), assertions derived FROM the catalog (required_tables, required_joins, filters incl. `lower(status)='completed'`, aggregation pattern, time grain) | new `app/eval/run_sql_correctness_eval.py` |
| T1.1b | Cases generated dynamically from catalog (honor "never drift") | catalog-driven |

### Phase 1.2 — Baseline + close failures

| ID | Task | Files |
|---|---|---|
| T1.2a | Run harness; record baseline pass rate per intent/section | — |
| T1.2b | Close failures by tightening `sql_recipe` + injection (not by loosening assertions) | `kpi_catalog.json`, `app/llm/prompts.py` |

### Phase 1.3 — Strengthen the KPI→SQL bridge

| ID | Task | Files |
|---|---|---|
| T1.3a | Make `to_prompt_block()` directive: explicit numerator/denominator/group_by/filters | `app/llm/kpi_matcher.py` |
| T1.3b | Always surface `value_basis` (gross/net/fee) in the prompt | `app/llm/prompts.py` |

### Phase 1 — deferred within scope (not in current batch)

| ID | Task |
|---|---|
| T1.4 | Part F Neon verification (user runs the 7 SQL checks; grounds eval assertions) |
| T1.5 | Paraphrase-robustness set (questions without literal aliases) to measure true matcher precision |

### Phase 2 — Conversational chat (follow-ups + correction)

| ID | Task | Files |
|---|---|---|
| T2.1 | Conversation state: thread prior turns (question, SQL, result summary, plan+KPI decision) into next generation | `app/ui.py`, `app/llm/generate_sql.py` |
| T2.2 | Follow-up resolution: detect references to previous turn ("that", "break it down", "instead") → standalone rewrite or thread prior SQL | `app/llm/planner.py` |
| T2.3 | Correction loop: user correction + previous SQL → regenerate; show old→new diff (distinct from error-retry) | `app/llm/generate_sql.py` |
| T2.4 | Editable SQL + 👍/👎 + "why this KPI/table?"; captured corrections feed Phase 1 eval | `app/ui.py` |
| T2.5 | Context-window management: summarize older turns | new helper |

### Phase 3 — Hardening & operability (deferred)

| ID | Task |
|---|---|
| T3.1 | Validator + enforce_limit pytest suite; wire eval into CI |
| T3.2 | Observability: latency, retrieval hits, retry rate, error classes, KPI-match confidence |
| T3.3 | Least-privilege DB role; redact/cap rows sent to the explainer (PII) |
| T3.4 | Perf: embedding cache, load schema docs once, fix empty-result cache bug, bound cache |
| T3.5 | Explicit abstention/clarification path; auth before real-data deploy |
| T3.6 | Cleanup: delete dead `retriever_experimental.py`, lazy client init, align `ClaudeC/` gitignore |

**Status:** user approved all tasks. Executing Phase 1.0 → 1.1 → 1.2 → 1.3 in order.

## 2026-06-17: Phase 1.0 COMPLETE

| ID | Result |
|---|---|
| T0.1 | ✅ Added `section` (A–E) to all 62 KPIs, sourced from canonical_list. Verified canonical_list ↔ overview agree 100% (0 disagreements, full coverage) before applying. Distribution A17/B12/C22/D7/E4. `category` retained. |
| T0.2 | ✅ `kpi_catalog.py`: added `VALID_SECTIONS`, `section` to required fields + enum check. Validates 62. |
| T0.3 | ✅ `generate_kpi_docs.py`: groups by `section` field (removed `CATEGORY_TO_SECTION` guess). |
| T0.4 | ✅ Regenerated inventory. `total_token_revenue`→A, `issuer_revenue`→C. Inventory vs overview mismatches: **0**. Planner eval 11/11. |
| T0.5 | ✅ Rewrote `kpi_catalog_spec.md`: removed tiers/tier-boost/"28"; added `section`, `value_basis`, `multi_table_rationale`, cluster + specificity resolution, 8 validation rules, snapshot (62; A17/B12/C22/D7/E4). |
| T0.6 | ✅ Reworded overview header: hand-maintained companion (not auto-generated); points to the generated inventory for the mechanical view. |

Verification: changed modules compile; catalog validates with `section` enforced on all 62; generator idempotent; planner eval 11/11. Temp scripts removed. Next: Phase 1.1 (SQL-correctness eval harness).

## 2026-06-17: Phase 1.1 + 1.2 + 1.3 COMPLETE (SQL correctness 56→62/62)

### T1.1 — Eval harness built

`app/eval/run_sql_correctness_eval.py`. Cases generated FROM the catalog (one representative question per active KPI). Runs the real pipeline (plan → match → generate_sql) against a full-schema context (isolates KPI→SQL correctness from retrieval). Semantic assertions, core vs secondary:
- core: `required_tables` present; completed-status filter applied correctly (catches the UPPERCASE `'COMPLETED'` zero-rows trap); aggregation pattern matches `sql_recipe.pattern`.
- secondary: required_joins column refs; date bucketing when the question implies a grain.
- CLI: `--limit/--kpi/--section/--offline/--json`. Needs project venv (`codex14-venv`, has openai/chromadb); added `load_dotenv()` so the import-time `OpenAI()` in `embeddings.py` gets the key; silences `generate_sql` debug prints via `redirect_stdout`.

### T1.2 — Baseline + failure analysis

Baseline: **56/62 core pass, 0 errors.** The 6 failures classified by reading the generated SQL:

| KPI | Verdict | Root cause | Fix |
|---|---|---|---|
| `id_verification_pass_rate` | correct SQL | assertion false-positive: matched substring "completed" in `completed_at` | assertion: require `status`+`completed` together |
| `supply_remaining` | correct SQL | catalog: pattern mislabeled `sum_grouped` (it's a per-row expression) | pattern → `raw_sql` |
| `amount_raised_vs_target` | correct SQL | catalog: `issuers` over-specified in required_tables | drop decorative `issuers` (+ dangling join/cols) |
| `platform_fee_revenue` | shortcut `SUM*0.2` | **directiveness gap: `raw_sql` recipe never injected** | T1.3a |
| `country_distribution` | users-only | example question said "of users" (too narrow) | broaden example question |
| `average_revenue_per_token` | correct (transactions rollup) | recipe not forced | T1.3a + assertion accepts SUM/COUNT avg |

### T1.3 — Directive KPI→SQL bridge (the high-value fix)

Key finding: `KpiMatchDecision.to_prompt_block()` **never surfaced `sql_recipe.raw_sql`**, so for all 19 raw_sql KPIs the LLM never saw the authoritative query. Rewrote `to_prompt_block()` (`app/llm/kpi_matcher.py`):
- frames the block as "authoritative — follow this recipe exactly";
- surfaces `value_basis` ("do not substitute a different revenue scale") — T1.3b;
- injects `raw_sql` as an `exact_sql_template` when present; otherwise the numerator/denominator/group_by;
- changed "default_filters" → "MUST apply these filters".

### Iteration + final result

After T1.3a the failure set shifted (raw_sql injection fixed platform_fee_revenue; directive recipe surfaced more decorative-table mismatches). Applied the principle **required_tables = tables needed to COMPUTE the value, not display labels** — removed decorative `issuers` from `token_leaderboard_most_traded`, `average_revenue_per_issuer`, `top_issuer_revenue_share`; broadened `country_distribution`'s example question; assertion accepts `SUM()/COUNT()` as a valid average.

**Final: SQL-correctness 62/62 core, 0 errors. Joins secondary 10/19, time_grain 9/9.** Routing eval 11/11, catalog validates, inventory regenerated, all modules compile.

Notes: LLM at temperature=0 has minor run-to-run variance; the three core checks are structural and robust. Catalog edits this phase: `supply_remaining`, `amount_raised_vs_target`, `token_leaderboard_most_traded`, `average_revenue_per_issuer`, `top_issuer_revenue_share`, `country_distribution`.

**Deferred (still Phase 1):** ~~T1.4 Part F Neon verification~~ (DONE below); T1.5 paraphrase-robustness set.

## 2026-06-17: T1.4 Part F — Neon verification COMPLETE (7/7 PASS)

Connected read-only to Neon via `DATABASE_URL` (`.env`; host ep-small-moon-…us-west-2.aws.neon.tech, db `neondb`, tables in `public` schema) using the `codex14-venv`. The app's `query_runner` defaults to localhost, so Part F used a direct read-only psycopg2 connection (`sslmode=require`, `statement_timeout=30s`). All read-only; temp script removed after.

| Check | Result |
|---|---|
| F1 status-case trap | ✅ `'COMPLETED'`=0; `lower(status)='completed'`=81,844 |
| F2 issuer net ratio | ✅ exactly **0.8000** (issuer_daily_revenue ÷ completed tx) |
| F3 tokens.total_revenue == summed completed tx/token | ✅ **0 mismatches** |
| F4 current_supply_minted all 0 | ✅ True (market cap must use `total_sold`) |
| F5 creator_profile empty | ✅ 0 rows (profile KPIs athlete-only) |
| F6 issuer status enum | ✅ {PASSED, PENDING, FAILED} |
| F7 tricky-recipe smoke | ✅ all return values |

F7 values (live Neon): total_token_revenue base = $2,599,624.82; market_cap = $3,116,829.54; active_traders = 2,000 distinct buyers; verification_pass_rate = 0.75; platform_fee_revenue (gtv − issuer_net) = $519,924.96.

Cross-check: platform_fee 519,924.96 = exactly 0.2 × gtv (2,599,624.82) → confirms platform_fee = gtv − issuer_net = 0.2×gtv, and issuer_net = 0.8×gtv. **Every data-reality assumption the catalog/eval relies on is verified against live data.** Only T1.5 (paraphrase robustness) remains in Phase 1.

## 2026-06-17: T1.5 Paraphrase robustness COMPLETE — key finding: lexical matching is fragile

Built a held-out paraphrase set (`app/eval/paraphrase_cases.json`, 62 questions, one per KPI) that deliberately avoids each KPI's name and alias phrases, plus a runner (`app/eval/run_paraphrase_eval.py`) that measures precision and includes a contamination check (no leaks). This isolates true matcher generalization vs the circular 62/62 routing eval (which uses the catalog's own example questions).

**Result: precision 3/62 = 4.8%** (vs 100% on tuned example questions). 51/62 fell below `MATCH_THRESHOLD` → schema fallback; 8 routed to the wrong KPI (spurious attractors like `top_tokens_share_of_volume` for any "share …" question, `failed_identity_checks` for "identity check …").

Verified real (not a harness bug): for "How much money did the platform bring in from all completed deals?", `total_token_revenue` scores 0.445 (top is `platform_fee_revenue` via the word "platform"), below the 0.58 threshold. The question tokens (money, deals, bring, platform) share zero tokens with the KPI's vocabulary (revenue, gtv, sales, token). Lexical token-overlap cannot bridge synonyms: revenue↔income/money, transactions↔deals, tokens↔coins, issuers↔creators.

**Conclusion / recommendation:** the catalog and SQL-correctness work are solid, but KPI *comprehension* is only robust when users speak the canonical vocabulary. Real-world precision sits between 4.8% (pure paraphrase) and 100% (canonical terms). This is decisive evidence for replacing/augmenting lexical KPI matching with an **embedding-shortlist** approach (semantic top-k candidates from the existing vector store → deterministic resolution among them via the current cluster/specificity rules). Do NOT overfit aliases to this set. Recommend promoting the embedding upgrade to the front of the chat/comprehension work.

**Phase 1 COMPLETE** (1.0 doc-truing, 1.1 eval harness, 1.2 baseline→fixes, 1.3 directive bridge, 1.4 Neon verification, 1.5 paraphrase measurement). New uncommitted files: `app/eval/paraphrase_cases.json`, `app/eval/run_paraphrase_eval.py`.

## 2026-06-17: Embedding-shortlist KPI matcher (Neon pgvector)

Decision: instead of local Chroma (ephemeral on Streamlit Cloud) or a new vendor, use **Neon + pgvector** — the managed DB already in use. Verified pgvector 0.8.0 available on Neon (PG 17.10). Drew the target flow in `docs/kpi_processing_flow_future.md` (copy of `kpi_processing_flow.md`).

Steps (user approved, step-by-step):
- **Step 1** — enabled `pgvector`; created `kpi_embeddings(kpi_id PK, section, model, embedding vector(1536), embed_text, content_hash, updated_at)` on Neon. Additive, idempotent.
- **Step 2** — wrote `app/rag/catalog/embed_kpis.py` (hash-gated build). Embed text per KPI = name + definition + aliases + example_questions, sourced entirely from `kpi_catalog.json`, embedded with `text-embedding-3-small`. Populated 62 rows.
- **Recall validation** (read-only, all 62 paraphrases): recall@1 73%, **@3 89%, @5 97%, @8 98%**, median rank 1. Only `buyer_to_seller_ratio` outside top-10. Confirms the shortlist foundation.
- **Step 3** — wired into `app/llm/kpi_matcher.py`: `match_kpi` now embeds the question, pulls top-8 from `kpi_embeddings`, runs `_resolve_candidates` (similarity gate `SIMILARITY_GATE=0.30`, specificity tiebreak, revenue-cluster default, leaderboard guardrail). Old lexical logic preserved as `_lexical_match_kpi` and used as graceful fallback when OpenAI/Neon unavailable (lazy imports → module still imports in bare envs). `KpiMatchDecision` unchanged.

Results:
- Paraphrase precision **4.8% → 72.6%** (45/62), 0 fallback, 17 wrong-KPI (semantic-sibling confusions, e.g. "creator take home" → `athlete_vs_creator_split`). Matches recall@1 — the resolver can't re-rank paraphrases without a literal-alias signal; ceiling is recall@5 = 97%.
- Canonical-vocab routing (planner eval) stays **11/11** via the embedding path, including the 3 schema-fallback negatives correctly rejected (gate works).
- Lexical fallback intact: planner eval 11/11 in bare system python (no openai).

Gotcha fixed: `run_paraphrase_eval.py` needed `load_dotenv()` or the embedding path silently fell back to lexical (still showed 4.8%).

Open: Step 4 gate tuning vs a negative set; optional LLM re-rank of the top-5 to close 73%→97%. New/changed files (uncommitted): `embed_kpis.py`, `kpi_matcher.py`, `run_paraphrase_eval.py`, `docs/kpi_processing_flow_future.md`; Neon `kpi_embeddings` table populated.

## 2026-06-17: Step 4 (gate tuning) + RAG review + doc updates

### Step 4 — similarity gate tuned

Added `app/eval/negative_cases.json` (12 non-KPI questions) and `--negatives` mode in `run_paraphrase_eval.py`. Measured top-1 similarity distributions:
- KPI paraphrases: min 0.311, median 0.478.
- Negatives: out-of-domain (weather/password/"list tables"/CEO) 0.15–0.26; **schema-exploration** ("sample the issuers table" 0.488, "what columns…" 0.447) **overlap the KPI band**.

Conclusion: `SIMILARITY_GATE = 0.30` is correct — keeps all 62 real KPI questions, rejects out-of-domain. But a numeric gate **cannot** separate schema-exploration from KPI questions (semantic overlap). Negatives abstention: **5/12** (the out-of-domain ones); the 7 leaks are all schema-exploration. The principled fix is an **LLM judge over the top-k with a NONE option** — which also closes the 73%→97% precision ceiling. Documented in code + flow docs. Gate value unchanged (already 0.30), now empirically justified.

### Two-RAG-paths question (user asked)

Separation is correct (schema grounding vs KPI routing are different jobs), but two issues: (1) the question is embedded twice (retriever + matcher), (2) two backends (Chroma schema_docs + Neon pgvector kpi_embeddings) → inconsistent persistence. Recommended convergence = **Phase 1.7**: embed once & share, migrate schema_docs to pgvector (one persistent backend), add the LLM judge.

### RAG module review + docs updated (pre-commit)

Reviewed all `app/rag/*` modules. Consistency confirmed: retriever, embed_kpis, and kpi_matcher all use `text-embedding-3-small` (clean for the future embed-once). `retriever_experimental.py` is dead/learning code (flag for Phase 3 cleanup). `generate_schema_docs_from_ddl.py` unaffected.

Docs updated:
- `docs/function_call_graph_rag.md` — added S6 (embed_kpis offline build) + S7 (kpi_matcher embedding retrieval, with lexical fallback); noted two backends + Phase 1.7.
- `docs/module_call_graph.md` — removed deleted `metric_resolver`; added `kpi_matcher → Neon pgvector kpi_embeddings` + OpenAI embeddings + `embed_kpis` build.
- `docs/kpi_catalog_spec.md` — matcher behavior rewritten to embedding-first (gate 0.30, top-8, resolver) with lexical fallback; added KPI Embedding Index section; refreshed eval-harness list.
- `docs/kpi_processing_flow.md` — now the current implemented (embedding) flow + known-limitation note.
- `docs/kpi_processing_flow_future.md` — re-scoped to Phase 1.7 (embed-once, single pgvector backend, LLM judge).

Verification: all modules compile; catalog validates (62); inventory in sync; planner eval 11/11 (lexical fallback path); paraphrase 72.6% (last embedding run); negatives 5/12 abstain. No temp files left. **Ready to commit Phase 1.6 + docs.**

Committed `51f4125` "Add embedding-shortlist KPI matcher (Neon pgvector)" and pushed. Remote also has `254cb33` "Update Readme.md" (added via GitHub web); pulled to sync. Branch `codex14-v3` = `origin/codex14-v3` = `254cb33`.

---

## RESUME HERE (new session)

**State:** Phase 1 + Phase 1.6 complete, committed & pushed. Branch `codex14-v3` at `254cb33`, clean.

**Done:** flat 62-KPI catalog with `section`/`value_basis`; SQL-correctness eval 62/62; Neon Part F 7/7; embedding-shortlist matcher (Neon pgvector) — paraphrase precision 4.8%→72.6%, canonical routing 11/11; all RAG docs updated.

**Next options (pick one):**
- **Phase 1.7** — converge the two RAG paths: embed the question once & share it; migrate `schema_docs` to Neon pgvector (one persistent backend, kills Streamlit cold-start re-embed); add an **LLM judge over the top-5** (closes 72.6%→~97% precision AND fixes schema-exploration abstention the gate can't). See `docs/kpi_processing_flow_future.md`.
- **Phase 2** — conversational chat (multi-turn state, follow-up resolution, correction loop, editable SQL + feedback). See the Phase Roadmap section above (T2.1–T2.5).
- **Phase 3** — deferred hardening (tests/CI, observability, security, perf).

**Environment gotchas (important):**
- Embedding/Neon/OpenAI paths need the project venv: `./codex14-venv/bin/python`. System python lacks `openai` → matcher silently uses the lexical fallback (this is the graceful fallback by design).
- Eval runners that hit embeddings (`run_sql_correctness_eval.py`, `run_paraphrase_eval.py`) call `load_dotenv()` and need `OPENAI_API_KEY` + `DATABASE_URL` in `.env`.
- Neon `kpi_embeddings` table is populated (62 rows). Re-run `./codex14-venv/bin/python app/rag/catalog/embed_kpis.py` after any catalog edit (hash-gated).
- After catalog edits also re-run `python app/rag/catalog/generate_kpi_docs.py` and `python app/eval/run_planner_kpi_eval.py`.

**Commands cheat-sheet:**
- SQL correctness: `./codex14-venv/bin/python app/eval/run_sql_correctness_eval.py`
- Paraphrase precision: `./codex14-venv/bin/python app/eval/run_paraphrase_eval.py` (`--negatives` for abstention)
- Routing: `python app/eval/run_planner_kpi_eval.py`

**Note:** `ClaudeC/` is NOT git-tracked (treated like `codex/`). It exists only on this machine — fine for resuming here; commit it if resuming elsewhere.
