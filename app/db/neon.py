"""Shared Neon (pgvector) connection resolver for the embedding/retrieval layer.

Why this exists
---------------
The pgvector tables (`kpi_embeddings`, `schema_embeddings`) live in Neon and are read at
runtime by the KPI matcher and the schema retriever, and written by the offline embed
scripts. Those paths previously read `os.getenv("DATABASE_URL")` directly. On Streamlit
Cloud `DATABASE_URL` is NOT in `os.environ` (secrets land in `st.secrets`, and
`_apply_secrets_to_env()` only bridges `OPENAI_API_KEY`/`DB_ENV`), so the matcher silently
fell back to lexical matching (~4.8% paraphrase precision instead of ~73%).

This module resolves the Neon connection from a single place:
  1. `DATABASE_URL` env var (CLI / .env — points to Neon by convention), else
  2. a DSN constructed from `st.secrets["postgres_neon"]` (Streamlit Cloud).

So the pgvector layer works wherever query execution works. Note: the pgvector tables are
always in Neon regardless of `DB_ENV`; `LOCAL_DATABASE_URL`/`POSTGRES_*` are the local
query-execution DB and are intentionally not used here.
"""

from __future__ import annotations

import os
from typing import Optional
from urllib.parse import quote_plus

_conn = None


def get_neon_dsn() -> Optional[str]:
    """Resolve the Neon connection string, or None if no credentials are available."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    # Streamlit Cloud: build a DSN from the postgres_neon secrets section.
    try:
        import streamlit as st

        if "postgres_neon" in st.secrets:
            c = st.secrets["postgres_neon"]
            user = quote_plus(str(c["user"]))
            password = quote_plus(str(c["password"]))
            return f"postgresql://{user}:{password}@{c['host']}:{c['port']}/{c['database']}"
    except Exception:
        pass

    return None


def get_neon_conn_kwargs() -> Optional[dict]:
    """Return Neon connection components {host, port, database, user, password}, or None.

    Resolves from `DATABASE_URL` (parsed) or `st.secrets["postgres_neon"]`. Used by the
    query-execution client (`PostgresClient`) so cloud SQL execution works in CLI and on
    Streamlit Cloud — the same Neon the pgvector indexes live in.
    """
    url = os.getenv("DATABASE_URL")
    if url:
        from urllib.parse import unquote, urlparse

        u = urlparse(url)
        if u.hostname:
            return {
                "host": u.hostname,
                "port": u.port or 5432,
                "database": (u.path or "").lstrip("/") or None,
                "user": unquote(u.username) if u.username else None,
                "password": unquote(u.password) if u.password else None,
            }

    try:
        import streamlit as st

        if "postgres_neon" in st.secrets:
            c = st.secrets["postgres_neon"]
            return {
                "host": c["host"],
                "port": c["port"],
                "database": c["database"],
                "user": c["user"],
                "password": c["password"],
            }
    except Exception:
        pass

    return None


def get_neon_conn(statement_timeout_ms: int = 10000):
    """Return a cached read-only Neon connection for pgvector reads, or None if unavailable.

    Used by the runtime read paths (KPI matcher, schema retriever). Callers should treat a
    None return as "vector store unavailable" and fall back to lexical behavior.
    """
    global _conn
    if _conn is not None and not getattr(_conn, "closed", 1):
        return _conn

    dsn = get_neon_dsn()
    if not dsn:
        return None

    try:
        import psycopg2

        conn = psycopg2.connect(
            dsn, sslmode="require", options=f"-c statement_timeout={statement_timeout_ms}"
        )
        conn.set_session(readonly=True, autocommit=True)
        _conn = conn
        return _conn
    except Exception:
        _conn = None
        return None


def reset_neon_conn() -> None:
    """Drop the cached connection so the next call reconnects (after a broken-conn error)."""
    global _conn
    try:
        if _conn is not None:
            _conn.close()
    except Exception:
        pass
    _conn = None
