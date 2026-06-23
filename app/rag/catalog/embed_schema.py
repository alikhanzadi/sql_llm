"""Build the schema-docs embedding index in Neon (pgvector).

Embeds each schema **table doc** (the same formatted "Table: … Columns: …" block the
retriever returns as context) with OpenAI text-embedding-3-small and upserts into the
`schema_embeddings` table. Hash-gated: only docs whose embed_text changed are re-embedded.

This replaces the Chroma `schema_docs` collection (which was rebuilt on every Streamlit
cold start). The pgvector index is persistent, so restarts no longer re-embed.

Only the 13 table docs are embedded — that is the actual vector-search surface
(`retriever.py` filters vector hits to `Table:` docs). The legacy metric docs remain
lexically matched from the JSON and are intentionally not embedded here.

Usage:
  python app/rag/catalog/embed_schema.py --dry-run    # print embed_text, no OpenAI/DB
  python app/rag/catalog/embed_schema.py              # embed changed docs, upsert to Neon
  python app/rag/catalog/embed_schema.py --force      # re-embed all regardless of hash
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

from app.rag.embeddings import format_doc, load_schema_docs

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536

DDL = """
CREATE TABLE IF NOT EXISTS schema_embeddings (
    table_name   text PRIMARY KEY,
    model        text,
    embedding    vector(1536),
    embed_text   text,
    content_hash text,
    updated_at   timestamptz
);
"""


def _table_docs() -> list[dict]:
    """Return the schema docs that are tables (the vector-search surface)."""
    return [d for d in load_schema_docs() if d.get("type") != "metric" and d.get("table")]


def _hash(text: str) -> str:
    return hashlib.sha256((EMBED_MODEL + "\n" + text).encode("utf-8")).hexdigest()


def _vec_literal(vec: list[float]) -> str:
    """pgvector accepts a bracketed string cast to ::vector."""
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print embed_text, no OpenAI/DB")
    ap.add_argument("--force", action="store_true", help="re-embed all table docs")
    args = ap.parse_args(argv)

    records = []
    for d in _table_docs():
        text = format_doc(d).strip()
        records.append({
            "table_name": d["table"],
            "embed_text": text,
            "content_hash": _hash(text),
        })

    if args.dry_run:
        for r in records:
            preview = " ".join(r["embed_text"].split())[:120]
            print(f"{r['table_name']}\n    {preview}...")
        print(f"\n{len(records)} table docs would be embedded with {EMBED_MODEL} (dim {EMBED_DIM}).")
        return 0

    import psycopg2
    from openai import OpenAI

    from app.db.neon import get_neon_dsn

    dsn = get_neon_dsn()
    if not dsn:
        raise SystemExit("No Neon DSN: set DATABASE_URL or st.secrets[postgres_neon].")
    conn = psycopg2.connect(dsn, sslmode="require")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute(DDL)

    existing = {}
    cur.execute("SELECT table_name, content_hash FROM schema_embeddings;")
    for table_name, h in cur.fetchall():
        existing[table_name] = h

    to_embed = [r for r in records if args.force or existing.get(r["table_name"]) != r["content_hash"]]
    stale = set(existing) - {r["table_name"] for r in records}

    print(f"{len(records)} table docs; {len(to_embed)} need (re)embedding; "
          f"{len(stale)} stale rows to delete.")

    if to_embed:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.embeddings.create(model=EMBED_MODEL, input=[r["embed_text"] for r in to_embed])
        for r, item in zip(to_embed, resp.data):
            cur.execute(
                """
                INSERT INTO schema_embeddings (table_name, model, embedding, embed_text, content_hash, updated_at)
                VALUES (%s, %s, %s::vector, %s, %s, now())
                ON CONFLICT (table_name) DO UPDATE SET
                  model=EXCLUDED.model, embedding=EXCLUDED.embedding,
                  embed_text=EXCLUDED.embed_text, content_hash=EXCLUDED.content_hash, updated_at=now();
                """,
                (r["table_name"], EMBED_MODEL, _vec_literal(item.embedding),
                 r["embed_text"], r["content_hash"]),
            )

    for table_name in stale:
        cur.execute("DELETE FROM schema_embeddings WHERE table_name=%s;", (table_name,))

    cur.execute("SELECT count(*) FROM schema_embeddings;")
    print(f"Done. schema_embeddings now has {cur.fetchone()[0]} rows.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
