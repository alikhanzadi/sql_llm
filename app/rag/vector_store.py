# app/rag/vector_store.py

import chromadb
import os
from app.db.schema import get_active_local_schema


_CLIENT = None


def _collection_name(base_name: str) -> str:
    db_env = os.getenv("DB_ENV", "local").lower()
    if db_env == "prod":
        return f"{base_name}_{db_env}"
    return f"{base_name}_{db_env}_{get_active_local_schema()}"


def _is_ephemeral_env() -> bool:
    return os.getenv("DB_ENV", "local").lower() == "prod"


def get_chroma_mode() -> str:
    return "ephemeral" if _is_ephemeral_env() else "persistent"

# get_collection() → client created
# store_embeddings() → upsert() → writes to disk → folder created

def get_chroma_client():
    """
    Create Chroma client by environment.

    Why:
    - Local: keep embeddings on disk for faster iteration
    - Prod/cloud: keep in-memory because filesystem is ephemeral
    """
    global _CLIENT
    if _CLIENT is None:
        if _is_ephemeral_env():
            _CLIENT = chromadb.Client()
        else:
            _CLIENT = chromadb.PersistentClient(path="./chroma_db")
    return _CLIENT


def get_collection(name="schema_docs"):
    """
    Get or create a collection.

    Why:
    - Collections group related embeddings
    - 'schema_docs' will store your table metadata
    """
    client = get_chroma_client()
    env_name = _collection_name(name)
    # return client.get_or_create_collection(name=name)

    # try:
    #     collection = client.get_or_create_collection(name=name)
    # except:
    #     client = chromadb.Client()
    #     collection = client.create_collection(name=name)
    # return collection 

    try:
        return client.get_collection(name=env_name)
    except:
        return client.create_collection(name=env_name)


def store_embeddings(collection, embedded_docs):
    """
    Store embeddings in Chroma.

    Input:
    - embedded_docs = [(text, embedding_vector)]

    Why:
    - This makes your schema searchable via similarity
    """
    texts = [doc[0] for doc in embedded_docs]
    embeddings = [doc[1] for doc in embedded_docs]
    ids = [f"id_{i}" for i in range(len(texts))]

    collection.upsert(
        documents=texts,
        embeddings=embeddings,
        ids=ids
    )


def query_collection(collection, query_embedding, n_results=2):
    """
    Query similar documents.

    Why:
    - This is the core of RAG retrieval
    - Finds relevant tables based on meaning (not keywords)
    """
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )