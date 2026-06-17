"""
Generate docs/kpi_inventory_grouped_by_section.md from kpi_catalog.json.

Run:  python app/rag/catalog/generate_kpi_docs.py

The generated file is the canonical human-readable inventory. Do not hand-edit it;
re-run this script if the catalog changes.
"""

import json
from pathlib import Path

CATALOG_PATH = Path("app/rag/catalog/kpi_catalog.json")
OUTPUT_PATH = Path("docs/kpi_inventory_grouped_by_section.md")

# North star executive sections, keyed by the catalog `section` field (A–E).
# Grouping is driven by the authoritative `section` on each KPI, not inferred
# from `category`, so this inventory always matches kpi_canonical_list / overview.
SECTION_LABELS = {
    "A": "A. Marketplace Health & Liquidity",
    "B": "B. User Growth & Engagement",
    "C": "C. Issuer Ecosystem Health",
    "D": "D. Financial & Business",
    "E": "E. Compliance, Trust & Risk",
}

SECTION_ORDER = ["A", "B", "C", "D", "E"]


def _status_badge(status: str) -> str:
    if status == "active":
        return "✓ active"
    if status == "blocked_by_missing_data":
        return "⚠ blocked"
    return status


def _format_kpi(kpi: dict) -> str:
    lines = [
        f"### `{kpi['kpi_id']}`",
        f"**{kpi['name']}**  {_status_badge(kpi['status'])}",
        "",
        kpi.get("business_definition", ""),
        "",
    ]

    if kpi.get("value_basis"):
        lines.append(f"- **value_basis:** `{kpi['value_basis']}`")

    tables = ", ".join(f"`{t}`" for t in kpi.get("required_tables", []))
    if tables:
        lines.append(f"- **tables:** {tables}")

    joins = kpi.get("required_joins", [])
    if joins:
        lines.append(f"- **joins:** {', '.join(f'`{j}`' for j in joins)}")

    filters = kpi.get("filters_defaults", [])
    if filters:
        lines.append(f"- **default filters:** `{'`, `'.join(filters)}`")

    dims = kpi.get("dimensions", [])
    if dims:
        lines.append(f"- **dimensions:** {', '.join(dims)}")

    recipe = kpi.get("sql_recipe", {})
    if recipe.get("pattern"):
        lines.append(f"- **recipe pattern:** `{recipe['pattern']}`")

    if kpi.get("missing_dependencies"):
        lines.append(f"- **missing:** {', '.join(kpi['missing_dependencies'])}")

    examples = kpi.get("example_questions", [])
    if examples:
        lines.append(f"- **example:** {examples[0]!r}")

    lines.append("")
    return "\n".join(lines)


def generate():
    with CATALOG_PATH.open() as f:
        catalog = json.load(f)

    kpis = catalog.get("kpis", [])
    version = catalog.get("version", "?")

    by_section: dict[str, list[dict]] = {s: [] for s in SECTION_ORDER}
    unmapped: list[dict] = []
    for kpi in kpis:
        section = kpi.get("section")
        if section in by_section:
            by_section[section].append(kpi)
        else:
            unmapped.append(kpi)

    lines = [
        f"# KPI Inventory — Grouped by Section",
        "",
        f"> Auto-generated from `{CATALOG_PATH}` (version {version}).  ",
        f"> Do not hand-edit — run `python app/rag/catalog/generate_kpi_docs.py` to regenerate.",
        "",
        f"**{len(kpis)} KPIs total** ({sum(1 for k in kpis if k['status'] == 'active')} active, "
        f"{sum(1 for k in kpis if k['status'] == 'blocked_by_missing_data')} blocked)",
        "",
        "---",
        "",
    ]

    for section in SECTION_ORDER:
        section_kpis = by_section[section]
        active = [k for k in section_kpis if k["status"] == "active"]
        blocked = [k for k in section_kpis if k["status"] != "active"]
        lines.append(f"## {SECTION_LABELS[section]}")
        lines.append("")
        lines.append(f"_{len(section_kpis)} KPIs — {len(active)} active, {len(blocked)} blocked_")
        lines.append("")
        for kpi in section_kpis:
            lines.append(_format_kpi(kpi))

    if unmapped:
        lines.append("## Unmapped (missing or invalid section)")
        lines.append("")
        for kpi in unmapped:
            lines.append(_format_kpi(kpi))

    output = "\n".join(lines)
    OUTPUT_PATH.write_text(output)
    print(f"Written: {OUTPUT_PATH} ({len(kpis)} KPIs, {len(lines)} lines)")


if __name__ == "__main__":
    generate()
