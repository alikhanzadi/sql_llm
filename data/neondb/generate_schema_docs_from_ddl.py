import argparse
import json
import re
from pathlib import Path


CREATE_TABLE_RE = re.compile(
    r"CREATE TABLE IF NOT EXISTS\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\);",
    re.DOTALL | re.IGNORECASE,
)

COLUMN_RE = re.compile(
    r'^\s*"?(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"?\s+'
    r"(?P<dtype>[A-Z]+(?:\([^)]+\))?(?:\[\])?)\s*(?P<rest>.*)$",
    re.IGNORECASE,
)

FK_RE = re.compile(
    r"FOREIGN KEY\s*\(([^)]+)\)\s*REFERENCES\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\(([^)]+)\)",
    re.IGNORECASE,
)

UNIQUE_RE = re.compile(r"UNIQUE\s*\(([^)]+)\)", re.IGNORECASE)
PK_RE = re.compile(r"PRIMARY KEY\s*\(([^)]+)\)", re.IGNORECASE)
ENUM_FROM_COMMENT_RE = re.compile(r"'([^']+)'")


def _clean_identifier(value: str) -> str:
    return value.strip().strip('"')


def _split_cols(value: str) -> list[str]:
    return [_clean_identifier(v) for v in value.split(",") if v.strip()]


def _extract_table_comment(sql: str, create_match_start: int) -> str:
    prefix = sql[:create_match_start]
    lines = prefix.splitlines()

    comment_lines: list[str] = []
    for line in reversed(lines):
        stripped = line.strip()
        if not stripped:
            if comment_lines:
                break
            continue
        if not stripped.startswith("--"):
            break
        text = stripped[2:].strip()
        if not text or set(text).issubset({"-", "="}):
            if comment_lines:
                break
            continue
        comment_lines.append(text)

    comment_lines.reverse()
    return " ".join(comment_lines).strip()


def _extract_comment_part(raw_line: str) -> str:
    if "--" not in raw_line:
        return ""
    return raw_line.split("--", 1)[1].strip()


def _normalize_pk_columns(pk_cols: list[str], column_names: set[str]) -> list[str]:
    normalized = []
    for col in pk_cols:
        if col in column_names:
            normalized.append(col)
        else:
            normalized.append(col)
    return normalized


def parse_sql_to_schema_docs(sql_text: str) -> list[dict]:
    docs: list[dict] = []

    for create_match in CREATE_TABLE_RE.finditer(sql_text):
        table_name = create_match.group(1)
        block = create_match.group(2)
        table_desc = _extract_table_comment(sql_text, create_match.start())

        columns: list[dict] = []
        primary_key: list[str] = []
        unique_keys: list[list[str]] = []
        foreign_keys: list[dict] = []

        for raw_line in block.splitlines():
            stripped = raw_line.strip().rstrip(",")
            if not stripped or stripped.startswith("--"):
                continue

            upper = stripped.upper()

            # Table-level constraints
            if upper.startswith(("CONSTRAINT", "PRIMARY KEY", "FOREIGN KEY", "UNIQUE")):
                pk_match = PK_RE.search(stripped)
                if pk_match:
                    primary_key = _split_cols(pk_match.group(1))

                unique_match = UNIQUE_RE.search(stripped)
                if unique_match:
                    unique_keys.append(_split_cols(unique_match.group(1)))

                fk_match = FK_RE.search(stripped)
                if fk_match:
                    foreign_keys.append(
                        {
                            "columns": _split_cols(fk_match.group(1)),
                            "references_table": _clean_identifier(fk_match.group(2)),
                            "references_columns": _split_cols(fk_match.group(3)),
                        }
                    )
                continue

            if stripped.startswith(")"):
                continue

            # Strip inline SQL comments before column parse, but keep comment metadata.
            sql_part = raw_line.split("--", 1)[0].strip().rstrip(",")
            col_match = COLUMN_RE.match(sql_part)
            if not col_match:
                continue

            col_name = _clean_identifier(col_match.group("name"))
            col_type = col_match.group("dtype").upper()
            rest = col_match.group("rest")
            col_comment = _extract_comment_part(raw_line)
            suggested_values = ENUM_FROM_COMMENT_RE.findall(col_comment)

            not_null = "NOT NULL" in rest.upper()
            is_inline_pk = "PRIMARY KEY" in rest.upper()
            is_inline_unique = "UNIQUE" in rest.upper()
            default_value = None
            default_match = re.search(r"DEFAULT\s+([^,\s]+(?:\s+\w+)*)", rest, re.IGNORECASE)
            if default_match:
                default_value = default_match.group(1).strip()

            col_doc = {
                "name": col_name,
                "type": col_type,
                "nullable": not (not_null or is_inline_pk),
            }
            if default_value:
                col_doc["default"] = default_value
            if col_comment:
                col_doc["comment"] = col_comment
            if suggested_values:
                col_doc["suggested_values"] = suggested_values

            columns.append(col_doc)

            if is_inline_pk and col_name not in primary_key:
                primary_key.append(col_name)
            if is_inline_unique:
                unique_keys.append([col_name])

        column_names = {c["name"] for c in columns}
        primary_key = _normalize_pk_columns(primary_key, column_names)

        time_columns = [
            c["name"]
            for c in columns
            if c["type"].startswith("TIMESTAMP") or c["type"].startswith("DATE")
        ]

        join_hints = []
        for fk in foreign_keys:
            pairs = zip(fk["columns"], fk["references_columns"])
            for local_col, ref_col in pairs:
                join_hints.append(
                    f"{table_name}.{local_col} = {fk['references_table']}.{ref_col}"
                )

        docs.append(
            {
                "type": "table",
                "table": table_name,
                "description": table_desc or f"Database table: {table_name}",
                "columns": columns,
                "primary_key": primary_key,
                "unique_keys": unique_keys,
                "foreign_keys": foreign_keys,
                "join_hints": join_hints,
                "time_columns": time_columns,
            }
        )

    return docs


def main():
    parser = argparse.ArgumentParser(description="Generate detailed schema docs from SQL DDL.")
    parser.add_argument(
        "--ddl",
        default="data/neondb/sql_create_tables/athl_raw_tables_postgres.sql",
        help="Path to source DDL SQL file.",
    )
    parser.add_argument(
        "--output",
        default="app/rag/catalog/schema_docs/neondb_schema_docs.json",
        help="Path to output schema docs JSON file.",
    )
    args = parser.parse_args()

    ddl_path = Path(args.ddl)
    output_path = Path(args.output)

    if not ddl_path.exists():
        raise FileNotFoundError(f"DDL file not found: {ddl_path}")

    docs = parse_sql_to_schema_docs(ddl_path.read_text())
    output_path.write_text(json.dumps(docs, indent=2))

    print(f"Wrote {len(docs)} table docs to {output_path}")


if __name__ == "__main__":
    main()
