# app/rag/retriever.py
from dotenv import load_dotenv
load_dotenv()

import re

from openai import OpenAI
from app.rag.vector_store import get_collection, query_collection

client = OpenAI()


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


# def retrieve_relevant_docs(question: str, top_k: int = 4): #cosine similarity of text
#     """
#     Input: user question
#     Output: list of relevant schema documents

#     Steps:
#     - Embed question
#     - Query Chroma
#     - Return matched documents
#     """

#     # Embed user question
#     embedding = client.embeddings.create(
#         model="text-embedding-3-small",
#         input=question
#     ).data[0].embedding

#     # Query vector DB
#     collection = get_collection()
#     results = query_collection(collection, embedding, n_results=top_k)
    

#     # Extract documents
#     docs = results.get("documents", [[]])[0]
#     # 🔴 NEW: prioritize metrics if present
#     metrics = [d for d in docs if "Metric:" in d]
#     tables = [d for d in docs if "Table:" in d]

#     # return metrics first, then tables
#     return metrics + tables

def retrieve_relevant_docs(question: str, top_k: int = 4):
    """
    Improved retrieval:
    - Always try to match metrics first (deterministic)
    - Then use vector search for tables
    """

    # -------------------------
    # 1. Load all docs (for metrics)
    # -------------------------
    from app.rag.embeddings import load_schema_docs, format_doc

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
    # 2. Vector search (tables)
    # -------------------------
    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    ).data[0].embedding

    collection = get_collection()
    results = query_collection(collection, embedding, n_results=top_k)

    docs = results.get("documents", [[]])[0]

    table_docs = [d for d in docs if "Table:" in d]

    # -------------------------
    # 3. Remove weak matches
    # -------------------------
    filtered_tables = []
    for t in table_docs:
        if question_tokens & _tokens(t):
            filtered_tables.append(t)

    if not filtered_tables:
        filtered_tables = table_docs

    # -------------------------
    # 4. Final ordering
    # -------------------------
    return _dedupe_docs(metric_docs + metric_table_docs + filtered_tables)
