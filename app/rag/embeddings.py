# app/rag/embeddings.py

from openai import OpenAI
import json

client = OpenAI()


def load_schema_docs(path="data/schema_docs.json"):
    with open(path, "r") as f:
        return json.load(f)


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

