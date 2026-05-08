import os
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

def clean_sql(response_text: str) -> str:
    return (
        response_text
        .replace("```sql", "")
        .replace("```", "")
        .strip()
    )


def _get_client():
    global _client
    if _client is not None:
        return _client
    if OpenAI is None:
        raise ModuleNotFoundError(
            "openai package is not installed. Install dependencies to run SQL generation."
        )
    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

def generate_sql(user_query: str, context: str) -> str:
    # Step 1: Build deterministic intent plan and prompt.
    plan = plan_query(user_query)
    kpi_decision = match_kpi(user_query, plan)
    print(
        "[KPI-MATCH]",
        {
            "matched_kpi_id": kpi_decision.kpi_id,
            "status": kpi_decision.status,
            "confidence": round(kpi_decision.confidence, 3),
            "reason": kpi_decision.reason,
        },
    )

    if kpi_decision.matched and kpi_decision.status == "blocked_by_missing_data":
        # Keep SQL-only contract while clearly surfacing unavailable KPI dependencies.
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

    # Step 2: Call LLM
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

# def fix_sql(user_query: str, sql: str, error: str) -> str:
def fix_sql(user_query: str, sql: str, error: str, context: str) -> str:
    plan = plan_query(user_query)
    kpi_decision = match_kpi(user_query, plan)
    print(
        "[KPI-MATCH-FIX]",
        {
            "matched_kpi_id": kpi_decision.kpi_id,
            "status": kpi_decision.status,
            "confidence": round(kpi_decision.confidence, 3),
            "reason": kpi_decision.reason,
        },
    )
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
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return clean_sql(response.choices[0].message.content)