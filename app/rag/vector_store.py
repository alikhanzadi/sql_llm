# app/rag/vector_store.py

import chromadb
# from chromadb.config import Settings

# get_collection() → client created
# store_embeddings() → upsert() → writes to disk → folder created

def get_chroma_client():
    """
    Create a persistent Chroma client.

    Why:
    - Ensures embeddings are saved to disk (./chroma_db)
    - Fixes issue where no folder was created
    """
    return chromadb.PersistentClient(path="./chroma_db")


def get_collection(name="schema_docs"):
    """
    Get or create a collection.

    Why:
    - Collections group related embeddings
    - 'schema_docs' will store your table metadata
    """
    client = get_chroma_client()
    return client.get_or_create_collection(name=name)


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