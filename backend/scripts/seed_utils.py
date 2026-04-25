"""Offline seed SQL helpers.

These helpers intentionally do not connect to Supabase/Postgres. They convert
reviewed JSON exports into SQL that can be inspected and applied separately.
"""

from __future__ import annotations

import argparse
import json
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


def load_rows(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
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
        raise ValueError("Seed source must be a JSON object, object with rows/items, or array.")
    if not all(isinstance(row, dict) for row in rows):
        raise ValueError("Every seed row must be a JSON object.")
    return rows[:limit] if limit else rows


def first_value(row: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in row and row[key] not in ("", None):
            return row[key]
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


def build_seed_sql(description: str, table: str, specs: list[ColumnSpec], conflict: str | None) -> None:
    args = parse_args(description)
    if not args.source:
        raise SystemExit("source JSON path is required")
    rows = project_rows(load_rows(args.source, args.limit), specs)
    write_sql(render_insert(table, [column for column, _ in specs], rows, conflict), args.out)
