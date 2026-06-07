#!/usr/bin/env python3
"""Apply issuer_daily_revenue fix to local Postgres (undoable via rollback_001_local.py)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS = Path(__file__).resolve().parent
TABLES_DIR = ROOT / "data" / "tables"
BACKUPS_DIR = MIGRATIONS / "backups"
SCHEMA = "athl_v2"
TABLE = "issuer_daily_revenue"
BACKUP_NAME = "issuer_daily_revenue.csv.pre_issuers_fk.bak"
CONTAINER = "ai_postgres"

load_dotenv(ROOT / ".env")


def _db_env() -> dict[str, str]:
    password = os.getenv("POSTGRES_PASSWORD", "admin")
    return {**os.environ, "PGPASSWORD": password}


def _psql(sql_text: str) -> None:
    db = os.getenv("POSTGRES_DB", "analytics_db")
    user = os.getenv("POSTGRES_USER", "admin")
    proc = subprocess.run(
        ["docker", "exec", "-i", CONTAINER, "psql", "-U", user, "-d", db, "-v", "ON_ERROR_STOP=1"],
        input=sql_text,
        capture_output=True,
        text=True,
        env=_db_env(),
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError("SQL failed")


def regenerate_issuer_daily_revenue_csv() -> pd.DataFrame:
    transactions_path = TABLES_DIR / "transactions.csv"
    issuers_path = TABLES_DIR / "issuers.csv"
    transactions_df = pd.read_csv(transactions_path)
    issuers_df = pd.read_csv(issuers_path)
    user_to_issuer = dict(zip(issuers_df["user_id"], issuers_df["issuer_id"]))

    df = (
        transactions_df.assign(issuer_id=lambda d: d["seller_id"].map(user_to_issuer))
        .groupby(["issuer_id", "timestamp"], as_index=False)
        .agg(total_amount_usdc=("total_amount_usdc", "sum"))
    )
    if df["issuer_id"].isna().any():
        raise ValueError("Some seller_id values could not map to issuer_id")

    df["total_amount_usdc"] = (0.8 * df["total_amount_usdc"]).round(6)
    return df.rename(columns={"timestamp": "date"})[["issuer_id", "date", "total_amount_usdc"]]


def backup_csv(csv_path: Path) -> None:
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUPS_DIR / BACKUP_NAME
    if csv_path.exists():
        shutil.copy2(csv_path, backup_path)
        print(f"Backed up {csv_path} -> {backup_path}")
    (BACKUPS_DIR / "001_applied_at.txt").write_text(datetime.now(timezone.utc).isoformat())


def reload_table(df: pd.DataFrame) -> None:
    buf = StringIO()
    df.to_csv(buf, index=False, header=True)
    buf.seek(0)

    _psql(f"TRUNCATE TABLE {SCHEMA}.{TABLE} RESTART IDENTITY CASCADE;")

    db = os.getenv("POSTGRES_DB", "analytics_db")
    user = os.getenv("POSTGRES_USER", "admin")
    copy_sql = (
        f"COPY {SCHEMA}.{TABLE} (issuer_id, date, total_amount_usdc) "
        "FROM STDIN WITH (FORMAT csv, HEADER true)"
    )
    proc = subprocess.run(
        ["docker", "exec", "-i", CONTAINER, "psql", "-U", user, "-d", db, "-v", "ON_ERROR_STOP=1", "-c", copy_sql],
        input=buf.getvalue(),
        capture_output=True,
        text=True,
        env=_db_env(),
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise RuntimeError("COPY failed")
    print(f"Reloaded {len(df)} rows into {SCHEMA}.{TABLE}")


def main() -> None:
    csv_path = TABLES_DIR / "issuer_daily_revenue.csv"
    backup_csv(csv_path)

    df = regenerate_issuer_daily_revenue_csv()
    df.to_csv(csv_path, index=False)
    print(f"Wrote corrected {csv_path} ({len(df)} rows)")

    _psql(f"ALTER TABLE {SCHEMA}.{TABLE} DROP CONSTRAINT IF EXISTS fk_rev_issuer;")
    reload_table(df)

    orphan_check = (
        f"SELECT COUNT(*) FROM {SCHEMA}.{TABLE} r "
        f"LEFT JOIN {SCHEMA}.issuers i ON i.issuer_id = r.issuer_id "
        "WHERE i.issuer_id IS NULL;"
    )
    proc = subprocess.run(
        ["docker", "exec", CONTAINER, "psql", "-U", os.getenv("POSTGRES_USER", "admin"),
         "-d", os.getenv("POSTGRES_DB", "analytics_db"), "-t", "-A", "-c", orphan_check],
        capture_output=True,
        text=True,
        env=_db_env(),
    )
    orphans = int(proc.stdout.strip() or "0")
    if orphans:
        raise RuntimeError(f"{orphans} rows do not match issuers.issuer_id")

    up_sql = (MIGRATIONS / "001_issuer_daily_revenue_fk_to_issuers.up.sql").read_text()
    _psql(up_sql)
    print("Applied FK migration (issuer_daily_revenue -> issuers.issuer_id)")
    print("Rollback: python data/local_athl_v2/migrations/rollback_001_local.py")


if __name__ == "__main__":
    main()
