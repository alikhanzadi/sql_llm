from dotenv import load_dotenv
load_dotenv()

from app.llm.generate_sql import generate_sql
from app.db.query_runner import PostgresClient
from app.db.validator import validate_sql, enforce_limit
from app.logger import log_query


def main():
    
    user_input = input("Ask a question: ")

    sql = generate_sql(user_input)
    print("\nGenerated SQL:\n", sql)

    if validate_sql(sql):
        sql = enforce_limit(sql)

        client = PostgresClient()
        result = client.run_query(sql)
    else:
        result = {"error": "Invalid or unsafe SQL"}

    log_query(user_input, sql, result)

    if isinstance(result, list):
        print("\nRows returned:", len(result))
        print("\nResult:\n", result)
    else:
        print("\nError:", result)


if __name__ == "__main__":
    main()