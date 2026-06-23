from dotenv import load_dotenv
import os
load_dotenv()

import streamlit as st 

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import ThreadedConnectionPool
from app.db.schema import get_active_local_schema


_POOLS: dict[tuple[tuple[str, str], ...], ThreadedConnectionPool] = {}


def _pool_key(conn_kwargs: dict) -> tuple[tuple[str, str], ...]:
    """Create a stable key so equivalent connection settings share one pool."""
    return tuple(sorted((key, str(value)) for key, value in conn_kwargs.items()))


def _get_pool(conn_kwargs: dict) -> ThreadedConnectionPool:
    """Return the process-local PostgreSQL pool for the provided connection settings."""
    key = _pool_key(conn_kwargs)
    if key not in _POOLS:
        maxconn = int(os.getenv("POSTGRES_POOL_MAX", "5"))
        _POOLS[key] = ThreadedConnectionPool(1, maxconn, **conn_kwargs)
    return _POOLS[key]


class PostgresClient:
    def __init__(self):
        self.conn = None
        self._pool = None

        # Decide environment (local vs prod)
        self.db_env = os.getenv("DB_ENV", "local").lower()

        creds = None
        try:
            if self.db_env == "prod" and "postgres_neon" in st.secrets:
                creds = st.secrets["postgres_neon"]
            elif self.db_env != "prod" and "postgres_local" in st.secrets:
                creds = st.secrets["postgres_local"]
            elif "postgres_neon" in st.secrets:
                creds = st.secrets["postgres_neon"]
            else:
                creds = st.secrets["postgres_local"]
        except Exception:
            creds = None

        if creds is None:
            # No Streamlit secrets (CLI / scripts). Resolve from env by DB_ENV.
            if self.db_env == "prod":
                from app.db.neon import get_neon_conn_kwargs

                creds = get_neon_conn_kwargs()
                if creds is None:
                    raise RuntimeError(
                        "DB_ENV=prod but no Neon credentials found "
                        "(set DATABASE_URL or st.secrets['postgres_neon'])."
                    )
            else:
                creds = {
                    "host": os.getenv("POSTGRES_HOST"),
                    "port": os.getenv("POSTGRES_PORT"),
                    "database": os.getenv("POSTGRES_DB"),
                    "user": os.getenv("POSTGRES_USER"),
                    "password": os.getenv("POSTGRES_PASSWORD"),
                }
        # # 1. Get the credentials (wherever they are)
        # creds = st.secrets["postgres"]

        # SSL for Neon only
        ssl_mode = "require" if "neon.tech" in creds["host"] else "disable"

        conn_kwargs = {
            "host": creds["host"],
            "port": creds["port"],
            "database": creds["database"],
            "user": creds["user"],
            "password": creds["password"],
            "sslmode": ssl_mode,
        }

        options = [f"-c statement_timeout={int(os.getenv('POSTGRES_STATEMENT_TIMEOUT_MS', '15000'))}"]
        if self.db_env != "prod":
            # Set search_path at session startup for local runtime.
            options.append(f"-c search_path={get_active_local_schema()}")

        conn_kwargs["options"] = " ".join(options)

        # Reuse a small process-local pool and make each session read-only.
        self._pool = _get_pool(conn_kwargs)
        self.conn = self._pool.getconn()
        self.conn.set_session(readonly=True, autocommit=True)

    def __enter__(self):
        """Support `with PostgresClient()` so callers reliably return connections."""
        return self

    def run_query(self, query: str):
        """Execute a validated read-only query and return rows or a structured error."""
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            return {"error": str(e)}

    def close(self):
        """Return the active connection to the pool."""
        if self.conn is not None and self._pool is not None:
            self._pool.putconn(self.conn)
            self.conn = None

    def __exit__(self, exc_type, exc, tb):
        """Close pooled resources when leaving a context manager block."""
        self.close()
        return False

if __name__ == "__main__":
    query = """
    SELECT COUNT(*) as total_trades FROM trades;
    """

    with PostgresClient() as client:
        result = client.run_query(query)
    print(result)
