#!/usr/bin/env python3
"""Rollback issuer_daily_revenue FK fix on local Postgres."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
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
    return {**os.environ, "PGPASSWORD": os.getenv("POSTGRES_PASSWORD", "admin")}


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


def reload_table(df: pd.DataFrame) -> None:
    buf = StringIO()
    df.to_csv(buf, index=False, header=True)
    _psql(f"ALTER TABLE {SCHEMA}.{TABLE} DROP CONSTRAINT IF EXISTS fk_rev_issuer;")
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
    backup_path = BACKUPS_DIR / BACKUP_NAME
    csv_path = TABLES_DIR / "issuer_daily_revenue.csv"
    if not backup_path.exists():
        raise FileNotFoundError(f"Missing backup: {backup_path}")

    shutil.copy2(backup_path, csv_path)
    print(f"Restored {csv_path} from {backup_path}")

    df = pd.read_csv(csv_path)
    reload_table(df)

    down_sql = (MIGRATIONS / "001_issuer_daily_revenue_fk_to_issuers.down.sql").read_text()
    _psql(down_sql)
    print("Rolled back FK to users(user_id)")


if __name__ == "__main__":
    main()
