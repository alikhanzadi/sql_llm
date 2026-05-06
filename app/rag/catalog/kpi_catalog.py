import json
from pathlib import Path


VALID_STATUS = {"active", "draft", "blocked_by_missing_data"}
VALID_TIME_GRAINS = {"day", "week", "month", "all_time"}

REQUIRED_FIELDS = {
    "kpi_id",
    "name",
    "category",
    "status",
    "owner_team",
    "business_definition",
    "time_grains",
    "dimensions",
    "required_tables",
    "required_columns",
    "required_joins",
    "filters_defaults",
    "sql_recipe",
    "example_questions",
    "quality_notes",
    "source_refs",
    "missing_dependencies",
}


def _validate_entry(entry: dict):
    """Validate one KPI record so broken definitions fail fast."""
    
    missing = REQUIRED_FIELDS.difference(entry.keys())
    if missing:
        raise ValueError(f"KPI '{entry.get('kpi_id', '<unknown>')}' missing fields: {sorted(missing)}")

    if entry["status"] not in VALID_STATUS:
        raise ValueError(f"KPI '{entry['kpi_id']}' has invalid status: {entry['status']}")

    invalid_grains = [g for g in entry["time_grains"] if g not in VALID_TIME_GRAINS]
    if invalid_grains:
        raise ValueError(
            f"KPI '{entry['kpi_id']}' has invalid time grains: {invalid_grains}"
        )

    if entry["status"] == "active":
        if not entry["required_tables"]:
            raise ValueError(f"KPI '{entry['kpi_id']}' active but required_tables is empty")
        if not entry["required_columns"]:
            raise ValueError(f"KPI '{entry['kpi_id']}' active but required_columns is empty")
        if not entry["example_questions"]:
            raise ValueError(f"KPI '{entry['kpi_id']}' active but example_questions is empty")

    if entry["status"] == "blocked_by_missing_data" and not entry["missing_dependencies"]:
        raise ValueError(
            f"KPI '{entry['kpi_id']}' blocked_by_missing_data but missing_dependencies is empty"
        )


def validate_kpi_catalog(catalog: dict):
    """Validate the full KPI catalog contract and uniqueness constraints."""

    if "kpis" not in catalog or not isinstance(catalog["kpis"], list):
        raise ValueError("Catalog must include a 'kpis' list")

    seen_ids = set()
    for entry in catalog["kpis"]:
        _validate_entry(entry)
        kpi_id = entry["kpi_id"]
        if kpi_id in seen_ids:
            raise ValueError(f"Duplicate kpi_id found: {kpi_id}")
        seen_ids.add(kpi_id)


def load_kpi_catalog(path: str = "app/rag/catalog/kpi_catalog.json") -> dict:
    """Load catalog JSON from disk and validate before use."""
    catalog_path = Path(path)
    if not catalog_path.exists():
        raise FileNotFoundError(f"KPI catalog not found: {catalog_path}")

    with catalog_path.open("r") as f:
        catalog = json.load(f)

    validate_kpi_catalog(catalog)
    return catalog
