import os

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def explain_results(question: str, sql: str, results: list) -> str:
    prompt = f"""
User Question:
{question}

SQL Query:
{sql}

Query Results:
{results}

Explain the results in plain English.
Be concise.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()