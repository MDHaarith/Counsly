"""Ingest the latest extracted seat matrix into Supabase/Postgres.

This script is intentionally scoped to round-by-round seat-matrix refreshes.
It expects `colleges` to already be seeded, then upserts:
- branches
- college_branches
- a physical per-round seat table such as seat_matrix_2026_r1
- optionally, seat_matrix_current as the latest app-facing availability mirror
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SEAT_MATRIX = REPO_ROOT / "supabase_db" / "Data_Extractor" / "Seat_Matrix" / "output" / "seat_matrix_data.json"
DEFAULT_BRANCHES = REPO_ROOT / "supabase_db" / "Data_Extractor" / "Seat_Matrix" / "output" / "branch_codes_filtered.json"
TABLE_NAME_PATTERN = re.compile(r"^seat_matrix_2026_r[0-9]+$")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def as_text(value: Any) -> str:
    return str(value).strip()


def as_int(value: Any) -> int:
    if value in (None, ""):
        return 0
    return int(value)


def as_date(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)[:10]


def normalize_branches(branch_rows: list[dict[str, Any]], seat_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_code: dict[str, dict[str, Any]] = {}
    for row in branch_rows:
        code = as_text(row.get("branch_code"))
        if not code:
            continue
        by_code[code] = {
            "branch_code": code,
            "branch_name": as_text(row.get("branch_name") or code),
            "is_architecture": bool(row.get("is_architecture", False)),
            "keep": bool(row.get("keep", True)),
            "removal_reasons": row.get("removal_reasons") or [],
        }

    for row in seat_rows:
        code = as_text(row.get("branch_code"))
        if code and code not in by_code:
            by_code[code] = {
                "branch_code": code,
                "branch_name": as_text(row.get("branch_name") or code),
                "is_architecture": False,
                "keep": True,
                "removal_reasons": [],
            }
    return sorted(by_code.values(), key=lambda item: item["branch_code"])


def seat_matrix_table_name(season_year: int, round_number: int) -> str:
    return f"seat_matrix_{season_year}_r{round_number}"


def validate_table_name(name: str) -> str:
    if not TABLE_NAME_PATTERN.fullmatch(name):
        raise ValueError("Seat matrix table name must match seat_matrix_2026_rN")
    return name


def normalize_seat_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        college_code = as_text(row.get("college_code"))
        branch_code = as_text(row.get("branch_code"))
        if not college_code or not branch_code:
            continue
        by_key[(college_code, branch_code)] = {
            "college_code": college_code,
            "branch_code": branch_code,
            "branch_name": as_text(row.get("branch_name") or branch_code),
            "oc": as_int(row.get("oc")),
            "bc": as_int(row.get("bc")),
            "bcm": as_int(row.get("bcm")),
            "mbc": as_int(row.get("mbc")),
            "sc": as_int(row.get("sc")),
            "sca": as_int(row.get("sca")),
            "st": as_int(row.get("st")),
            "total": as_int(row.get("total")),
            "source_file": row.get("source_file"),
            "extraction_date": as_date(row.get("extraction_date")),
        }
    return list(by_key.values())


def existing_college_codes(conn: Any) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("SELECT college_code FROM colleges")
        return {as_text(row[0]) for row in cur.fetchall()}


def upsert_branches(conn: Any, branches: list[dict[str, Any]]) -> None:
    from psycopg.types.json import Jsonb

    params = [
        (
            row["branch_code"],
            row["branch_name"],
            row["is_architecture"],
            row["keep"],
            Jsonb(row["removal_reasons"]),
        )
        for row in branches
    ]
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO branches (branch_code, branch_name, is_architecture, keep, removal_reasons)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (branch_code) DO UPDATE SET
                branch_name = EXCLUDED.branch_name,
                is_architecture = EXCLUDED.is_architecture,
                keep = EXCLUDED.keep,
                removal_reasons = EXCLUDED.removal_reasons,
                updated_at = now()
            """,
            params,
        )


