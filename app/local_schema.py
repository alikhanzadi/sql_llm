"""
Single local schema switch.

Default is the new extended schema. If you want to temporarily use the
legacy local schema, change ACTIVE_LOCAL_SCHEMA to "public".
"""

ACTIVE_LOCAL_SCHEMA = "athl_v2"  # change to "public" when needed


def get_active_local_schema() -> str:
    return ACTIVE_LOCAL_SCHEMA


def get_active_local_schema_docs_path() -> str:
    if get_active_local_schema() == "public":
        return "data/local/schema_docs.json"
    return "data/neondb_schema_docs.json"
