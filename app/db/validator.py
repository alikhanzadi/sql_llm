# app/db/validator.py

def validate_sql(sql: str) -> bool:
    sql_clean = sql.strip().lower()

    # Only allow SELECT
    if not sql_clean.startswith("select"):
        return False

    forbidden = ["insert", "update", "delete", "drop", "alter", "truncate"]

    for keyword in forbidden:
        if keyword in sql_clean:
            return False

    return True


def enforce_limit(sql: str, limit: int = 10) -> str:
    if "limit" not in sql.lower():
        sql = sql.rstrip(";") + f" LIMIT {limit};"
    return sql