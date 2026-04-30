# app/rag/embeddings.py

from openai import OpenAI
import json
import os
from typing import Optional

from app.local_schema import get_active_local_schema_docs_path

client = OpenAI()


def _resolve_schema_path(path: Optional[str] = None) -> str:
    if path:
        return path

    db_env = os.getenv("DB_ENV", "local").lower()
    if db_env == "prod":
        return "data/neondb_schema_docs.json"
    return get_active_local_schema_docs_path()


def get_active_schema_path(path: Optional[str] = None) -> str:
    return _resolve_schema_path(path)


def _normalize_docs(raw_docs: list) -> list:
    """
    Normalize schema docs from different source formats into:
    {
      "table": str,
      "description": str,
      "columns": [str]
    }
    """
    if not raw_docs:
        return []

    # Already in target docs format (plus optional metric docs).
    first = raw_docs[0]
    if isinstance(first, dict) and ("table" in first or first.get("type") == "metric"):
        return raw_docs

    # Flattened format (e.g. Neon export rows):
    # [{"table_name": "...", "column_name": "..."}, ...]
    if isinstance(first, dict) and "table_name" in first and "column_name" in first:
        grouped = {}
        for row in raw_docs:
            table = row.get("table_name")
            column = row.get("column_name")
            if not table or not column:
                continue
            grouped.setdefault(table, set()).add(column)

        return [
            {
                "table": table,
                "description": f"Database table: {table}",
                "columns": sorted(list(columns)),
            }
            for table, columns in grouped.items()
        ]

    return raw_docs


def load_schema_docs(path: Optional[str] = None):
    resolved_path = _resolve_schema_path(path)
    with open(resolved_path, "r") as f:
        raw_docs = json.load(f)
    return _normalize_docs(raw_docs)


def format_doc(doc):
    # NEW: handle metrics
    if doc.get("type") == "metric":
        return f"""
        Metric: {doc['name']}
        Definition: {doc['definition']}
        """

    # existing behavior (tables)
    return f"""
    Table: {doc['table']}
    Description: {doc['description']}
    Columns: {', '.join(doc['columns'])}
    """


def generate_embeddings(docs):
    texts = [format_doc(doc) for doc in docs]

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )

    embeddings = [e.embedding for e in response.data]

    return list(zip(texts, embeddings))

