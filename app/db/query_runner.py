import psycopg2
from psycopg2.extras import RealDictCursor


class PostgresClient:
    def __init__(self):
        self.conn = psycopg2.connect(
            host="localhost",
            port=5432,
            dbname="analytics_db",
            user="admin",
            password="admin"
        )

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
