# app/rag/retriever.py
from dotenv import load_dotenv
load_dotenv()

import re

from app.db.neon import get_neon_conn, reset_neon_conn
from app.rag.embeddings import embed_query, format_doc, load_schema_docs


_STOPWORDS = {
    "a",
    "about",
    "all",
    "an",
    "and",
    "are",
    "as",
    "at",
    "by",
    "for",
    "from",
    "give",
    "how",
    "in",
    "is",
    "list",
    "many",
    "me",
    "of",
    "on",
    "or",
    "show",
    "the",
    "to",
    "total",
    "what",
    "which",
    "with",
}


def _tokens(text: str) -> set[str]:
    """Tokenize text while dropping low-signal question words."""
    return {
        token
        for token in re.findall(r"[a-z0-9_]+", text.lower())
        if len(token) > 2 and token not in _STOPWORDS
    }


def _dedupe_docs(docs: list[str]) -> list[str]:
    """Preserve retrieval order while removing duplicate formatted documents."""
    seen = set()
    unique_docs = []
    for doc in docs:
        key = " ".join(doc.split())
        if key in seen:
            continue
        seen.add(key)
        unique_docs.append(doc)
    return unique_docs


def _vec_literal(vec) -> str:
    """Format an embedding as a pgvector literal."""
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def _pgvector_table_docs(question: str, top_k: int, query_embedding=None):
    """Return top-k formatted table-doc blocks from Neon `schema_embeddings`.

    Returns None to signal the caller to fall back to lexical retrieval (offline / no key /
    Neon down). Semantic ranking already orders by relevance, so no token filter is applied.
    A precomputed `query_embedding` (shared with KPI matching) is used when provided.
    """
    try:
        embedding = query_embedding if query_embedding is not None else embed_query(question)
        conn = get_neon_conn()
        if conn is None:
            return None
        literal = _vec_literal(embedding)
        with conn.cursor() as cur:
            cur.execute(
                "SELECT embed_text FROM schema_embeddings "
                "ORDER BY embedding <=> %s::vector LIMIT %s;",
                (literal, top_k),
            )
            rows = cur.fetchall()
        return [r[0] for r in rows] or None
    except Exception:
        reset_neon_conn()
        return None


def _lexical_table_docs(question: str, raw_docs: list, top_k: int) -> list[str]:
    """Offline fallback: rank table docs by question-token overlap."""
    question_tokens = _tokens(question)
    scored = []
    for doc in raw_docs:
        if doc.get("type") == "metric" or not doc.get("table"):
            continue
        text = format_doc(doc)
        overlap = len(question_tokens & _tokens(text))
        scored.append((overlap, text))
    scored.sort(key=lambda x: x[0], reverse=True)
    with_overlap = [t for o, t in scored if o > 0]
    chosen = with_overlap if with_overlap else [t for _, t in scored]
    return chosen[:top_k]


def retrieve_relevant_docs(question: str, top_k: int = 4, query_embedding=None):
    """
    Retrieve schema context for a question:
    - Deterministically match metric docs (and pull in their required tables).
    - Semantically retrieve table docs from Neon pgvector (lexical fallback offline).

    A precomputed `query_embedding` (shared with KPI matching) avoids re-embedding.
    """

    # -------------------------
    # 1. Load all docs (for metrics) + table lookup
    # -------------------------
    raw_docs = load_schema_docs()
    question_tokens = _tokens(question)
    table_docs_by_name = {
        doc.get("table"): format_doc(doc)
        for doc in raw_docs
        if doc.get("table")
    }

    metric_docs = []
    metric_table_docs = []
    for doc in raw_docs:
        if doc.get("type") == "metric":
            metric_text = " ".join(
                [
                    doc.get("name", ""),
                    doc.get("definition", ""),
                    doc.get("formula", ""),
                ]
            )
            metric_tokens = _tokens(metric_text)
            if doc["name"].lower() in question.lower() or len(question_tokens & metric_tokens) >= 2:
                metric_docs.append(format_doc(doc))
                for table_name in doc.get("required_tables", []):
                    table_doc = table_docs_by_name.get(table_name)
                    if table_doc:
                        metric_table_docs.append(table_doc)

    # -------------------------
    # 2. Vector search (tables) via Neon pgvector, lexical fallback offline
    # -------------------------
    table_docs = _pgvector_table_docs(question, top_k, query_embedding=query_embedding)
    if table_docs is None:
        table_docs = _lexical_table_docs(question, raw_docs, top_k)

    # -------------------------
    # 3. Final ordering
    # -------------------------
    return _dedupe_docs(metric_docs + metric_table_docs + table_docs)
