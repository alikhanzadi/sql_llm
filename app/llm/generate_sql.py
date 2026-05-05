import os
from openai import OpenAI
from dotenv import load_dotenv

from .prompts import SYSTEM_PROMPT

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
    # Step 1: Construct prompt from already-retrieved context
    prompt = f"""
    {context}

    User Question:
    {user_query}
    """

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
    prompt = f"""
The following SQL query failed.

Relevant Database Schema:
{context}

User Question:
{user_query}

SQL:
{sql}

Error:
{error}

Fix the SQL query.
Return ONLY corrected SQL.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return clean_sql(response.choices[0].message.content)