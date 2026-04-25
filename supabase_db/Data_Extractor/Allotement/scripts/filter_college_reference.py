#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


ARCHITECTURE_BRANCH_CODES = {"AR", "BA", "BP", "DA", "ID"}


def load_reference_colleges(reference_json: Path) -> list[dict]:
    with reference_json.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise RuntimeError(f"Expected a list of colleges in {reference_json}")
    return [item for item in payload if isinstance(item, dict)]


def load_present_college_codes(merged_csv: Path) -> set[str]:
    with merged_csv.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if "COLLEGE CODE" not in (reader.fieldnames or []):
            raise RuntimeError(f"'COLLEGE CODE' column not found in {merged_csv}")
        return {
            row.get("COLLEGE CODE", "").strip()
            for row in reader
            if row.get("COLLEGE CODE", "").strip()
        }


def extract_branch_codes(college: dict) -> list[str]:
    courses = college.get("courses", [])
    if not isinstance(courses, list):
        return []
    branch_codes: list[str] = []
    for course in courses:
        if not isinstance(course, dict):
            continue
        branch_code = str(course.get("Branch_Code", "")).strip()
        if branch_code:
            branch_codes.append(branch_code)
    return branch_codes


def is_architecture_only_college(college: dict) -> bool:
    branch_codes = extract_branch_codes(college)
    return bool(branch_codes) and set(branch_codes).issubset(ARCHITECTURE_BRANCH_CODES)


def default_output_json(reference_json: Path) -> Path:
    return reference_json.with_name(f"{reference_json.stem}_present_non_architecture.json")


def default_removed_report(reference_json: Path) -> Path:
    return reference_json.with_name("removed_architecture_or_absent_colleges.csv")


def write_removed_report(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["College_Code", "College_Name", "Reason"],
        )
        writer.writeheader()
        writer.writerows(rows)


def filter_reference_colleges(
    colleges: list[dict],
    present_codes: set[str],
) -> tuple[list[dict], list[dict[str, str]]]:
    kept: list[dict] = []
    removed: list[dict[str, str]] = []

    for college in colleges:
        college_code = str(college.get("College_Code", "")).strip()
        if not college_code:
            continue

        reasons: list[str] = []
        if college_code not in present_codes:
            reasons.append("not_present_in_allotment")
        if is_architecture_only_college(college):
            reasons.append("architecture_only")

        if reasons:
            removed.append(
                {
                    "College_Code": college_code,
                    "College_Name": str(college.get("College_Name", "")).strip(),
                    "Reason": "|".join(reasons),
                }
            )
            continue

        kept.append(college)

    return kept, removed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Filter a college reference JSON down to colleges that are present in the "
            "allotment data and not architecture-only institutions."
        )
    )
    parser.add_argument(
        "reference_json",
        type=Path,
        help="Path to the source college reference JSON file",
    )
    parser.add_argument(
        "merged_csv",
        type=Path,
        help="Path to the merged allotment CSV containing COLLEGE CODE",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=None,
        help="Optional explicit path for the filtered output JSON",
    )
    parser.add_argument(
        "--removed-report",
        type=Path,
        default=None,
        help="Optional explicit path for the CSV report of removed colleges",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    reference_json = args.reference_json.resolve()
    merged_csv = args.merged_csv.resolve()
    output_json = (
        args.output_json.resolve()
        if args.output_json is not None
        else default_output_json(reference_json)
    )
    removed_report = (
        args.removed_report.resolve()
        if args.removed_report is not None
        else default_removed_report(reference_json)
    )

    colleges = load_reference_colleges(reference_json)
    present_codes = load_present_college_codes(merged_csv)
    kept, removed = filter_reference_colleges(colleges, present_codes)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    with output_json.open("w", encoding="utf-8") as handle:
        json.dump(kept, handle, ensure_ascii=False, indent=2)
    write_removed_report(removed_report, removed)

    print(
        json.dumps(
            {
                "reference_json": str(reference_json),
                "merged_csv": str(merged_csv),
                "output_json": str(output_json),
                "removed_report": str(removed_report),
                "kept_colleges": len(kept),
                "removed_colleges": len(removed),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
