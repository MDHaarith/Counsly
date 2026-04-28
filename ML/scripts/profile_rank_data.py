"""Profile historical rank-list data for rank-prediction modeling."""

from __future__ import annotations

import csv
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RANK_SOURCE = ROOT / "data" / "raw" / "general_rank_list_2020_2025.csv"
REPORT_DIR = ROOT / "reports"


def read_rows() -> list[dict[str, str]]:
    with RANK_SOURCE.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    rows = read_rows()
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    by_year: dict[str, list[dict[str, str]]] = defaultdict(list)
    community_counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        year = row["YEAR"]
        by_year[year].append(row)
        community_counts[(year, row["COMMUNITY"])] += 1

    summary_path = REPORT_DIR / "rank_year_summary.csv"
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            lineterminator="\n",
            fieldnames=[
                "year",
                "total_students",
                "rank_min",
                "rank_max",
                "aggregate_mark_min",
                "aggregate_mark_max",
            ],
        )
        writer.writeheader()
        for year in sorted(by_year):
            year_rows = by_year[year]
            ranks = [int(row["GENERAL RANK"]) for row in year_rows if row["GENERAL RANK"]]
            marks = [Decimal(row["AGGREGATE MARK"]) for row in year_rows if row["AGGREGATE MARK"]]
            writer.writerow(
                {
                    "year": year,
                    "total_students": len(year_rows),
                    "rank_min": min(ranks),
                    "rank_max": max(ranks),
                    "aggregate_mark_min": min(marks),
                    "aggregate_mark_max": max(marks),
                }
            )

    community_path = REPORT_DIR / "community_year_counts.csv"
    with community_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["year", "community", "students"], lineterminator="\n")
        writer.writeheader()
        for year, community in sorted(community_counts):
            writer.writerow({"year": year, "community": community, "students": community_counts[(year, community)]})

    print(f"Wrote {summary_path}")
    print(f"Wrote {community_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
