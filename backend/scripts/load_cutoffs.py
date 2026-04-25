"""Load historical cutoff CSV into PostgreSQL in batches."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any

from seed_utils import first_value, load_rows

DEFAULT_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "supabase_db"
    / "seed_data"
    / "cutoff_data"
    / "cutoffs_2020_2025_training_ready.csv"
)


def row_tuple(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        first_value(row, "season_year", "year"),
        first_value(row, "round_number", "round", default=1),
        first_value(row, "aggregate_mark", "aggregate mark"),
        first_value(row, "general_rank", "rank"),
        first_value(row, "community_quota", "community"),
        first_value(row, "community"),
        first_value(row, "college_code", "college"),
        first_value(row, "branch_code", "branch"),
        first_value(row, "allotted_category", "allotted category"),
        first_value(row, "application_number", "application number"),
        str(DEFAULT_SOURCE),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load cutoff_data from CSV into PostgreSQL.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--batch-size", type=int, default=5000)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.database_url:
        raise SystemExit("DATABASE_URL is required")

    import psycopg

    rows = load_rows(args.source, args.limit)
    loaded = 0
    sql = """
        INSERT INTO cutoff_data (
            season_year, round_number, aggregate_mark, general_rank, community_quota,
            source_community_raw, college_code, branch_code, allotted_category,
            application_number, source_file
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    with psycopg.connect(args.database_url) as conn:
        with conn.cursor() as cur:
            for index in range(0, len(rows), args.batch_size):
                batch = [row_tuple(row) for row in rows[index : index + args.batch_size]]
                cur.executemany(sql, batch)
                loaded += len(batch)
            cur.execute(
                """
                INSERT INTO data_freshness (dataset_name, last_success_at, freshness_status, source_reference, notes)
                VALUES (%s, now(), %s, %s, %s)
                ON CONFLICT (dataset_name) DO UPDATE SET
                    last_success_at = EXCLUDED.last_success_at,
                    freshness_status = EXCLUDED.freshness_status,
                    source_reference = EXCLUDED.source_reference,
                    notes = EXCLUDED.notes,
                    updated_at = now()
                """,
                ("cutoff_data", "verified", str(args.source), f"Loaded {loaded} cutoff rows"),
            )
        conn.commit()
    print(f"Loaded {loaded} cutoff rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
