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


LEGACY_COMMUNITIES = {"MBCDNC", "MBCV", "SCA"}


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def count_csv_rows(path: Path) -> int:
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        return max(sum(1 for _ in handle) - 1, 0)


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


def validate_training_csv(path: Path) -> dict[str, int]:
    validation = {
        "rows": 0,
        "bad_ranks": 0,
        "legacy_communities": 0,
        "architecture_branch_rows": 0,
    }

    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            validation["rows"] += 1
            if not row.get("RANK", "").strip().isdigit():
                validation["bad_ranks"] += 1
            if (
                row.get("COMMUNITY", "").strip() in LEGACY_COMMUNITIES
                or row.get("ALLOTTED CATEGORY", "").strip() in LEGACY_COMMUNITIES
            ):
                validation["legacy_communities"] += 1
            if row.get("BRANCH CODE", "").strip() in ARCHITECTURE_BRANCH_CODES:
                validation["architecture_branch_rows"] += 1

    if validation["rows"] == 0:
        raise RuntimeError(f"No rows found in training CSV {path}")
    if validation["bad_ranks"] != 0:
        raise RuntimeError(f"Training CSV still has {validation['bad_ranks']} bad ranks")
    if validation["legacy_communities"] != 0:
        raise RuntimeError(
            "Training CSV still has "
            f"{validation['legacy_communities']} legacy community values"
        )
    if validation["architecture_branch_rows"] != 0:
        raise RuntimeError(
            "Training CSV still has "
            f"{validation['architecture_branch_rows']} architecture branch rows"
        )

    return validation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Canonical end-to-end TNEA training-data pipeline: parse PDFs, merge clean "
            "records, filter by college reference JSON, and write the final "
            "training-ready CSV plus validation manifest."
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
    parser.add_argument(
        "--training-output",
        type=Path,
        default=None,
        help="Optional explicit path for the final training CSV",
    )
    parser.add_argument(
        "--training-removed-report",
        type=Path,
        default=None,
        help="Optional explicit path for the removed-rows report",
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=None,
        help="Optional explicit path for the pipeline manifest JSON",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()

    raw_root = args.raw_root.resolve()
    output_root = args.output_root.resolve()
    reference_json = args.reference_json.resolve()
    merged_root = output_root / MERGED_DIRNAME
    reports_root = output_root / REPORTS_DIRNAME
    merged_root.mkdir(parents=True, exist_ok=True)
    reports_root.mkdir(parents=True, exist_ok=True)

    training_output = (
        args.training_output.resolve()
        if args.training_output is not None
        else merged_root / "merged_records_all_years_rounds_training_ready.csv"
    )
    training_removed_report = (
        args.training_removed_report.resolve()
        if args.training_removed_report is not None
        else reports_root / "merged_records_all_years_rounds_training_ready_removed_rows.csv"
    )
    manifest_path = (
        args.manifest_path.resolve()
        if args.manifest_path is not None
        else reports_root / "training_pipeline_manifest.json"
    )

    batch_exit_code = 0
    if not args.skip_batch:
        batch_exit_code = run_batch(
            SimpleNamespace(
                root=raw_root,
                output_root=output_root,
                max_pages=args.max_pages,
                copy_source=args.copy_source,
                with_audit_files=args.with_audit_files,
            )
        )
        if batch_exit_code != 0:
            raise SystemExit(batch_exit_code)

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
        output_csv=training_output,
        removed_report=training_removed_report,
        drop_architecture_branches=True,
    )
    validation = validate_training_csv(training_output)

    manifest = {
        "raw_root": str(raw_root),
        "output_root": str(output_root),
        "reference_json": str(reference_json),
        "batch_skipped": args.skip_batch,
        "batch_exit_code": batch_exit_code,
        "reference_cleaned_csv": str(reference_cleaned_csv),
        "reference_cleaned_rows": count_csv_rows(reference_cleaned_csv),
        "filtered_reference_json": str(filtered_reference_json),
        "filtered_reference_json_colleges": len(kept_colleges),
        "filtered_reference_removed_report": str(filtered_reference_removed_report),
        "training_output_csv": training_result["output_csv"],
        "training_removed_report": training_result["removed_report"],
        "training_kept_rows": training_result["kept_rows"],
        "training_removed_rows": training_result["removed_rows"],
        "training_removal_counts": training_result["removal_counts"],
        "validation": validation,
    }
    write_json(manifest_path, manifest)

    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
