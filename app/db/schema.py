ACTIVE_LOCAL_SCHEMA = "athl_v2"
ACTIVE_LOCAL_SCHEMA_DOCS_PATH = "app/rag/catalog/schema_docs/neondb_schema_docs.json"


def get_active_local_schema() -> str:
    return ACTIVE_LOCAL_SCHEMA


def get_active_local_schema_docs_path() -> str:
    return ACTIVE_LOCAL_SCHEMA_DOCS_PATH


def get_schema():
    from app.db.query_runner import PostgresClient

    client = PostgresClient()
    conn = client.conn
    cursor = conn.cursor()
    schema_name = get_active_local_schema()

    query = """
    SELECT table_name, column_name
    FROM information_schema.columns
    WHERE table_schema = %s
    ORDER BY table_name, ordinal_position;
    """

    cursor.execute(query, (schema_name,))
    rows = cursor.fetchall()

    schema = {}
    for table, column in rows:
        schema.setdefault(table, []).append(column)

    cursor.close()
    conn.close()

    return schema
