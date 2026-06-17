from dataclasses import dataclass, field
import re
from typing import Optional

from app.rag.catalog.kpi_catalog import load_kpi_catalog


TOKEN_RE = re.compile(r"[a-z0-9_]+")
MATCH_THRESHOLD = 0.58
AMBIGUOUS_MARGIN = 0.03
LEADERBOARD_TERMS = {"top", "rank", "ranking", "highest", "lowest", "most", "least", "leaderboard"}

# Cluster default-resolution: when top-2 candidates are within AMBIGUOUS_MARGIN,
# resolve to the cluster default rather than falling back to schema-only.
REVENUE_CLUSTER = {"total_token_revenue", "issuer_revenue", "platform_fee_revenue"}
REVENUE_CLUSTER_DEFAULT = "total_token_revenue"


@dataclass
class KpiMatchDecision:
    """Structured outcome for KPI matching and downstream prompt routing."""

    matched: bool
    confidence: float
    reason: str
    kpi_id: Optional[str] = None
    status: Optional[str] = None
    missing_dependencies: list[str] = field(default_factory=list)
    kpi: Optional[dict] = None

    def to_prompt_block(self) -> str:
        """Return canonical KPI context for prompting only when match is active."""
        if not self.matched or not self.kpi:
            return ""
        if self.status != "active":
            return ""

        kpi = self.kpi
        recipe = kpi.get("sql_recipe", {})
        group_by = recipe.get("group_by")
        group_by_text = ", ".join(group_by) if isinstance(group_by, list) else (group_by or "none")

        lines = [
            "Canonical KPI Context (authoritative — follow this recipe exactly):",
            f"- kpi_id: {kpi.get('kpi_id', '')}",
            f"- name: {kpi.get('name', '')}",
            f"- definition: {kpi.get('business_definition', '')}",
            f"- required_tables: {', '.join(kpi.get('required_tables', [])) or 'none'}",
            f"- required_joins: {', '.join(kpi.get('required_joins', [])) or 'none'}",
            f"- MUST apply these filters: {', '.join(kpi.get('filters_defaults', [])) or 'none'}",
        ]

        # value_basis prevents gross/net/fee revenue confusion — always surface it.
        if kpi.get("value_basis"):
            lines.append(f"- value_basis: {kpi['value_basis']} (do not substitute a different revenue scale)")

        # raw_sql recipes are the exact intended query — present them as the template.
        raw_sql = recipe.get("raw_sql")
        if raw_sql:
            lines.append(f"- exact_sql_template (adapt aliases/filters as needed, keep the logic): {raw_sql}")
        else:
            lines.append(f"- recipe_pattern: {recipe.get('pattern', '')}")
            lines.append(f"- recipe_numerator: {recipe.get('numerator', '') or 'none'}")
            lines.append(f"- recipe_denominator: {recipe.get('denominator', '') or 'none'}")
            lines.append(f"- recipe_group_by: {group_by_text}")

        return "\n".join(lines)

    def blocked_message(self) -> str:
        """Build user-safe message for KPIs blocked by missing data dependencies."""
        deps = ", ".join(self.missing_dependencies) or "required source tables/events"
        return (
            f"KPI '{self.kpi_id}' is blocked_by_missing_data. "
            f"Missing dependencies: {deps}."
        )


def _norm(text: str) -> str:
    """Lowercase and normalize whitespace for deterministic string comparisons."""
    return " ".join(text.lower().split())


def _tokenize(text: str) -> set[str]:
    """Tokenize normalized text and lightly singularize plural nouns."""
    normalized = set()
    for token in TOKEN_RE.findall(_norm(text)):
        if len(token) > 3 and token.endswith("s"):
            token = token[:-1]
        normalized.add(token)
    return normalized


def _score_entry(question: str, q_tokens: set[str], kpi: dict, plan) -> float:
    """Score one KPI candidate against question text plus planner signals."""
    score = 0.0
    name = _norm(kpi.get("name", ""))
    aliases = [_norm(a) for a in kpi.get("aliases", [])]
    name_tokens = _tokenize(name)

    if name and name in question:
        score += 0.65
    for alias in aliases:
        if alias and alias in question:
            score += 0.55
            break

    overlap_count = len(q_tokens & name_tokens)
    if overlap_count >= 2:
        score += 0.45
    elif overlap_count == 1:
        score += 0.18

    candidate_tokens = _tokenize(" ".join([name] + aliases))
    if candidate_tokens:
        overlap = len(q_tokens & candidate_tokens) / len(candidate_tokens)
        score += overlap * 0.35

    examples = " ".join(kpi.get("example_questions", []))
    example_tokens = _tokenize(examples)
    if example_tokens:
        overlap_examples = len(q_tokens & example_tokens) / len(example_tokens)
        score += overlap_examples * 0.30

    time_grains = set(kpi.get("time_grains", []))
    if plan.time_grain in time_grains:
        score += 0.08

    recipe_pattern = str(kpi.get("sql_recipe", {}).get("pattern", ""))
    if plan.intent == "top_k" and "rank" in recipe_pattern:
        score += 0.08
    elif plan.intent in {"count", "sum", "avg_per_entity"} and any(
        word in recipe_pattern for word in {"count", "sum", "average", "ratio"}
    ):
        score += 0.05

    if plan.entities:
        entity_tokens = set(plan.entities)
        if q_tokens & entity_tokens:
            score += 0.04

    return min(score, 0.99)


def _longest_match_in_question(kpi: dict, question: str) -> int:
    """Return the character length of the longest name/alias substring found in question."""
    name = _norm(kpi.get("name", ""))
    aliases = [_norm(a) for a in kpi.get("aliases", [])]
    candidates = [name] + aliases
    return max((len(c) for c in candidates if c and c in question), default=0)


