import os
from dataclasses import dataclass
from typing import Any
from dotenv import load_dotenv

from .kpi_matcher import match_kpi
from .planner import plan_query
from .prompts import SYSTEM_PROMPT, compose_fix_user_prompt, compose_sql_user_prompt

try:
    from openai import OpenAI
except ModuleNotFoundError:  # pragma: no cover - env dependent
    OpenAI = None

load_dotenv()
_client = None

SYNONYMS = {
    "users": ["customers", "clients"],
    "trades": ["transactions"]
}


@dataclass
class SqlPlanningContext:
    """Reusable planner and KPI decisions for one user question."""
    plan: Any
    kpi_decision: Any


def clean_sql(response_text: str) -> str:
    """Remove markdown fences so model output can be handled as raw SQL."""
    return (
        response_text
        .replace("```sql", "")
        .replace("```", "")
        .strip()
    )


def _get_client():
    """Lazy-load the OpenAI client so imports work without installed dependencies."""
    global _client
    if _client is not None:
        return _client
    if OpenAI is None:
        raise ModuleNotFoundError(
            "openai package is not installed. Install dependencies to run SQL generation."
        )
    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def build_sql_planning_context(user_query: str) -> SqlPlanningContext:
    """Compute deterministic planning context once for generate and retry paths."""
    plan = plan_query(user_query)
    kpi_decision = match_kpi(user_query, plan)
    return SqlPlanningContext(
        plan=plan,
        kpi_decision=kpi_decision,
    )


def _log_planning_context(label: str, planning_context: SqlPlanningContext) -> None:
    """Print deterministic planner/KPI decisions for debugging."""
    kpi_decision = planning_context.kpi_decision
    print(
        f"[KPI-MATCH{label}]",
        {
            "matched_kpi_id": kpi_decision.kpi_id,
            "status": kpi_decision.status,
            "confidence": round(kpi_decision.confidence, 3),
            "reason": kpi_decision.reason,
        },
    )


def generate_sql(
    user_query: str,
    context: str,
    planning_context: SqlPlanningContext | None = None,
) -> str:
    """Generate first-pass SQL using retrieved context and deterministic planning."""
    planning_context = planning_context or build_sql_planning_context(user_query)
    plan = planning_context.plan
    kpi_decision = planning_context.kpi_decision
    _log_planning_context("", planning_context)

    if kpi_decision.matched and kpi_decision.status == "blocked_by_missing_data":
        blocked_text = kpi_decision.blocked_message().replace("'", "''")
        return (
            "SELECT "
            f"'{blocked_text}' AS blocked_kpi_message;"
        )

    prompt = compose_sql_user_prompt(
        user_query=user_query,
        context=context,
        plan_block=plan.to_prompt_block(),
        kpi_block=kpi_decision.to_prompt_block(),
    )

    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )

    raw_sql = response.choices[0].message.content
    cleaned_sql = clean_sql(raw_sql)

    print("\n--- RETRIEVED CONTEXT ---")
    print(context)
    print("------------------------\n")

    return cleaned_sql


def fix_sql(
    user_query: str,
    sql: str,
    error: str,
    context: str,
    planning_context: SqlPlanningContext | None = None,
) -> str:
    """Ask the model to repair failed SQL while reusing the original planning context."""
    planning_context = planning_context or build_sql_planning_context(user_query)
    plan = planning_context.plan
    kpi_decision = planning_context.kpi_decision
    _log_planning_context("-FIX", planning_context)
    prompt = compose_fix_user_prompt(
        user_query=user_query,
        sql=sql,
        error=error,
        context=context,
        plan_block=plan.to_prompt_block(),
        kpi_block=kpi_decision.to_prompt_block(),
    )

    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0
    )

    return clean_sql(response.choices[0].message.content)
