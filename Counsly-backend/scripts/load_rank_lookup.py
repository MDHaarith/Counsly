"""Load generated rank_lookup CSV into PostgreSQL."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from seed_utils import first_value, load_rows


def row_tuple(row: dict[str, Any]) -> tuple[Any, ...]:
    source_years = first_value(row, "source_years", default="[]")
    if isinstance(source_years, str):
        source_years = json.loads(source_years or "[]")
    return (
        first_value(row, "aggregate_mark"),
        first_value(row, "rank_min"),
        first_value(row, "rank_max"),
        first_value(row, "confidence_label"),
        first_value(row, "sample_size"),
        json.dumps(source_years, separators=(",", ":")),
        first_value(row, "method_version", default="grl-aggregate-v1"),
        str(first_value(row, "is_abstain", default="false")).lower() == "true",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load generated rank_lookup CSV into PostgreSQL.")
    parser.add_argument("source", type=Path)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.database_url:
        raise SystemExit("DATABASE_URL is required")

    import psycopg
    from psycopg.types.json import Jsonb

    rows = [row_tuple(row) for row in load_rows(args.source)]
    with psycopg.connect(args.database_url) as conn:
        with conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO rank_lookup (
                    aggregate_mark, rank_min, rank_max, confidence_label, sample_size,
                    source_years, method_version, is_abstain
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (aggregate_mark) DO UPDATE SET
                    rank_min = EXCLUDED.rank_min,
                    rank_max = EXCLUDED.rank_max,
                    confidence_label = EXCLUDED.confidence_label,
                    sample_size = EXCLUDED.sample_size,
                    source_years = EXCLUDED.source_years,
                    method_version = EXCLUDED.method_version,
                    is_abstain = EXCLUDED.is_abstain,
                    updated_at = now()
                """,
                [
                    (*row[:5], Jsonb(json.loads(row[5])), row[6], row[7])
                    for row in rows
                ],
            )
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
                ("rank_lookup", "verified", str(args.source), f"Loaded {len(rows)} rank lookup rows"),
            )
            cur.execute(
                """
                INSERT INTO app_config (config_key, value_type, value_json, updated_by)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (config_key) DO UPDATE SET
                    value_json = EXCLUDED.value_json,
                    updated_by = EXCLUDED.updated_by,
                    updated_at = now()
                """,
                ("RANK_LOOKUP_READY", "boolean", Jsonb(True), "seed"),
            )
        conn.commit()
    print(f"Loaded {len(rows)} rank lookup rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
