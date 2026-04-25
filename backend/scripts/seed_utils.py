"""Offline seed SQL helpers.

These helpers intentionally do not connect to Supabase/Postgres. They convert
reviewed JSON exports into SQL that can be inspected and applied separately.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

ColumnSpec = tuple[str, Any]


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("source", nargs="?", type=Path, help="JSON file containing an object or array of objects")
    parser.add_argument("--out", type=Path, help="Optional SQL output file. Defaults to stdout.")
    parser.add_argument("--limit", type=int, help="Only render the first N rows.")
    return parser.parse_args()


def normalize_key(key: str) -> str:
    """Normalize extractor column names such as `College_Code` and `COLLEGE CODE`."""
    normalized = key.strip().lstrip("\ufeff").lower()
    normalized = re.sub(r"[^a-z0-9]+", "_", normalized)
    return normalized.strip("_")


def normalized_row(row: dict[str, Any]) -> dict[str, Any]:
    values = dict(row)
    for key, value in row.items():
        values.setdefault(normalize_key(str(key)), value)
    return values


def load_rows(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        rows: list[dict[str, Any]] = []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                rows.append(normalized_row(row))
                if limit and len(rows) >= limit:
                    break
        return rows

    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, dict):
        if isinstance(payload.get("items"), list):
            rows = payload["items"]
        elif isinstance(payload.get("rows"), list):
            rows = payload["rows"]
        else:
            rows = [payload]
    elif isinstance(payload, list):
        rows = payload
    else:
        raise ValueError("Seed source must be a JSON/CSV object, object with rows/items, or array.")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Every seed row must be an object.")
    rows = [normalized_row(row) for row in rows]
    return rows[:limit] if limit else rows


def first_value(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    normalized = normalized_row(row)
    for key in keys:
        if key in row and row[key] not in ("", None):
            return row[key]
        normalized_key = normalize_key(key)
        if normalized_key in normalized and normalized[normalized_key] not in ("", None):
            return normalized[normalized_key]
    return default


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float):
        return str(value)
    if isinstance(value, list | dict):
        value = json.dumps(value, ensure_ascii=True, separators=(",", ":"))
    return "'" + str(value).replace("'", "''") + "'"


def render_insert(table: str, columns: list[str], rows: Iterable[dict[str, Any]], conflict: str | None = None) -> str:
    values = ["(" + ", ".join(sql_literal(row.get(column)) for column in columns) + ")" for row in rows]
    if not values:
        return f"-- No rows for {table}\n"

    sql = [
        f"INSERT INTO {table} ({', '.join(columns)})",
        "VALUES",
        ",\n".join(values),
    ]
    if conflict:
        protected = set(conflict.strip("()").replace(" ", "").split(","))
        updates = [f"{column} = EXCLUDED.{column}" for column in columns if column not in protected]
        sql.append(f"ON CONFLICT {conflict} DO UPDATE SET {', '.join(updates)}, updated_at = now()")
    sql.append(";")
    return "\n".join(sql) + "\n"


def render_freshness_update(dataset_name: str, source_reference: str | None = None, rows_loaded: int | None = None) -> str:
    notes = "Loaded by offline seed script"
    if rows_loaded is not None:
        notes = f"{notes}; rows_loaded={rows_loaded}"
    return render_insert(
        "data_freshness",
        ["dataset_name", "last_success_at", "freshness_status", "source_reference", "notes"],
        [
            {
                "dataset_name": dataset_name,
                "last_success_at": "now()",
                "freshness_status": "verified",
                "source_reference": source_reference,
                "notes": notes,
            }
        ],
        "(dataset_name)",
    ).replace("'now()'", "now()")


def project_rows(source_rows: list[dict[str, Any]], specs: list[ColumnSpec]) -> list[dict[str, Any]]:
    projected = []
    for row in source_rows:
        next_row: dict[str, Any] = {}
        for column, resolver in specs:
            next_row[column] = resolver(row) if callable(resolver) else first_value(row, column, str(column).upper(), default=resolver)
        projected.append(next_row)
    return projected


def write_sql(sql: str, out: Path | None) -> None:
    if out:
        out.write_text(sql, encoding="utf-8")
    else:
        print(sql, end="")


def build_seed_sql(description: str, table: str, specs: list[ColumnSpec], conflict: str | None, freshness_dataset: str | None = None) -> None:
    args = parse_args(description)
    if not args.source:
        raise SystemExit("source JSON path is required")
    rows = project_rows(load_rows(args.source, args.limit), specs)
    sql = render_insert(table, [column for column, _ in specs], rows, conflict)
    if freshness_dataset:
        sql += "\n" + render_freshness_update(freshness_dataset, str(args.source), len(rows))
    write_sql(sql, args.out)
