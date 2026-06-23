from dataclasses import dataclass

from app.rag.retriever import retrieve_relevant_docs


@dataclass
class RetrievalContext:
    docs: list
    text: str


def build_context(docs: list) -> str:
    """
    Format retrieved schema docs into a clean text block for prompting.
    """
    context = "Relevant Database Schema:\n"
    for doc in docs:
        context += f"{doc.strip()}\n\n"
    return context.strip()


def get_retrieval_context(question: str, query_embedding=None) -> RetrievalContext:
    """
    Single source of truth for schema retrieval context.

    Returns both raw retrieved docs and formatted context text so downstream
    steps can share one retrieval pass. A precomputed `query_embedding` (shared
    with KPI matching) avoids re-embedding the question.
    """
    docs = retrieve_relevant_docs(question, query_embedding=query_embedding)
    context_text = build_context(docs)
    return RetrievalContext(docs=docs, text=context_text)
