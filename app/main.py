
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI

from app.llm.generate_sql import generate_sql
from app.db.query_runner import PostgresClient
from app.db.validator import validate_sql, enforce_limit
from app.logger import log_query

from app.llm.explain_results import explain_results
from app.llm.generate_sql import fix_sql

from app.rag.embeddings import load_schema_docs, generate_embeddings
from app.rag.vector_store import get_collection, store_embeddings, query_collection

from app.cache import (
    get_cached_sql,
    set_cached_sql,
    get_cached_result,
    set_cached_result
)


def main():

    # =========================
    # 🔴 TEMP BLOCK — SETUP
    # =========================
    # WHY:
    # - Run ONCE to store schema embeddings in Chroma
    # - Required before retrieval works
    # - DELETE after first successful run

    docs = load_schema_docs()
    embedded_docs = generate_embeddings(docs)

    collection = get_collection()
    store_embeddings(collection, embedded_docs)

    print("Stored embeddings.")

    # =========================
    # 🔴 TEMP BLOCK — TEST RAG
    # =========================
    # WHY:
    # - Validate embeddings + vector DB + similarity search
    # - Ensures system retrieves correct tables
    # - DELETE after confirmed

    client = OpenAI()

    query = "average trades per user"

    q_embed = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    ).data[0].embedding

    results = query_collection(collection, q_embed)

    print("\nRAG TEST RESULTS:\n", results["documents"])

    # =========================
    # ✅ ACTUAL APP FLOW
    # =========================

    user_input = input("Ask a question: ")

    cache_key = user_input.strip().lower()
    sql = get_cached_sql(cache_key)

    if not sql:
        sql = generate_sql(user_input)
        set_cached_sql(cache_key, sql)
    else:
        print("\nUsing cached SQL\n")
        print("\nGenerated SQL:\n", sql)

    print("\nDEBUG SQL:\n", sql)

    if validate_sql(sql):
        sql = enforce_limit(sql)

        client = PostgresClient()

        result = get_cached_result(sql)
        if not result:
            result = client.run_query(sql)
            set_cached_result(sql, result)
        else:
            print("\nUsing cached result\n")

        # retry once if failed
        if isinstance(result, dict) and "error" in result:
            print("\nRetrying with fixed SQL...\n")

            fixed_sql = fix_sql(user_input, sql, result["error"])
            print("Fixed SQL:\n", fixed_sql)

            result = get_cached_result(fixed_sql)
            if not result:
                result = client.run_query(fixed_sql)
                set_cached_result(fixed_sql, result)
            else:
                print("\nUsing cached result (fixed SQL)\n")

            sql = fixed_sql

    else:
        result = {"error": "Invalid or unsafe SQL"}

    log_query(user_input, sql, result)

    if isinstance(result, list):
        print("\nRows returned:", len(result))
        print("\nSQL:\n")
        print("\nResult:\n", result)

        explanation = explain_results(user_input, sql, result)
        print("\nExplanation:\n", explanation)
    else:
        print("\nError:", result)


if __name__ == "__main__":
    main()