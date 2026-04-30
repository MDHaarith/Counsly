#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path

from qa.report_utils import ensure_dir, read_csv_rows, write_json, write_text

ROOT = Path(__file__).resolve().parents[1]
GRL_CSV = ROOT / "General_Rank_List/processed/merged/merged_general_rank_list_all_years.csv"
REPORT_DIR = ROOT / "qa/reports"
JSON_OUT = REPORT_DIR / "grl_summary.json"
MD_OUT = REPORT_DIR / "grl_summary.md"


def main() -> int:
    ensure_dir(REPORT_DIR)
    rows = read_csv_rows(GRL_CSV)

    year_counts = Counter()
    community_counts = Counter()
    blank_community_rank = 0
    blank_aggregate = 0

    for row in rows:
        year_counts[row.get("YEAR", "").strip()] += 1
        community_counts[row.get("COMMUNITY", "").strip()] += 1
        if not row.get("COMMUNITY RANK", "").strip():
            blank_community_rank += 1
        if not row.get("AGGREGATE MARK", "").strip():
            blank_aggregate += 1

    summary = {
        "row_count": len(rows),
        "year_counts": dict(sorted(year_counts.items())),
        "community_counts": dict(sorted(community_counts.items())),
        "blank_community_rank_rows": blank_community_rank,
        "blank_aggregate_mark_rows": blank_aggregate,
    }
    write_json(JSON_OUT, summary)

    md = []
    md.append("# General Rank List QA Summary")
    md.append("")
    md.append(f"- Rows: {summary['row_count']}")
    md.append(f"- Blank community rank rows: {summary['blank_community_rank_rows']}")
    md.append(f"- Blank aggregate mark rows: {summary['blank_aggregate_mark_rows']}")
    md.append("")
    md.append("## Year counts")
    for year, count in summary['year_counts'].items():
        md.append(f"- {year}: {count}")
    md.append("")
    md.append("## Community counts")
    for community, count in summary['community_counts'].items():
        md.append(f"- {community}: {count}")

    write_text(MD_OUT, "\n".join(md) + "\n")
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
