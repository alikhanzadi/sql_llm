import os
import json
import hashlib

from app.rag.embeddings import load_schema_docs, generate_embeddings
from app.rag.vector_store import get_collection, store_embeddings

STATE_FILE = "chroma_db/schema_hash.txt"


def compute_schema_hash(docs: list) -> str:
    """Create a hash of schema_docs.json to detect changes."""
    raw = json.dumps(docs, sort_keys=True).encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def has_schema_changed(new_hash: str) -> bool:
    """Check if schema has changed since last ingest."""
    if not os.path.exists(STATE_FILE):
        return True

    with open(STATE_FILE, "r") as f:
        old_hash = f.read().strip()

    return new_hash != old_hash


def save_hash(hash_value: str):
    """Persist latest schema hash."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        f.write(hash_value)

from app.rag.vector_store import get_chroma_client

client = get_chroma_client()
client.delete_collection(name="schema_docs")

collection = client.get_or_create_collection(name="schema_docs")


def run_ingest():
    docs = load_schema_docs()
    schema_hash = compute_schema_hash(docs)

    if not has_schema_changed(schema_hash):
        print("No schema changes detected. Skipping ingestion.")
        return

    print("Schema changed. Rebuilding embeddings...")

    embedded_docs = generate_embeddings(docs)

    # ✅ FIX: reset collection properly
    client = get_chroma_client()
    try:
        client.delete_collection(name="schema_docs")
    except Exception:
        pass  # collection may not exist yet

    collection = get_collection()

    store_embeddings(collection, embedded_docs)

    save_hash(schema_hash)

    print("Ingestion complete.")