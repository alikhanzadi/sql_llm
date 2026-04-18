import os
from openai import OpenAI
from dotenv import load_dotenv

# Mostly Day 5

# Day 15: Why this is removed: keyword-based filtering is removed and replaced with semantic retrieval (RAG)
# from app.schema import get_schema # Day 15 - commented out
from .prompts import SYSTEM_PROMPT

from app.rag.retriever import retrieve_relevant_docs
from app.rag.context_builder import build_context

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYNONYMS = {
    "users": ["customers", "clients"],
    "trades": ["transactions"]
}

# def format_schema(schema: dict) -> str: # Day 15 - commented out
#     text = ""
#     for table, cols in schema.items():
#         text += f"\nTable: {table}\n"
#         for col in cols:
#             text += f"- {col}\n"
#     return text

def clean_sql(response_text: str) -> str:
    return (
        response_text
        .replace("```sql", "")
        .replace("```", "")
        .strip()
    )

def matches(term: str, text: str) -> bool:
    return (
        term in text or
        term.rstrip("s") in text or
        (term + "s") in text
    )

# def filter_schema(schema: dict, question: str) -> dict: # DAY 5 # Day 9 --> commented out
#     question = question.lower()
#     filtered = {}

#     for table, cols in schema.items():
#         table_name = table.lower()

#         # include synonyms
#         synonyms = SYNONYMS.get(table_name, [])
#         all_terms = [table_name] + synonyms

#         # table_match = any(str(term) in question for term in all_terms) #this was before we used matches to resolve prular vs singluar
#         table_match = any(matches(term, question) for term in all_terms)

#         col_matches = [
#             col for col in cols if col.lower() in question
#         ]

#         if table_match or col_matches:
#             filtered[table] = cols

#     print("TERMS:", all_terms)
#     print("MATCHED TABLE:", table if table_match else None)

    # fallback if nothing matched
    # return filtered if filtered else schema

# def filter_schema(schema: dict, question: str) -> dict: #Day 9 # Day 15 - commented out
#     question = question.lower()
#     table_scores = {}

#     for table, cols in schema.items():
#         table_name = table.lower()

#         # include synonyms
#         synonyms = SYNONYMS.get(table_name, [])
#         all_terms = [table_name] + synonyms
#         score = 0

#         # Table name match
#         if any(matches(term, question) for term in all_terms):
#             score += 3

#         # Column matches
#         for col in cols:
#             col_clean = col.lower().replace("_", " ")
#             if matches(col_clean,question):
#             # col.lower() in question:
#                 print(col)
#                 score += 1

#         # store score if relevant
#         if score > 0:
#             table_scores[table] = score

#     # sort tables by score
#     sorted_tables = sorted(
#         table_scores.items(),
#         key=lambda x: x[1],
#         reverse=True
#     )

#     # keep top N tables (important)
#     TOP_K = 3
#     selected_tables = [t[0] for t in sorted_tables[:TOP_K]]

#     filtered = {t: schema[t] for t in selected_tables}

#     print("TABLE SCORES:", table_scores)
#     print("SELECTED TABLES:", selected_tables)

#     return filtered if filtered else schema

# def generate_sql(user_query: str) -> str: # Day 5 | # Day 15 - commented out
#     schema = get_schema()
#     filtered_schema = filter_schema(schema, user_query)
#     schema_text = format_schema(filtered_schema)

#     prompt = f"""
#     Database Schema:
#     {schema_text}

#     User Question:
#     {user_query}
#     """

#     response = client.chat.completions.create(
#         model="gpt-4o-mini",
#         messages=[
#             {"role": "system", "content": SYSTEM_PROMPT},
#             {"role": "user", "content": prompt}
#         ],
#         temperature=0
#     )

#     raw_sql = response.choices[0].message.content
#     cleaned_sql = clean_sql(raw_sql)
    
#     print("\n--- FILTERED SCHEMA ---")
#     print(schema_text)
#     print("--------------\n")

#     return cleaned_sql

def generate_sql(user_query: str) -> str:
    # Step 1: Retrieve relevant schema docs
    docs = retrieve_relevant_docs(user_query)

    # Step 2: Build clean context
    context = build_context(docs)

    # Step 3: Construct prompt
    prompt = f"""
    {context}

    User Question:
    {user_query}
    """

    # Step 4: Call LLM
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