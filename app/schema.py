# app/schema.py

from app.db.query_runner import PostgresClient


def get_schema():
    client = PostgresClient()
    conn = client.conn
    cursor = conn.cursor()

    query = """
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """

    cursor.execute(query)
    rows = cursor.fetchall()

    schema = {}

    for table, column in rows:
        schema.setdefault(table, []).append(column)

    # for table, column in rows:
    #     if table not in schema:
    #         schema[table] = []
    #     schema[table].append(column)

    cursor.close()
    conn.close()

    return schema
