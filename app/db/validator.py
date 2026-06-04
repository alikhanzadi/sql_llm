# app/db/validator.py
from __future__ import annotations

import sqlparse
from sqlparse import tokens as T
from sqlparse.sql import Parenthesis, Statement


_ALLOWED_FIRST_KEYWORDS = {"SELECT", "WITH"}
_FORBIDDEN_KEYWORDS = {
    "ALTER",
    "ANALYZE",
    "CALL",
    "COMMENT",
    "COMMIT",
    "COPY",
    "CREATE",
    "DELETE",
    "DO",
    "DROP",
    "EXEC",
    "EXECUTE",
    "GRANT",
    "INSERT",
    "LOCK",
    "MERGE",
    "REFRESH",
    "REINDEX",
    "RESET",
    "REVOKE",
    "ROLLBACK",
    "SET",
    "TRUNCATE",
    "UPDATE",
    "VACUUM",
}
_BLOCKED_FUNCTIONS = {"pg_sleep"}


def _single_statement(sql: str) -> Statement | None:
    """Return the parsed statement only when SQL contains exactly one statement."""
    statements = [stmt for stmt in sqlparse.parse(sql) if str(stmt).strip()]
    if len(statements) != 1:
        return None
    return statements[0]


def _first_significant_token(statement: Statement):
    """Find the first non-whitespace, non-comment token in a parsed statement."""
    for token in statement.tokens:
        if not token.is_whitespace and token.ttype not in T.Comment:
            return token
    return None


def _token_keyword(token) -> str:
    """Normalize a token to uppercase text for keyword comparisons."""
    return str(token).strip().upper()


def _has_forbidden_tokens(statement: Statement) -> bool:
    """Detect write-oriented commands and blocked functions anywhere in the statement."""
    for token in statement.flatten():
        if token.is_whitespace or token.ttype in T.Comment:
            continue

        keyword = _token_keyword(token)
        if keyword in _FORBIDDEN_KEYWORDS:
            return True
        if token.ttype in T.Name and keyword.lower() in _BLOCKED_FUNCTIONS:
            return True

    return False


def _has_top_level_limit(statement: Statement) -> bool:
    """Return true when the outer query already has a LIMIT clause."""
    for token in statement.tokens:
        if token.is_whitespace or token.ttype in T.Comment:
            continue
        if isinstance(token, Parenthesis):
            continue
        if _token_keyword(token) == "LIMIT":
            return True
    return False


def validate_sql(sql: str) -> bool:
    """Allow one read-only SELECT/WITH statement and reject unsafe SQL shapes."""
    statement = _single_statement(sql)
    if statement is None:
        return False

    first = _first_significant_token(statement)
    if first is None or _token_keyword(first) not in _ALLOWED_FIRST_KEYWORDS:
        return False

    if _has_forbidden_tokens(statement):
        return False

    return True


def enforce_limit(sql: str, limit: int = 10) -> str:
    """Append a row limit only when the outer query does not already define one."""
    statement = _single_statement(sql)
    if statement is None or _has_top_level_limit(statement):
        return sql

    return sql.strip().rstrip(";") + f" LIMIT {limit};"
