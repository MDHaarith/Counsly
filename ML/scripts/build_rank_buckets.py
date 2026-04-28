"""Build 1-point aggregate-mark buckets for rank prediction."""

from __future__ import annotations

import csv
from collections import defaultdict
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RANK_SOURCE = ROOT / "data" / "raw" / "general_rank_list_2020_2025.csv"
REPORT_DIR = ROOT / "reports"
OUTPUT_PATH = REPORT_DIR / "rank_mark_buckets_1pt.csv"


def bucket_mark_1pt(value: str) -> int:
    """Map a raw aggregate mark to its whole-number bucket."""
    return int(Decimal(value).quantize(Decimal("1"), rounding=ROUND_FLOOR))


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    yearly_totals: dict[str, int] = defaultdict(int)
    buckets: dict[tuple[str, int], list[dict[str, str]]] = defaultdict(list)

    with RANK_SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            year = row["YEAR"]
            mark_bucket = bucket_mark_1pt(row["AGGREGATE MARK"])
            yearly_totals[year] += 1
            buckets[(year, mark_bucket)].append(row)

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "year",
                "mark_bucket",
                "total_students",
                "bucket_size",
                "rank_min",
                "rank_max",
                "aggregate_mark_min",
                "aggregate_mark_max",
                "community_modes",
            ],
            lineterminator="\n",
        )
        writer.writeheader()

        for year, mark_bucket in sorted(buckets):
            rows = buckets[(year, mark_bucket)]
            ranks = [int(row["GENERAL RANK"]) for row in rows if row["GENERAL RANK"]]
            marks = [Decimal(row["AGGREGATE MARK"]) for row in rows if row["AGGREGATE MARK"]]
            community_counts: dict[str, int] = defaultdict(int)
            for row in rows:
                community_counts[row["COMMUNITY"]] += 1
            community_modes = ";".join(
                f"{community}:{count}" for community, count in sorted(community_counts.items(), key=lambda item: (-item[1], item[0]))[:5]
            )
            writer.writerow(
                {
                    "year": year,
                    "mark_bucket": mark_bucket,
                    "total_students": yearly_totals[year],
                    "bucket_size": len(rows),
                    "rank_min": min(ranks),
                    "rank_max": max(ranks),
                    "aggregate_mark_min": min(marks),
                    "aggregate_mark_max": max(marks),
                    "community_modes": community_modes,
                }
            )

    print(f"Wrote {OUTPUT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
