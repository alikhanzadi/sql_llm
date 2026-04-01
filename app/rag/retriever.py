# app/rag/retriever.py
from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from app.rag.vector_store import get_collection, query_collection

client = OpenAI()


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

    metric_docs = []
    for doc in raw_docs:
        if doc.get("type") == "metric":
            if doc["name"].lower() in question.lower():
                metric_docs.append(format_doc(doc))

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
        if any(word in t.lower() for word in question.lower().split()):
            filtered_tables.append(t)

    if not filtered_tables:
        filtered_tables = table_docs

    # -------------------------
    # 4. Final ordering
    # -------------------------
    return metric_docs + filtered_tables