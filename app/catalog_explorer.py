"""Load and summarize schema, KPI, lineage, and local CSV catalog data."""

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DOCS_PATH = PROJECT_ROOT / "app" / "rag" / "catalog" / "schema_docs" / "v2_schema_docs.json"
KPI_CATALOG_PATH = PROJECT_ROOT / "app" / "rag" / "catalog" / "kpi_catalog.json"
LOCAL_TABLES_DIR = PROJECT_ROOT / "data" / "tables"


def load_catalog_docs(path: Path = SCHEMA_DOCS_PATH) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_tables() -> list[dict[str, Any]]:
    return [doc for doc in load_catalog_docs() if doc.get("type") == "table" and doc.get("table")]


def load_metric_docs() -> list[dict[str, Any]]:
    return [doc for doc in load_catalog_docs() if doc.get("type") == "metric"]


def load_kpi_catalog(path: Path = KPI_CATALOG_PATH) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_kpis() -> list[dict[str, Any]]:
    return load_kpi_catalog().get("kpis", [])


def table_by_name() -> dict[str, dict[str, Any]]:
    return {table["table"]: table for table in load_tables()}


def _csv_path_for_table(table_name: str) -> Path:
    return LOCAL_TABLES_DIR / f"{table_name}.csv"


def get_csv_profile(table_name: str) -> dict[str, Any]:
    path = _csv_path_for_table(table_name)
    if not path.exists():
        return {
            "table": table_name,
            "csv_available": False,
            "csv_path": "",
            "row_count": None,
            "csv_columns": [],
        }

    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            header = []
            row_count = 0
        else:
            row_count = sum(1 for _ in reader)

    return {
        "table": table_name,
        "csv_available": True,
        "csv_path": str(path.relative_to(PROJECT_ROOT)),
        "row_count": row_count,
        "csv_columns": header,
    }


def sample_csv_rows(table_name: str, limit: int = 25) -> list[dict[str, str]]:
    path = _csv_path_for_table(table_name)
    if not path.exists():
        return []

    rows = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for index, row in enumerate(reader):
            if index >= limit:
                break
            rows.append(dict(row))
    return rows


def build_table_summary() -> list[dict[str, Any]]:
    rows = []
    for table in load_tables():
        csv_profile = get_csv_profile(table["table"])
        rows.append(
            {
                "table": table["table"],
                "description": table.get("description", ""),
                "classification": table.get("taxonomy", {}).get("classification", ""),
                "columns": len(table.get("columns", [])),
                "primary_key": ", ".join(table.get("primary_key", [])),
                "foreign_keys": len(table.get("foreign_keys", [])),
                "time_columns": ", ".join(table.get("time_columns", [])),
                "csv_rows": csv_profile["row_count"],
                "csv_available": csv_profile["csv_available"],
            }
        )
    return rows


def build_column_details(table_name: str) -> list[dict[str, Any]]:
    table = table_by_name().get(table_name)
    if not table:
        return []

    primary_key = set(table.get("primary_key", []))
    fk_columns = {
        column
        for fk in table.get("foreign_keys", [])
        for column in fk.get("columns", [])
    }
    rows = []
    for column in table.get("columns", []):
        name = column.get("name", "")
        rows.append(
            {
                "column": name,
                "type": column.get("type", ""),
                "nullable": column.get("nullable", True),
                "default": column.get("default", ""),
                "role": "PK" if name in primary_key else "FK" if name in fk_columns else "",
                "description": column.get("comment", ""),
                "suggested_values": ", ".join(column.get("suggested_values", [])),
            }
        )
    return rows


def build_relationships() -> list[dict[str, str]]:
    relationships = []
    for table in load_tables():
        source = table["table"]
        for fk in table.get("foreign_keys", []):
            target = fk.get("references_table", "")
            relationships.append(
                {
                    "from_table": source,
                    "from_columns": ", ".join(fk.get("columns", [])),
                    "to_table": target,
                    "to_columns": ", ".join(fk.get("references_columns", [])),
                    "join": f"{source}.{', '.join(fk.get('columns', []))} = {target}.{', '.join(fk.get('references_columns', []))}",
                }
            )
    return relationships