def upsert_college_branches(conn: Any, rows: list[dict[str, Any]]) -> None:
    params = [
        (
            row["college_code"],
            row["branch_code"],
            row["branch_name"],
            row["source_file"],
            row["extraction_date"],
        )
        for row in rows
    ]
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO college_branches (college_code, branch_code, branch_name, active, source_file, extraction_date)
            VALUES (%s, %s, %s, true, %s, %s)
            ON CONFLICT (college_code, branch_code) DO UPDATE SET
                branch_name = EXCLUDED.branch_name,
                active = true,
                source_file = EXCLUDED.source_file,
                extraction_date = EXCLUDED.extraction_date,
                updated_at = now()
            """,
            params,
        )


def create_round_table(conn: Any, table_name: str) -> None:
    from psycopg import sql

    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    college_code TEXT NOT NULL REFERENCES colleges (college_code),
                    branch_code TEXT NOT NULL REFERENCES branches (branch_code),
                    oc INT NOT NULL DEFAULT 0,
                    bc INT NOT NULL DEFAULT 0,
                    bcm INT NOT NULL DEFAULT 0,
                    mbc INT NOT NULL DEFAULT 0,
                    sc INT NOT NULL DEFAULT 0,
                    sca INT NOT NULL DEFAULT 0,
                    st INT NOT NULL DEFAULT 0,
                    total INT NOT NULL DEFAULT 0,
                    source_file TEXT,
                    extraction_date DATE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT {unique_name} UNIQUE (college_code, branch_code)
                )
                """
            ).format(
                table_name=sql.Identifier(table_name),
                unique_name=sql.Identifier(f"uq_{table_name}"),
            )
        )
        cur.execute(sql.SQL("ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY").format(table_name=sql.Identifier(table_name)))
        cur.execute(
            sql.SQL("CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} (college_code, branch_code)").format(
                index_name=sql.Identifier(f"idx_{table_name}_college_branch"),
                table_name=sql.Identifier(table_name),
            )
        )


def upsert_round_seat_matrix(conn: Any, table_name: str, rows: list[dict[str, Any]]) -> None:
    from psycopg import sql

    params = [
        (
            row["college_code"],
            row["branch_code"],
            row["oc"],
            row["bc"],
            row["bcm"],
            row["mbc"],
            row["sc"],
            row["sca"],
            row["st"],
            row["total"],
            row["source_file"],
            row["extraction_date"],
        )
        for row in rows
    ]
    with conn.cursor() as cur:
        cur.executemany(
            sql.SQL(
                """
                INSERT INTO {table_name} (
                    college_code, branch_code, oc, bc, bcm, mbc, sc, sca, st, total, source_file, extraction_date
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (college_code, branch_code) DO UPDATE SET
                    oc = EXCLUDED.oc,
                    bc = EXCLUDED.bc,
                    bcm = EXCLUDED.bcm,
                    mbc = EXCLUDED.mbc,
                    sc = EXCLUDED.sc,
                    sca = EXCLUDED.sca,
                    st = EXCLUDED.st,
                    total = EXCLUDED.total,
                    source_file = EXCLUDED.source_file,
                    extraction_date = EXCLUDED.extraction_date,
                    updated_at = now()
                """
            ).format(table_name=sql.Identifier(table_name)),
            params,
        )


def upsert_current_seat_matrix(conn: Any, rows: list[dict[str, Any]]) -> None:
    params = [
        (
            row["college_code"],
            row["branch_code"],
            row["oc"],
            row["bc"],
            row["bcm"],
            row["mbc"],
            row["sc"],
            row["sca"],
            row["st"],
            row["total"],
            row["source_file"],
            row["extraction_date"],
        )
        for row in rows
    ]
    with conn.cursor() as cur:
        cur.executemany(
            """
            INSERT INTO seat_matrix_current (
                college_code, branch_code, oc, bc, bcm, mbc, sc, sca, st, total, source_file, extraction_date
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (college_code, branch_code) DO UPDATE SET
                oc = EXCLUDED.oc,
                bc = EXCLUDED.bc,
                bcm = EXCLUDED.bcm,
                mbc = EXCLUDED.mbc,
                sc = EXCLUDED.sc,
                sca = EXCLUDED.sca,
                st = EXCLUDED.st,
                total = EXCLUDED.total,
                source_file = EXCLUDED.source_file,
                extraction_date = EXCLUDED.extraction_date,
                updated_at = now()
            """,
            params,
        )


