import os
from openai import OpenAI
from dotenv import load_dotenv

from .planner import plan_query
from .prompts import SYSTEM_PROMPT, compose_fix_user_prompt, compose_sql_user_prompt

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def generate_sql(user_query: str, context: str) -> str:
    # Step 1: Build deterministic intent plan and prompt.
    plan = plan_query(user_query)
    prompt = compose_sql_user_prompt(
        user_query=user_query,
        context=context,
        plan_block=plan.to_prompt_block(),
    )

    # Step 2: Call LLM
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
    prompt = compose_fix_user_prompt(
        user_query=user_query,
        sql=sql,
        error=error,
        context=context,
        plan_block=plan.to_prompt_block(),
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return clean_sql(response.choices[0].message.content)