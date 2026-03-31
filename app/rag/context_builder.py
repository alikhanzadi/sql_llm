
# app/rag/context_builder.py

def build_context(docs: list) -> str:
    """
    Input: retrieved documents
    Output: formatted schema context for LLM

    Why:
    - LLM performs better with clean structured text
    - Avoid passing raw JSON or messy strings
    """

    context = "Relevant Database Schema:\n"

    for doc in docs:
        context += f"{doc.strip()}\n\n"

    return context.strip()