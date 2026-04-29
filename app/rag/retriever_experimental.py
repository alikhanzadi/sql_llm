"""
Experimental retriever for learning/comparison.

This file is intentionally NOT wired into the app.
It gives you a stricter alternative to `retriever.py` so you can compare behavior.
"""

import re
from dotenv import load_dotenv
from openai import OpenAI

from app.rag.vector_store import get_collection, query_collection
from app.rag.embeddings import load_schema_docs, format_doc

load_dotenv()
client = OpenAI()


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "done", "each", "for",
    "from", "how", "in", "is", "many", "month", "of", "on", "per", "the",
    "to", "what", "when", "where", "which", "with"
}


def _tokens(text: str) -> set:
    words = re.findall(r"[a-z0-9_]+", text.lower())
    return {w for w in words if w and w not in STOPWORDS and len(w) > 1}


def _parse_table_name(table_doc: str) -> str:
    match = re.search(r"Table:\s*([a-zA-Z0-9_]+)", table_doc)
    return match.group(1).lower() if match else ""


def _parse_columns(table_doc: str) -> set:
    match = re.search(r"Columns:\s*(.+)", table_doc)
    if not match:
        return set()
    cols = [c.strip().lower() for c in match.group(1).split(",")]
    return {c for c in cols if c}


def _score_table_doc(table_doc: str, query_tokens: set) -> int:
    """Simple token-overlap scoring to reduce noisy table matches."""
    table_name = _parse_table_name(table_doc)
    columns = _parse_columns(table_doc)

    score = 0
    if table_name in query_tokens:
        score += 3

    score += len(columns.intersection(query_tokens))
    score += len(_tokens(table_doc).intersection(query_tokens))
    return score


def retrieve_relevant_docs_experimental(question: str, top_k: int = 6, max_tables: int = 2):
    """
    Alternative retrieval strategy:
    1) deterministic metric matching
    2) vector search for candidate tables
    3) token-overlap re-ranking
    4) keep only top N scored tables (less context noise)
    """
    q_lower = question.lower()
    q_tokens = _tokens(question)

    # 1) Deterministic metric retrieval
    raw_docs = load_schema_docs()
    metric_docs = []
    for doc in raw_docs:
        if doc.get("type") == "metric" and doc["name"].lower() in q_lower:
            metric_docs.append(format_doc(doc))

    # 2) Vector candidates
    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    ).data[0].embedding

    collection = get_collection()
    results = query_collection(collection, embedding, n_results=top_k)
    candidates = results.get("documents", [[]])[0]
    table_docs = [d for d in candidates if "Table:" in d]

    # 3) Re-rank and trim
    scored = []
    for table_doc in table_docs:
        score = _score_table_doc(table_doc, q_tokens)
        scored.append((score, table_doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    best_tables = [doc for score, doc in scored if score > 0][:max_tables]

    # fallback: if everything scored 0, keep the top vector result only
    if not best_tables and table_docs:
        best_tables = table_docs[:1]

    return metric_docs + best_tables
