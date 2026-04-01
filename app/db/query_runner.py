from dotenv import load_dotenv
load_dotenv()

import streamlit as st 

import psycopg2
from psycopg2.extras import RealDictCursor

class PostgresClient:
    def __init__(self):
        # This single block works for BOTH local and cloud 
        # because Streamlit handles the 'st.secrets' lookup automatically.
        creds = st.secrets["postgres"]
        
        # Check if we are on the cloud (Neon) or local (Docker)
        # Neon (cloud) usually requires SSL
        ssl_mode = "require" if "neon.tech" in creds["host"] else "disable"

        self.conn = psycopg2.connect(
            host=creds["host"],
            port=creds["port"],
            database=creds["database"],
            user=creds["user"],
            password=creds["password"],
            sslmode=ssl_mode
        )
    
    #     # 1. Try to get secrets from Streamlit Cloud
    #     if "postgres" in st.secrets:
    #         creds = st.secrets["postgres"]
    #         self.conn = psycopg2.connect(
    #             host=creds["host"],
    #             port=creds["port"],
    #             database=creds["database"],
    #             user=creds["user"],
    #             password=creds["password"],
    #             sslmode="require" # Cloud DBs usually need this
    #         )
    #     # 2. Fallback to your local Docker settings
    #     else:
    #         self.conn = psycopg2.connect(
    #             host="localhost",
    #             port=5432,
    #             dbname="analytics_db",
    #             user="admin",
    #             password="admin"
    #         )

    def run_query(self, query: str):
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            return {"error": str(e)}

if __name__ == "__main__":
    client = PostgresClient()
    
    query = """
    SELECT COUNT(*) as total_trades FROM trades;
    """
    
    result = client.run_query(query)
    print(result)
