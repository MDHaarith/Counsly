#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from qa.report_utils import ensure_dir, pct, write_json, write_text

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "qa/reports"
JSON_OUT = REPORT_DIR / "geo_summary.json"
MD_OUT = REPORT_DIR / "geo_summary.md"

FILES = {
    "legacy_clean_output": ROOT / "geo_integration/College_Details/archive/intermediate/college_names_only_with_coordinates_final_cleaned.json",
    "legacy_unresolved": ROOT / "geo_integration/College_Details/archive/intermediate/college_names_only_with_coordinates_final_unresolved.json",
    "active_clean_output": ROOT / "geo_integration/active/v4go_intermediate/college_names_only_clean_output.json",
    "active_unresolved": ROOT / "geo_integration/active/v4go_intermediate/college_names_only_clean_output_unresolved.json",
}


def source_breakdown(records: list) -> dict:
    counts = {}
    for item in records:
        if not isinstance(item, dict):
            continue
        source = item.get("source") or "<missing>"
        counts[source] = counts.get(source, 0) + 1
    return dict(sorted(counts.items()))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def count_coords(records: list) -> int:
    count = 0
    for item in records:
        if isinstance(item, dict) and item.get("latitude") is not None and item.get("longitude") is not None:
            count += 1
    return count


def main() -> int:
    ensure_dir(REPORT_DIR)
    summary = {}

    for name, path in FILES.items():
        if not path.exists():
            summary[name] = {"exists": False}
            continue
        data = load_json(path)
        if isinstance(data, list):
            summary[name] = {
                "exists": True,
                "count": len(data),
                "with_coords": count_coords(data),
                "with_coords_pct": pct(count_coords(data), len(data)),
                "source_breakdown": source_breakdown(data),
            }
        else:
            summary[name] = {
                "exists": True,
                "type": type(data).__name__,
            }

    write_json(JSON_OUT, summary)

    md = []
    md.append("# Geo Integration QA Summary")
    md.append("")
    md.append("Focus: raw coordinate coverage and imported snapshot availability, not UI status.")
    md.append("")
    for name, info in summary.items():
        if not info.get("exists"):
            md.append(f"- {name}: missing")
            continue
        if "count" in info:
            md.append(f"- {name}: {info['count']} records, {info['with_coords']} with coordinates ({info['with_coords_pct']}%)")
            if info.get("source_breakdown"):
                md.append(f"  - sources: {info['source_breakdown']}")
        else:
            md.append(f"- {name}: exists")

    write_text(MD_OUT, "\n".join(md) + "\n")
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
