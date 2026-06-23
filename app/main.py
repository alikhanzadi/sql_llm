from dotenv import load_dotenv
load_dotenv()

from app.llm.generate_sql import build_sql_planning_context, generate_sql

from app.db.query_runner import PostgresClient
from app.db.validator import validate_sql, enforce_limit

from app.logger import log_query

from app.llm.explain_results import explain_results
from app.llm.generate_sql import fix_sql

from app.rag.context_service import get_retrieval_context
from app.rag.embeddings import embed_query_safe

from app.cache import (
    get_cached_sql,
    set_cached_sql,
    get_cached_result,
    set_cached_result
)


def main():

    user_input = input("Ask a question: ")

    # Embed the question once and share it across schema retrieval and KPI matching.
    query_embedding = embed_query_safe(user_input)

    # Retrieve context once and reuse across generate/fix/debug.
    retrieval_ctx = get_retrieval_context(user_input, query_embedding=query_embedding)
    context = retrieval_ctx.text
    planning_context = build_sql_planning_context(user_input, query_embedding=query_embedding)

    cache_key = user_input.strip().lower()
    sql = get_cached_sql(cache_key)

    if not sql:
        sql = generate_sql(user_input, context, planning_context=planning_context)
        set_cached_sql(cache_key, sql)
        sql_source = "generated"
    else:
        sql_source = "cached"

    print(f"\nSQL ({sql_source}):\n", sql)

    if validate_sql(sql):
        sql = enforce_limit(sql)

        with PostgresClient() as client:
            result = get_cached_result(sql)
            if not result:
                result = client.run_query(sql)
                set_cached_result(sql, result)
            else:
                print("\nUsing cached result\n")

            # retry once if failed
            if isinstance(result, dict) and "error" in result:
                print("\nRetrying with fixed SQL...\n")

                fixed_sql = fix_sql(
                    user_input,
                    sql,
                    result["error"],
                    context,
                    planning_context=planning_context,
                )
                print("Fixed SQL:\n", fixed_sql)

                if validate_sql(fixed_sql):
                    fixed_sql = enforce_limit(fixed_sql)
                    result = get_cached_result(fixed_sql)
                    if not result:
                        result = client.run_query(fixed_sql)
                        set_cached_result(fixed_sql, result)
                    else:
                        print("\nUsing cached result (fixed SQL)\n")

                    sql = fixed_sql
                else:
                    result = {"error": "Retry SQL did not pass the SELECT-only validator."}

    else:
        result = {"error": "Invalid or unsafe SQL"}

    log_query(user_input, sql, result)

    if isinstance(result, list):
        print("\nRows returned:", len(result))
        print("\nSQL:\n", sql)
        print("\nResult:\n", result)

        explanation = explain_results(user_input, sql, result)
        print("\nExplanation:\n", explanation)
    else:
        print("\nError:", result)


if __name__ == "__main__":
    main()
