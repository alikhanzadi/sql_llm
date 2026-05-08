import csv
import os
from io import StringIO
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql

# This is a local database bootstrap/load script for your athl_v2 schema:


load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
DDL_PATH = ROOT / "data" / "neondb" / "sql_create_tables" / "athl_raw_tables_postgres.sql"
CSV_DIR = ROOT / "data" / "neondb" / "tables"

SCHEMA_NAME = "athl_v2"

TABLE_FILE_MAP = {
    "users": "users.csv",
    "issuers": "issuers.csv",
    "athlete_profile": "athletes.csv",
    "creator_profile": None,
    "identity_verification": "identity_verification.csv",
    "social_verification": "social_verification.csv",
    "social_media_auth_fail": None,
    "issuer_post_signup": "issuer_post_signup.csv",
    "waitlist": None,
    "issuer_preferences": "issuer_preferences.csv",
    "tokens": "tokens.csv",
    "transactions": "transactions.csv",
    "payments": None,
    "user_token_wallet": "user_token_wallet.csv",
    "user_wallet": "user_wallet.csv",
    "issuer_daily_revenue": None,
}


def _connect():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        database=os.getenv("POSTGRES_DB", "analytics_db"),
        user=os.getenv("POSTGRES_USER", "admin"),
        password=os.getenv("POSTGRES_PASSWORD", "admin"),
        sslmode="disable",
    )


def _create_schema_and_tables(conn):
    ddl_sql = DDL_PATH.read_text()

    with conn.cursor() as cur:
        cur.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(SCHEMA_NAME)))
        cur.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(SCHEMA_NAME)))
        cur.execute(ddl_sql)
    conn.commit()


def _truncate_tables(conn):
    with conn.cursor() as cur:
        for table_name in TABLE_FILE_MAP.keys():
            cur.execute(
                sql.SQL("TRUNCATE TABLE {}.{} RESTART IDENTITY CASCADE").format(
                    sql.Identifier(SCHEMA_NAME), sql.Identifier(table_name)
                )
            )
    conn.commit()


def _copy_csv_to_table(conn, table_name: str, csv_path: Path):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            (SCHEMA_NAME, table_name),
        )
        table_columns = {row[0] for row in cur.fetchall()}

    with csv_path.open("r", newline="") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError(f"CSV has no header: {csv_path}")
        selected_columns = [c for c in reader.fieldnames if c in table_columns]
        if not selected_columns:
            raise ValueError(f"No compatible columns for {table_name} in {csv_path.name}")

        buf = StringIO()
        writer = csv.DictWriter(buf, fieldnames=selected_columns)
        writer.writeheader()
        for row in reader:
            writer.writerow({col: row.get(col) for col in selected_columns})
        buf.seek(0)

    copy_stmt = sql.SQL(
        "COPY {}.{} ({}) FROM STDIN WITH (FORMAT csv, HEADER true)"
    ).format(
        sql.Identifier(SCHEMA_NAME),
        sql.Identifier(table_name),
        sql.SQL(", ").join(sql.Identifier(col.strip()) for col in selected_columns),
    )

    with conn.cursor() as cur:
        cur.copy_expert(copy_stmt, buf)
    conn.commit()


def main():
    if not DDL_PATH.exists():
        raise FileNotFoundError(f"DDL file not found: {DDL_PATH}")
    if not CSV_DIR.exists():
        raise FileNotFoundError(f"CSV folder not found: {CSV_DIR}")

    conn = _connect()
    try:
        print(f"Creating/loading schema: {SCHEMA_NAME}")
        _create_schema_and_tables(conn)
        _truncate_tables(conn)

        for table_name, csv_name in TABLE_FILE_MAP.items():
            if not csv_name:
                continue
            csv_path = CSV_DIR / csv_name
            if not csv_path.exists():
                print(f"Skipping {table_name}: missing file {csv_name}")
                continue
            _copy_csv_to_table(conn, table_name, csv_path)
            print(f"Loaded {table_name} from {csv_name}")

        print("Done. Local v2 schema is ready.")
        print("Local runtime schema is fixed to athl_v2.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
