#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
import re

from qa.report_utils import count_missing, ensure_dir, pct, write_json, write_text

ROOT = Path(__file__).resolve().parents[1]
RAW_JSON = ROOT / "College_Info_Done/output.json"
FILTERED_JSON = ROOT / "College_Info_Done/output_present_non_architecture.json"
REPORT_DIR = ROOT / "qa/reports"
JSON_OUT = REPORT_DIR / "college_info_summary.json"
MD_OUT = REPORT_DIR / "college_info_summary.md"

KEY_FIELDS = [
    "College_Code",
    "College_Name",
    "District",
    "Website",
    "Address",
    "Placement_Record",
    "Autonomous_Status",
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_district(value: str) -> str:
    text = str(value).strip().upper()
    if not text:
        return ""
    if re.fullmatch(r"\d{6}", text):
        return "<PINCODE_LIKE>"
    return text


def summarize(colleges: list[dict]) -> dict:
    districts = Counter()
    autonomy = Counter()
    missing = {}
    courses_total = 0
    colleges_with_courses = 0
    colleges_with_nba_course = 0
    pincode_like_districts = 0

    for field in KEY_FIELDS:
        missing[field] = count_missing(colleges, field)

    for college in colleges:
        district_raw = str(college.get("District", "")).strip()
        district = normalize_district(district_raw)
        if district:
            districts[district] += 1
        if district == "<PINCODE_LIKE>":
            pincode_like_districts += 1
        autonomy[str(college.get("Autonomous_Status", "")).strip() or "<blank>"] += 1

        courses = college.get("courses", [])
        if isinstance(courses, list) and courses:
            colleges_with_courses += 1
            courses_total += len(courses)
            if any(str(c.get("NBA_Accredited", "")).strip().lower() == "yes" for c in courses if isinstance(c, dict)):
                colleges_with_nba_course += 1

    return {
        "count": len(colleges),
        "missing_field_counts": missing,
        "missing_field_pct": {field: pct(value, len(colleges)) for field, value in missing.items()},
        "district_count": len(districts),
        "top_15_districts": districts.most_common(15),
        "autonomy_counts": dict(sorted(autonomy.items())),
        "pincode_like_district_rows": pincode_like_districts,
        "pincode_like_district_pct": pct(pincode_like_districts, len(colleges)),
        "colleges_with_courses": colleges_with_courses,
        "colleges_with_courses_pct": pct(colleges_with_courses, len(colleges)),
        "avg_courses_per_college": round(courses_total / len(colleges), 4) if colleges else 0.0,
        "colleges_with_nba_course": colleges_with_nba_course,
        "colleges_with_nba_course_pct": pct(colleges_with_nba_course, len(colleges)),
    }


def main() -> int:
    ensure_dir(REPORT_DIR)
    raw = load(RAW_JSON)
    filtered = load(FILTERED_JSON)

    summary = {
        "raw": summarize(raw),
        "filtered": summarize(filtered),
    }
    write_json(JSON_OUT, summary)

    md = []
    md.append("# College Info QA Summary")
    md.append("")
    md.append(f"- Raw colleges: {summary['raw']['count']}")
    md.append(f"- Filtered colleges: {summary['filtered']['count']}")
    md.append(f"- Raw colleges with course data: {summary['raw']['colleges_with_courses']} ({summary['raw']['colleges_with_courses_pct']}%)")
    md.append(f"- Filtered colleges with course data: {summary['filtered']['colleges_with_courses']} ({summary['filtered']['colleges_with_courses_pct']}%)")
    md.append(f"- Filtered pincode-like district rows: {summary['filtered']['pincode_like_district_rows']} ({summary['filtered']['pincode_like_district_pct']}%)")
    md.append("")
    md.append("## Raw missing field percentages")
    for field, value in summary['raw']['missing_field_pct'].items():
        md.append(f"- {field}: {value}% missing")
    md.append("")
    md.append("## Filtered top districts")
    for district, count in summary['filtered']['top_15_districts']:
        md.append(f"- {district}: {count}")

    write_text(MD_OUT, "\n".join(md) + "\n")
    print(f"Wrote {JSON_OUT}")
    print(f"Wrote {MD_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
