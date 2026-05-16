from dataclasses import dataclass, field
import re
from typing import Optional

from app.rag.catalog.kpi_catalog import load_kpi_catalog


TOKEN_RE = re.compile(r"[a-z0-9_]+")
MATCH_THRESHOLD = 0.58
AMBIGUOUS_MARGIN = 0.03
LEADERBOARD_TERMS = {"top", "rank", "ranking", "highest", "lowest", "most", "least", "leaderboard"}


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
        return (
            "Canonical KPI Context:\n"
            f"- kpi_id: {kpi.get('kpi_id', '')}\n"
            f"- name: {kpi.get('name', '')}\n"
            f"- definition: {kpi.get('business_definition', '')}\n"
            f"- required_tables: {', '.join(kpi.get('required_tables', [])) or 'none'}\n"
            f"- required_joins: {', '.join(kpi.get('required_joins', [])) or 'none'}\n"
            f"- default_filters: {', '.join(kpi.get('filters_defaults', [])) or 'none'}\n"
            f"- recipe_pattern: {recipe.get('pattern', '')}\n"
            f"- recipe_numerator: {recipe.get('numerator', '')}\n"
            f"- recipe_denominator: {recipe.get('denominator', '')}\n"
            f"- recipe_group_by: {', '.join(recipe.get('group_by', [])) if isinstance(recipe.get('group_by'), list) else recipe.get('group_by', '')}"
        )

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

    # Tiered canonical support: prefer tier_1 for planner routing.
    if kpi.get("tier") == "tier_1":
        score += 0.03
    elif kpi.get("tier") == "tier_2":
        score -= 0.02

    return min(score, 0.99)


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
