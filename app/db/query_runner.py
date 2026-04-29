from dotenv import load_dotenv
import os
load_dotenv()

import streamlit as st 

import psycopg2
from psycopg2.extras import RealDictCursor

class PostgresClient:
    def __init__(self):

        # Decide environment (local vs prod)
        db_env = os.getenv("DB_ENV", "local").lower()

        try:
            if db_env == "prod" and "postgres_neon" in st.secrets:
                creds = st.secrets["postgres_neon"]
            elif db_env != "prod" and "postgres_local" in st.secrets:
                creds = st.secrets["postgres_local"]
            elif "postgres_neon" in st.secrets:
                creds = st.secrets["postgres_neon"]
            else:
                creds = st.secrets["postgres_local"]
        except Exception:
            # fallback for local CLI runs
            creds = {
                "host": os.getenv("POSTGRES_HOST"),
                "port": os.getenv("POSTGRES_PORT"),
                "database": os.getenv("POSTGRES_DB"),
                "user": os.getenv("POSTGRES_USER"),
                "password": os.getenv("POSTGRES_PASSWORD"),
            }
        # # 1. Get the credentials (wherever they are)
        # creds = st.secrets["postgres"]

        # SSL for Neon only
        ssl_mode = "require" if "neon.tech" in creds["host"] else "disable"

        # 3. Connect using the dynamically chosen SSL mode
        self.conn = psycopg2.connect(
            host=creds["host"],
            port=creds["port"],
            database=creds["database"],
            user=creds["user"],
            password=creds["password"],
            sslmode=ssl_mode
        )        

    def run_query(self, query: str):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            self.conn.rollback()
            return {"error": str(e)}

if __name__ == "__main__":
    client = PostgresClient()
    
    query = """
    SELECT COUNT(*) as total_trades FROM trades;
    """
    
    result = client.run_query(query)
    print(result)
