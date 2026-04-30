"""Build aggregate-mark rank lookup rows from merged GRL CSV data."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from seed_utils import first_value, load_rows

DEFAULT_SOURCE = (
    Path(__file__).resolve().parents[2]
    / "supabase_db"
    / "seed_data"
    / "rank_lookup"
    / "general_rank_list_2020_2025.csv"
)


def decimal_key(value: Any) -> str | None:
    if value in (None, ""):
        return None
    try:
        decimal = Decimal(str(value).strip())
    except InvalidOperation:
        return None
    return format(decimal.quantize(Decimal("0.0001")).normalize(), "f")


def confidence(sample_size: int, source_year_count: int) -> str:
    if sample_size >= 100 and source_year_count >= 4:
        return "High"
    if sample_size >= 30 and source_year_count >= 2:
        return "Medium"
    return "Low"


def build_rows(source: Path, limit: int | None = None) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "rank_min": None,
            "rank_max": None,
            "sample_size": 0,
            "source_years": set(),
        }
    )
    for row in load_rows(source, limit):
        mark = decimal_key(first_value(row, "aggregate_mark", "aggregate mark"))
        rank_value = first_value(row, "general_rank", "general rank", "rank")
        year_value = first_value(row, "season_year", "year")
        if mark is None or rank_value in (None, ""):
            continue
        try:
            rank = int(str(rank_value).strip())
            year = int(str(year_value).strip()) if year_value not in (None, "") else None
        except ValueError:
            continue
        item = grouped[mark]
        item["rank_min"] = rank if item["rank_min"] is None else min(item["rank_min"], rank)
        item["rank_max"] = rank if item["rank_max"] is None else max(item["rank_max"], rank)
        item["sample_size"] += 1
        if year:
            item["source_years"].add(year)

    rows: list[dict[str, Any]] = []
    for mark, item in sorted(grouped.items(), key=lambda pair: Decimal(pair[0]), reverse=True):
        years = sorted(item["source_years"])
        sample_size = int(item["sample_size"])
        rows.append(
            {
                "aggregate_mark": mark,
                "rank_min": item["rank_min"],
                "rank_max": item["rank_max"],
                "confidence_label": confidence(sample_size, len(years)),
                "sample_size": sample_size,
                "source_years": json.dumps(years, separators=(",", ":")),
                "method_version": "grl-aggregate-v1",
                "is_abstain": "false",
            }
        )
    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build rank_lookup seed CSV from merged GRL rows.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = build_rows(args.source, args.limit)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = [
            "aggregate_mark",
            "rank_min",
            "rank_max",
            "confidence_label",
            "sample_size",
            "source_years",
            "method_version",
            "is_abstain",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"ok": True, "source": str(args.source), "out": str(args.out), "rows": len(rows)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
