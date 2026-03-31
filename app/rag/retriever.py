# app/rag/retriever.py

from openai import OpenAI
from app.rag.vector_store import get_collection, query_collection

client = OpenAI()


def retrieve_relevant_docs(question: str, top_k: int = 2):
    """
    Input: user question
    Output: list of relevant schema documents

    Steps:
    - Embed question
    - Query Chroma
    - Return matched documents
    """

    # Embed user question
    embedding = client.embeddings.create(
        model="text-embedding-3-small",
        input=question
    ).data[0].embedding

    # Query vector DB
    collection = get_collection()
    results = query_collection(collection, embedding, n_results=top_k)

    # Extract documents
    docs = results.get("documents", [[]])[0]

    return docs