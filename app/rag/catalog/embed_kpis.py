"""
Build the KPI embedding index in Neon (pgvector).

Embeds each canonical KPI's text (name + definition + aliases + examples) with
OpenAI text-embedding-3-small and upserts into the `kpi_embeddings` table. Hash-gated:
only KPIs whose embed_text changed are re-embedded, so re-runs are cheap.

The embeddings are persistent in Postgres, so Streamlit Cloud restarts do not wipe
them (unlike a local Chroma store).

Usage:
  python app/rag/catalog/embed_kpis.py --dry-run    # print embed_text, no OpenAI/DB
  python app/rag/catalog/embed_kpis.py              # embed changed KPIs, upsert to Neon
  python app/rag/catalog/embed_kpis.py --force      # re-embed all regardless of hash
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

from app.rag.catalog.kpi_catalog import load_kpi_catalog

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536


def build_embed_text(kpi: dict) -> str:
    """Compose the semantic text for one KPI (what the matcher will search against)."""
    name = kpi.get("name", "")
    definition = kpi.get("business_definition", "")
    aliases = ", ".join(kpi.get("aliases", []))
    examples = " ".join(kpi.get("example_questions", []))
    parts = [f"{name}.", definition]
    if aliases:
        parts.append(f"Also known as: {aliases}.")
    if examples:
        parts.append(f"Example questions: {examples}")
    return " ".join(p for p in parts if p).strip()


def _hash(text: str) -> str:
    return hashlib.sha256((EMBED_MODEL + "\n" + text).encode("utf-8")).hexdigest()


def _vec_literal(vec: list[float]) -> str:
    """pgvector accepts a bracketed string cast to ::vector."""
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="print embed_text, no OpenAI/DB")
    ap.add_argument("--force", action="store_true", help="re-embed all KPIs")
    ap.add_argument("--limit", type=int, default=None, help="preview only N (with --dry-run)")
    args = ap.parse_args(argv)

    kpis = load_kpi_catalog()["kpis"]
    records = []
    for k in kpis:
        text = build_embed_text(k)
        records.append({
            "kpi_id": k["kpi_id"],
            "section": k.get("section"),
            "embed_text": text,
            "content_hash": _hash(text),
        })

    if args.dry_run:
        shown = records[: args.limit] if args.limit else records
        for r in shown:
            print(f"[{r['section']}] {r['kpi_id']}")
            print(f"    {r['embed_text']}")
        print(f"\n{len(records)} KPIs would be embedded with {EMBED_MODEL} (dim {EMBED_DIM}).")
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

    existing = {}
    cur.execute("SELECT kpi_id, content_hash FROM kpi_embeddings;")
    for kpi_id, h in cur.fetchall():
        existing[kpi_id] = h

    to_embed = [r for r in records if args.force or existing.get(r["kpi_id"]) != r["content_hash"]]
    stale = set(existing) - {r["kpi_id"] for r in records}

    print(f"{len(records)} KPIs in catalog; {len(to_embed)} need (re)embedding; "
          f"{len(stale)} stale rows to delete.")

    if to_embed:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        resp = client.embeddings.create(model=EMBED_MODEL, input=[r["embed_text"] for r in to_embed])
        for r, item in zip(to_embed, resp.data):
            cur.execute(
                """
                INSERT INTO kpi_embeddings (kpi_id, section, model, embedding, embed_text, content_hash, updated_at)
                VALUES (%s, %s, %s, %s::vector, %s, %s, now())
                ON CONFLICT (kpi_id) DO UPDATE SET
                  section=EXCLUDED.section, model=EXCLUDED.model, embedding=EXCLUDED.embedding,
                  embed_text=EXCLUDED.embed_text, content_hash=EXCLUDED.content_hash, updated_at=now();
                """,
                (r["kpi_id"], r["section"], EMBED_MODEL, _vec_literal(item.embedding),
                 r["embed_text"], r["content_hash"]),
            )

    for kpi_id in stale:
        cur.execute("DELETE FROM kpi_embeddings WHERE kpi_id=%s;", (kpi_id,))

    cur.execute("SELECT count(*) FROM kpi_embeddings;")
    print(f"Done. kpi_embeddings now has {cur.fetchone()[0]} rows.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
