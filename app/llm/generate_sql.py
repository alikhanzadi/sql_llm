import os
from openai import OpenAI
from dotenv import load_dotenv

from app.schema import get_schema
from .prompts import SYSTEM_PROMPT

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYNONYMS = {
    "users": ["customers", "clients"],
    "trades": ["transactions"]
}

def format_schema(schema: dict) -> str:
    text = ""
    for table, cols in schema.items():
        text += f"\nTable: {table}\n"
        for col in cols:
            text += f"- {col}\n"
    return text

def clean_sql(response_text: str) -> str:
    return (
        response_text
        .replace("```sql", "")
        .replace("```", "")
        .strip()
    )

def filter_schema(schema: dict, question: str) -> dict:
    question = question.lower()
    filtered = {}

    for table, cols in schema.items():
        table_name = table.lower()

        # include synonyms
        synonyms = SYNONYMS.get(table_name, [])
        all_terms = [table_name] + synonyms

        table_match = any(str(term) in question for term in all_terms)

        col_matches = [
            col for col in cols if col.lower() in question
        ]

        if table_match or col_matches:
            filtered[table] = cols

    # fallback if nothing matched
    return filtered if filtered else schema

def generate_sql(user_query: str) -> str:
    schema = get_schema()
    filtered_schema = filter_schema(schema, user_query)
    schema_text = format_schema(filtered_schema)

    filtered_schema = filter_schema(schema, user_query)
    schema_text = format_schema(filtered_schema)

    prompt = f"""
    Database Schema:
    {schema_text}

    User Question:
    {user_query}
    """

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
    
    print("\n--- FILTERED SCHEMA ---")
    print(schema_text)
    print("--------------\n")

    return cleaned_sql