def _resolve_ambiguous(best: dict, second: Optional[dict], question: str = "") -> Optional[dict]:
    """
    When two candidates are within AMBIGUOUS_MARGIN, attempt deterministic resolution.

    Rules (in order):
    1. If both candidates are in the revenue cluster, return the cluster default.
    2. If the top-2 differ in value_basis, force the cluster default.
    3. Specificity tiebreak: prefer the candidate whose longest matching name/alias
       substring is longer. A 25-char exact match beats a 16-char one — more specific.
    4. Otherwise return None — fall back to schema-only.
    """
    if second is None:
        return None

    best_id = best.get("kpi_id", "")
    second_id = second.get("kpi_id", "")

    # Rule 1: both in revenue cluster → default
    if best_id in REVENUE_CLUSTER and second_id in REVENUE_CLUSTER:
        catalog = load_kpi_catalog()
        kpis_by_id = {k["kpi_id"]: k for k in catalog.get("kpis", [])}
        return kpis_by_id.get(REVENUE_CLUSTER_DEFAULT)

    # Rule 2: specificity tiebreak via longest exact substring match.
    # A 23-char exact match is far more specific than a 7-char one — use it first
    # so we don't over-apply the revenue cluster default to clearly-distinguished KPIs.
    if question:
        best_len = _longest_match_in_question(best, question)
        second_len = _longest_match_in_question(second, question)
        if best_len > second_len:
            return best
        if second_len > best_len:
            return second

    # Rule 3: value_basis mismatch in near-tie → force revenue cluster default.
    # Only reaches here when specificity cannot break the tie (equal-length matches).
    best_basis = best.get("value_basis")
    second_basis = second.get("value_basis")
    if best_basis and second_basis and best_basis != second_basis:
        catalog = load_kpi_catalog()
        kpis_by_id = {k["kpi_id"]: k for k in catalog.get("kpis", [])}
        return kpis_by_id.get(REVENUE_CLUSTER_DEFAULT)

    return None


def match_kpi(question: str, plan) -> KpiMatchDecision:
    """Match question to one canonical KPI using confidence and ambiguity guards."""
    normalized_question = _norm(question)
    q_tokens = _tokenize(normalized_question)
    catalog = load_kpi_catalog()
    kpis = catalog.get("kpis", [])

    ranked: list[tuple[float, dict]] = []
    for kpi in kpis:
        score = _score_entry(normalized_question, q_tokens, kpi, plan)
        ranked.append((score, kpi))

    ranked.sort(key=lambda x: x[0], reverse=True)
    best_score, best_kpi = ranked[0] if ranked else (0.0, None)
    second_score = ranked[1][0] if len(ranked) > 1 else 0.0

    if not best_kpi or best_score < MATCH_THRESHOLD:
        return KpiMatchDecision(
            matched=False,
            confidence=best_score,
            reason="No KPI match passed confidence threshold.",
        )

    # Guardrail: leaderboard KPIs should only match ranking-style questions.
    # Otherwise generic trading questions can inherit a narrow default window (e.g., 7d)
    # and return empty/null outputs on stale local datasets.
    if best_kpi.get("category") == "leaderboard":
        has_leaderboard_language = any(
            term in normalized_question for term in LEADERBOARD_TERMS
        )
        if not plan.requires_ranking and not has_leaderboard_language:
            return KpiMatchDecision(
                matched=False,
                confidence=best_score,
                reason="Leaderboard KPI requires ranking intent; using schema fallback.",
            )

    if (best_score - second_score) < AMBIGUOUS_MARGIN:
        # Collect ALL candidates within AMBIGUOUS_MARGIN of the best score.
        # The 0.99 cap collapses genuinely different-quality matches — use longest
        # exact substring match across all tied candidates to pick the most specific.
        within_margin = [k for s, k in ranked if best_score - s < AMBIGUOUS_MARGIN]
        lm_by_kpi = {k["kpi_id"]: _longest_match_in_question(k, normalized_question) for k in within_margin}
        max_lm = max(lm_by_kpi.values(), default=0)
        if max_lm > 0:
            top_by_lm = [k for k in within_margin if lm_by_kpi[k["kpi_id"]] == max_lm]
            if len(top_by_lm) == 1:
                winner = top_by_lm[0]
                return KpiMatchDecision(
                    matched=True,
                    confidence=best_score,
                    reason=f"Ambiguous match resolved by specificity (longest exact match) to '{winner['kpi_id']}'.",
                    kpi_id=winner.get("kpi_id"),
                    status=winner.get("status"),
                    missing_dependencies=winner.get("missing_dependencies", []),
                    kpi=winner,
                )

        second_kpi = ranked[1][1] if len(ranked) > 1 else None
        resolved = _resolve_ambiguous(best_kpi, second_kpi, normalized_question)
        if resolved is not None:
            return KpiMatchDecision(
                matched=True,
                confidence=best_score,
                reason=(
                    f"Ambiguous match resolved to cluster default '{resolved.get('kpi_id')}'. "
                    f"Also available: {best_kpi.get('kpi_id')}, {second_kpi.get('kpi_id') if second_kpi else ''}."
                ),
                kpi_id=resolved.get("kpi_id"),
                status=resolved.get("status"),
                missing_dependencies=resolved.get("missing_dependencies", []),
                kpi=resolved,
            )
        return KpiMatchDecision(
            matched=False,
            confidence=best_score,
            reason="KPI match ambiguous; using schema fallback.",
        )

    return KpiMatchDecision(
        matched=True,
        confidence=best_score,
        reason="Matched canonical KPI.",
        kpi_id=best_kpi.get("kpi_id"),
        status=best_kpi.get("status"),
        missing_dependencies=best_kpi.get("missing_dependencies", []),
        kpi=best_kpi,
    )
