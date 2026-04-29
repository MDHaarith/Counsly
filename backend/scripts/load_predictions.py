"""Load generated ML prediction CSVs into PostgreSQL/Supabase."""

from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
from typing import Iterable

import psycopg

ROOT = Path(__file__).resolve().parents[2]
CLOSING_CSV = ROOT / "ML/predictions/closing_ranks_2026.csv"
RANK_CSV = ROOT / "ML/predictions/rank_bands_2026.csv"
BATCH_SIZE = 5000


def _chunks(rows: list[dict[str, str]], size: int) -> Iterable[list[dict[str, str]]]:
    for index in range(0, len(rows), size):
        yield rows[index : index + size]


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_closing(conn: psycopg.Connection, path: Path) -> int:
    rows = _read_csv(path)
    sql = """
        INSERT INTO predicted_closing_ranks (
            season_year, round_number, community_quota, college_code, branch_code,
            predicted_closing_rank, prediction_lower, prediction_upper,
            confidence_label, model_version
        )
        VALUES (
            %(season_year)s, %(round_number)s, %(community_quota)s, %(college_code)s, %(branch_code)s,
            %(predicted_closing_rank)s, %(prediction_lower)s, %(prediction_upper)s,
            %(confidence_label)s, %(model_version)s
        )
        ON CONFLICT (season_year, round_number, community_quota, college_code, branch_code)
        DO UPDATE SET
            predicted_closing_rank = EXCLUDED.predicted_closing_rank,
            prediction_lower = EXCLUDED.prediction_lower,
            prediction_upper = EXCLUDED.prediction_upper,
            confidence_label = EXCLUDED.confidence_label,
            model_version = EXCLUDED.model_version,
            predicted_at = now()
    """
    with conn.cursor() as cur:
        for batch in _chunks(rows, BATCH_SIZE):
            cur.executemany(sql, batch)
    conn.commit()
    return len(rows)


def load_rank_bands(conn: psycopg.Connection, path: Path) -> int:
    rows = _read_csv(path)
    sql = """
        INSERT INTO predicted_rank_bands (
            aggregate_mark, community_quota, predicted_rank_min, predicted_rank_max,
            predicted_total_students, confidence_label, model_version
        )
        VALUES (
            %(aggregate_mark)s, %(community_quota)s, %(predicted_rank_min)s, %(predicted_rank_max)s,
            %(predicted_total_students)s, %(confidence_label)s, %(model_version)s
        )
        ON CONFLICT (aggregate_mark, community_quota)
        DO UPDATE SET
            predicted_rank_min = EXCLUDED.predicted_rank_min,
            predicted_rank_max = EXCLUDED.predicted_rank_max,
            predicted_total_students = EXCLUDED.predicted_total_students,
            confidence_label = EXCLUDED.confidence_label,
            model_version = EXCLUDED.model_version,
            predicted_at = now()
    """
    with conn.cursor() as cur:
        for batch in _chunks(rows, BATCH_SIZE):
            cur.executemany(sql, batch)
    conn.commit()
    return len(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL"))
    parser.add_argument("--closing-csv", type=Path, default=CLOSING_CSV)
    parser.add_argument("--rank-csv", type=Path, default=RANK_CSV)
    args = parser.parse_args()
    if not args.database_url:
        raise SystemExit("DATABASE_URL is required")

    with psycopg.connect(args.database_url) as conn:
        closing_count = load_closing(conn, args.closing_csv)
        rank_count = load_rank_bands(conn, args.rank_csv)
    print(f"Loaded {closing_count:,} predicted closing ranks")
    print(f"Loaded {rank_count:,} predicted rank bands")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
