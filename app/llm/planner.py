from dataclasses import dataclass, field
import re
from typing import Optional


INTENT_PRIORITY = [
    "top_k",
    "trend",
    "cohort",
    "avg_per_entity",
    "sum",
    "count",
    "join_lookup",
]


INTENT_KEYWORDS = {
    "count": {"count", "how many", "number of", "total number"},
    "sum": {"sum", "total", "revenue", "raised", "volume"},
    "avg_per_entity": {"average", "avg", "per ", "rate"},
    "top_k": {"top", "highest", "lowest", "rank", "leaderboard"},
    "trend": {"trend", "over time", "by day", "daily", "weekly", "monthly"},
    "cohort": {"cohort", "retention", "conversion", "funnel"},
}

TIME_GRAIN_KEYWORDS = {
    "day": {"day", "daily", "24h", "today"},
    "week": {"week", "weekly", "7d"},
    "month": {"month", "monthly", "30d"},
}

ENTITY_TERMS = {
    "user": {"user", "users", "customer", "customers", "fan", "fans"},
    "token": {"token", "tokens"},
    "issuer": {"issuer", "issuers", "athlete", "athletes"},
    "trade": {"trade", "trades", "transaction", "transactions"},
    "verification": {"verification", "verify", "kyc", "identity"},
    "onboarding": {"onboarding", "signup", "waitlist", "activation"},
    "wallet": {"wallet", "wallets", "balance", "balances"},
}


@dataclass
class QueryPlan:
    intent: str
    time_grain: str
    entities: list[str] = field(default_factory=list)
    top_k: Optional[int] = None
    requires_ranking: bool = False
    notes: list[str] = field(default_factory=list)

    def to_prompt_block(self) -> str:
        entities = ", ".join(self.entities) if self.entities else "unknown"
        top_k = str(self.top_k) if self.top_k is not None else "none"
        notes = "; ".join(self.notes) if self.notes else "none"
        ranking = "yes" if self.requires_ranking else "no"
        return (
            "Planned Query Intent:\n"
            f"- intent: {self.intent}\n"
            f"- time_grain: {self.time_grain}\n"
            f"- entities: {entities}\n"
            f"- top_k: {top_k}\n"
            f"- requires_ranking: {ranking}\n"
            f"- notes: {notes}"
        )


def _normalize(text: str) -> str:
    return " ".join(text.lower().strip().split())


def _extract_top_k(query: str) -> Optional[int]:
    number_match = re.search(r"\btop\s+(\d+)\b", query)
    if number_match:
        return int(number_match.group(1))
    if "top" in query:
        return 10
    return None


def _detect_time_grain(query: str) -> str:
    for grain, keywords in TIME_GRAIN_KEYWORDS.items():
        if any(keyword in query for keyword in keywords):
            return grain
    return "all_time"


def _detect_entities(query: str) -> list[str]:
    entities = []
    for entity, terms in ENTITY_TERMS.items():
        if any(term in query for term in terms):
            entities.append(entity)
    return entities


def _detect_intent(query: str) -> str:
    for intent in INTENT_PRIORITY:
        keywords = INTENT_KEYWORDS.get(intent, set())
        if any(keyword in query for keyword in keywords):
            return intent
    return "join_lookup"


def plan_query(question: str) -> QueryPlan:
    normalized = _normalize(question)
    intent = _detect_intent(normalized)
    top_k = _extract_top_k(normalized)
    time_grain = _detect_time_grain(normalized)
    entities = _detect_entities(normalized)
    requires_ranking = intent == "top_k" or top_k is not None

    notes: list[str] = []
    if intent == "avg_per_entity":
        notes.append("Use two-stage aggregation when averaging per entity.")
    if requires_ranking:
        notes.append("Use ORDER BY metric and ranking/window function when needed.")
    if time_grain != "all_time":
        notes.append("Use explicit date truncation based on requested time grain.")
    if not entities:
        notes.append("Infer primary entity from schema context before selecting tables.")

    return QueryPlan(
        intent=intent,
        time_grain=time_grain,
        entities=entities,
        top_k=top_k,
        requires_ranking=requires_ranking,
        notes=notes,
    )
