import os
import json
import hashlib

from app.rag.embeddings import load_schema_docs, generate_embeddings, get_active_schema_path
from app.rag.vector_store import get_collection, store_embeddings, get_chroma_client, get_chroma_mode
from app.db.schema import get_active_local_schema

_STARTUP_LOGGED = False

# Check if environment is prod or local and 
def _state_file() -> str:
    db_env = os.getenv("DB_ENV", "local").lower()
    if db_env == "prod":
        return "chroma_db/schema_hash_prod.txt"
    return f"chroma_db/schema_hash_local_{get_active_local_schema()}.txt"


def _log_startup_once():
    global _STARTUP_LOGGED
    if _STARTUP_LOGGED:
        return
    db_env = os.getenv("DB_ENV", "local").lower()
    local_schema = get_active_local_schema()
    print(
        f"[startup] DB_ENV={db_env} | local_schema={local_schema} | schema_docs={get_active_schema_path()} | chroma_mode={get_chroma_mode()}"
    )
    _STARTUP_LOGGED = True


def compute_schema_hash(docs: list) -> str:
    """Create a hash of schema_docs.json to detect changes."""
    raw = json.dumps(docs, sort_keys=True).encode("utf-8")
    return hashlib.md5(raw).hexdigest()


def has_schema_changed(new_hash: str) -> bool:
    """Check if schema has changed since last ingest."""
    state_file = _state_file()
    if not os.path.exists(state_file):
        return True

    with open(state_file, "r") as f:
        old_hash = f.read().strip()

    return new_hash != old_hash


def save_hash(hash_value: str):
    """Persist latest schema hash."""
    state_file = _state_file()
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w") as f:
        f.write(hash_value)

# from app.rag.vector_store import get_chroma_client

# client = get_chroma_client()
# client.delete_collection(name="schema_docs")

# collection = client.get_or_create_collection(name="schema_docs")


def run_ingest():
    _log_startup_once()
    docs = load_schema_docs()
    schema_hash = compute_schema_hash(docs)

    if not has_schema_changed(schema_hash):
        print("No schema changes detected. Skipping ingestion.")
        return

    print("Schema changed. Rebuilding embeddings...")

    embedded_docs = generate_embeddings(docs)

    # Reset only the active environment's collection.
    client = get_chroma_client()
    collection_name = get_collection().name
    try:
        try:
            client.delete_collection(name=collection_name)
        except:
            pass
    except Exception:
        pass  # collection may not exist yet

    collection = get_collection()

    store_embeddings(collection, embedded_docs)

    save_hash(schema_hash)

    print("Ingestion complete.")