def build_join_paths() -> dict[str, list[str]]:
    paths = defaultdict(list)
    for relationship in build_relationships():
        paths[relationship["from_table"]].append(relationship["join"])
        paths[relationship["to_table"]].append(relationship["join"])
    return dict(paths)


def build_metric_summary() -> list[dict[str, Any]]:
    rows = []
    for metric in load_metric_docs():
        rows.append(
            {
                "metric": metric.get("name", ""),
                "definition": metric.get("definition", ""),
                "formula": metric.get("formula", ""),
                "required_tables": ", ".join(metric.get("required_tables", [])),
                "required_columns": ", ".join(metric.get("required_columns", [])),
                "group_by": ", ".join(metric.get("group_by", [])),
            }
        )
    return rows


def build_kpi_summary() -> list[dict[str, Any]]:
    rows = []
    for kpi in load_kpis():
        rows.append(
            {
                "kpi_id": kpi.get("kpi_id", ""),
                "name": kpi.get("name", ""),
                "status": kpi.get("status", ""),
                "tier": kpi.get("tier", ""),
                "category": kpi.get("category", ""),
                "owner_team": kpi.get("owner_team", ""),
                "definition": kpi.get("business_definition", ""),
                "required_tables": ", ".join(kpi.get("required_tables", [])),
                "time_grains": ", ".join(kpi.get("time_grains", [])),
                "missing_dependencies": ", ".join(kpi.get("missing_dependencies", [])),
            }
        )
    return rows


def build_kpi_status_counts() -> dict[str, int]:
    return dict(Counter(kpi.get("status", "unknown") for kpi in load_kpis()))


def build_kpi_category_counts() -> dict[str, int]:
    return dict(Counter(kpi.get("category", "unknown") for kpi in load_kpis()))


def build_lineage_rows() -> list[dict[str, str]]:
    rows = []
    for relationship in build_relationships():
        rows.append(
            {
                "lineage_type": "foreign_key",
                "source": relationship["from_table"],
                "target": relationship["to_table"],
                "detail": relationship["join"],
            }
        )

    for metric in load_metric_docs():
        for table in metric.get("required_tables", []):
            rows.append(
                {
                    "lineage_type": "metric_dependency",
                    "source": table,
                    "target": metric.get("name", ""),
                    "detail": metric.get("formula", ""),
                }
            )

    for kpi in load_kpis():
        for table in kpi.get("required_tables", []):
            rows.append(
                {
                    "lineage_type": "kpi_dependency",
                    "source": table,
                    "target": kpi.get("name", ""),
                    "detail": kpi.get("business_definition", ""),
                }
            )
    return rows


def build_mermaid_erd() -> str:
    lines = ["erDiagram"]
    for table in load_tables():
        table_name = table["table"].upper()
        lines.append(f"    {table_name} {{")
        for column in table.get("columns", []):
            raw_type = column.get("type", "TEXT").replace(" ", "_").replace(",", "")
            name = column.get("name", "")
            key_marker = ""
            if name in table.get("primary_key", []):
                key_marker = " PK"
            lines.append(f"        {raw_type} {name}{key_marker}")
        lines.append("    }")

    for relationship in build_relationships():
        source = relationship["from_table"].upper()
        target = relationship["to_table"].upper()
        label = relationship["from_columns"].replace(",", "_")
        lines.append(f'    {target} ||--o{{ {source} : "{label}"')
    return "\n".join(lines)


def build_architecture_mermaid() -> str:
    return """flowchart LR
    User[User question] --> UI[Streamlit UI]
    UI --> Docs[Schema explorer and docs]
    UI --> RAG[RAG retrieval]
    RAG --> SchemaDocs[Schema and metric docs JSON]
    RAG --> Chroma[Chroma vector store]
    UI --> Planner[Planner and KPI matcher]
    Planner --> Catalog[KPI catalog]
    Planner --> SQL[SQL generation]
    SQL --> Validator[SELECT-only validator]
    Validator --> Postgres[(PostgreSQL / Neon)]
    Postgres --> Results[Results table]
    Results --> Viz[Charts and explanation]
    """