def upsert_round_metadata(
    conn: Any,
    season_year: int,
    round_number: int,
    table_name: str,
    rows_loaded: int,
    rows: list[dict[str, Any]],
) -> None:
    source_file = next((row.get("source_file") for row in rows if row.get("source_file")), None)
    extraction_date = next((row.get("extraction_date") for row in rows if row.get("extraction_date")), None)
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO seat_matrix_round_tables (
                season_year, round_number, table_name, source_file, extraction_date, rows_loaded
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (season_year, round_number) DO UPDATE SET
                table_name = EXCLUDED.table_name,
                source_file = EXCLUDED.source_file,
                extraction_date = EXCLUDED.extraction_date,
                rows_loaded = EXCLUDED.rows_loaded,
                updated_at = now()
            """,
            (season_year, round_number, table_name, source_file, extraction_date, rows_loaded),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Upsert extracted TNEA seat-matrix data into Supabase.")
    parser.add_argument("--seat-matrix", type=Path, default=DEFAULT_SEAT_MATRIX)
    parser.add_argument("--branches", type=Path, default=DEFAULT_BRANCHES)
    parser.add_argument("--season-year", type=int, default=2026)
    parser.add_argument("--round-number", type=int, default=1)
    parser.add_argument("--table-name", help="Defaults to seat_matrix_2026_r<round>.")
    parser.add_argument("--sync-current", action="store_true", help="Also mirror this round into the app-facing seat_matrix_current table.")
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--dry-run", action="store_true", help="Validate and print counts without writing to the DB.")
    parser.add_argument(
        "--fail-on-missing-colleges",
        action="store_true",
        help="Fail if the seat matrix contains college codes not present in the colleges table.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.season_year != 2026:
        raise SystemExit("Seat-matrix ingestion is restricted to 2026. Pass --season-year 2026.")
    if not args.database_url and not args.dry_run:
        raise SystemExit("DATABASE_URL is required unless --dry-run is used.")

    table_name = validate_table_name(args.table_name or seat_matrix_table_name(args.season_year, args.round_number))
    seat_rows = normalize_seat_rows(load_json(args.seat_matrix))
    branch_rows = normalize_branches(load_json(args.branches), seat_rows)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "ok": True,
                    "dry_run": True,
                    "branches": len(branch_rows),
                    "round_number": args.round_number,
                    "season_year": args.season_year,
                    "sync_current": args.sync_current,
                    "table_name": table_name,
                    "seat_rows": len(seat_rows),
                    "seat_matrix": str(args.seat_matrix),
                    "branches_file": str(args.branches),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    assert args.database_url is not None
    import psycopg

    with psycopg.connect(args.database_url) as conn:
        known_colleges = existing_college_codes(conn)
        missing = sorted({row["college_code"] for row in seat_rows if row["college_code"] not in known_colleges})
        if missing and args.fail_on_missing_colleges:
            raise SystemExit(f"Seat matrix has {len(missing)} college codes missing from colleges table: {missing[:20]}")

        ingest_rows = [row for row in seat_rows if row["college_code"] in known_colleges]
        upsert_branches(conn, branch_rows)
        upsert_college_branches(conn, ingest_rows)
        create_round_table(conn, table_name)
        upsert_round_seat_matrix(conn, table_name, ingest_rows)
        upsert_round_metadata(conn, args.season_year, args.round_number, table_name, len(ingest_rows), ingest_rows)
        if args.sync_current:
            upsert_current_seat_matrix(conn, ingest_rows)
        conn.commit()

    print(
        json.dumps(
            {
                "ok": True,
                "branches_upserted": len(branch_rows),
                "round_number": args.round_number,
                "season_year": args.season_year,
                "sync_current": args.sync_current,
                "table_name": table_name,
                "seat_rows_seen": len(seat_rows),
                "seat_rows_upserted": len(ingest_rows),
                "missing_college_codes_skipped": len(missing),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
