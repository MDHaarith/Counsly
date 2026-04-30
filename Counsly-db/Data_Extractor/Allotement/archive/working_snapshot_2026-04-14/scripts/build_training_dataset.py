#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

from filter_allotment_reference import (
    ARCHITECTURE_BRANCH_CODES,
    build_allowed_college_codes,
    write_csv as write_rows_csv,
)
from filter_college_reference import (
    default_output_json,
    default_removed_report as default_reference_removed_report,
    filter_reference_colleges,
    load_present_college_codes,
    load_reference_colleges,
    write_removed_report,
)
from tnea_pdf_parser import MERGED_DIRNAME, REPORTS_DIRNAME, merge_clean_csvs, run_batch


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def filter_merged_for_training(
    *,
    merged_csv: Path,
    reference_json: Path,
    output_csv: Path,
    removed_report: Path,
    drop_architecture_branches: bool,
) -> dict[str, object]:
    allowed_codes, architecture_only_codes = build_allowed_college_codes(reference_json)
    kept_rows: list[dict[str, str]] = []
    removed_rows: list[dict[str, str]] = []
    removal_counts: Counter[str] = Counter()

    with merged_csv.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise RuntimeError(f"No headers found in {merged_csv}")
        fieldnames = list(reader.fieldnames)

        for row in reader:
            college_code = row.get("COLLEGE CODE", "").strip()
            branch_code = row.get("BRANCH CODE", "").strip()

            if college_code in allowed_codes:
                if drop_architecture_branches and branch_code in ARCHITECTURE_BRANCH_CODES:
                    removed_row = dict(row)
                    removed_row["REMOVAL_REASON"] = "architecture_branch"
                    removed_rows.append(removed_row)
                    removal_counts["architecture_branch"] += 1
                    continue
                kept_rows.append(dict(row))
                continue

            reason = "not_in_reference_json"
            if college_code in architecture_only_codes:
                reason = "architecture_only_college"
            removed_row = dict(row)
            removed_row["REMOVAL_REASON"] = reason
            removed_rows.append(removed_row)
            removal_counts[reason] += 1

    if not kept_rows:
        raise RuntimeError("No rows left after building the training dataset")

    write_rows_csv(output_csv, kept_rows, fieldnames)
    write_rows_csv(removed_report, removed_rows, [*fieldnames, "REMOVAL_REASON"])

    return {
        "output_csv": str(output_csv),
        "removed_report": str(removed_report),
        "kept_rows": len(kept_rows),
        "removed_rows": len(removed_rows),
        "removal_counts": dict(removal_counts),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run the full TNEA pipeline in one command: parse PDFs, merge records, "
            "filter by college reference JSON, and write the final training-ready CSV."
        )
    )
    parser.add_argument(
        "--raw-root",
        type=Path,
        default=Path("data/raw"),
        help="Root folder containing the source PDFs",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/processed"),
        help="Root folder containing bundles, merged files, and reports",
    )
    parser.add_argument(
        "--reference-json",
        type=Path,
        default=Path("/home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json"),
        help="Path to the source college reference JSON file",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional page limit per PDF during parsing",
    )
    parser.add_argument(
        "--with-audit-files",
        action="store_true",
        help="Also write audit files while parsing PDFs",
    )
    parser.add_argument(
        "--copy-source",
        action="store_true",
        help="Copy source PDFs into bundle folders during parsing",
    )
    parser.add_argument(
        "--skip-batch",
        action="store_true",
        help="Skip reparsing PDFs and reuse the existing processed bundles",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    raw_root = args.raw_root.resolve()
    output_root = args.output_root.resolve()
    reference_json = args.reference_json.resolve()
    merged_root = output_root / MERGED_DIRNAME
    reports_root = output_root / REPORTS_DIRNAME

    if not args.skip_batch:
        batch_result = run_batch(
            SimpleNamespace(
                root=raw_root,
                output_root=output_root,
                max_pages=args.max_pages,
                copy_source=args.copy_source,
                with_audit_files=args.with_audit_files,
            )
        )
        if batch_result != 0:
            raise SystemExit(batch_result)

    reference_cleaned_csv = merge_clean_csvs(
        output_root=output_root,
        destination=merged_root / "merged_records_all_years_rounds_cleaned_reference_colleges_only.csv",
        drop_abnormal_ranks=True,
        normalize_communities=True,
        retain_only_college_codes_from_json=reference_json,
    )

    colleges = load_reference_colleges(reference_json)
    present_codes = load_present_college_codes(reference_cleaned_csv)
    kept_colleges, removed_colleges = filter_reference_colleges(colleges, present_codes)

    filtered_reference_json = default_output_json(reference_json)
    filtered_reference_removed_report = default_reference_removed_report(reference_json)
    write_json(filtered_reference_json, kept_colleges)
    write_removed_report(filtered_reference_removed_report, removed_colleges)

    training_result = filter_merged_for_training(
        merged_csv=reference_cleaned_csv,
        reference_json=reference_json,
        output_csv=merged_root / "merged_records_all_years_rounds_training_ready.csv",
        removed_report=reports_root / "merged_records_all_years_rounds_training_ready_removed_rows.csv",
        drop_architecture_branches=True,
    )

    print(
        json.dumps(
            {
                "raw_root": str(raw_root),
                "output_root": str(output_root),
                "reference_json": str(reference_json),
                "reference_cleaned_csv": str(reference_cleaned_csv),
                "filtered_reference_json": str(filtered_reference_json),
                "filtered_reference_removed_report": str(filtered_reference_removed_report),
                "training_output_csv": training_result["output_csv"],
                "training_removed_report": training_result["removed_report"],
                "training_kept_rows": training_result["kept_rows"],
                "training_removed_rows": training_result["removed_rows"],
                "training_removal_counts": training_result["removal_counts"],
                "batch_skipped": args.skip_batch,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
