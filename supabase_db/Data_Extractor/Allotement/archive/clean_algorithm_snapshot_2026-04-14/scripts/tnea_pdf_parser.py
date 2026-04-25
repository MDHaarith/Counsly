#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


RECORD_START_RE = re.compile(r"^\s*(\d+)\s+(\d{6})\b")
MARK_RE = re.compile(r"^\d+(?:\.\d+)?$")
RANK_RE = re.compile(r"^\d+[A-Z]*$")
DATE_RE = re.compile(r"^\d{2}-\d{2}-\d{4}$")
YEAR_RE = re.compile(r"ADMISSIONS(?:\s*\(TNEA\))?\s*-\s*(\d{4})", re.IGNORECASE)
ROUND_RE = re.compile(r"ROUND\s+(\d+)", re.IGNORECASE)
PAGE_OF_RE = re.compile(r"Page\s+(\d+)\s+of\s+(\d+)", re.IGNORECASE)
PATH_ROUND_RE = re.compile(r"\b\d{4}-(\d+)\b")
COMMUNITY_VALUES = {
    "OC",
    "BC",
    "BCM",
    "MBC",
    "MBCV",
    "MBCDNC",
    "SC",
    "SCA",
    "ST",
}
COMMUNITY_NORMALIZATION = {
    "MBCDNC": "MBC",
    "MBCV": "MBC",
    "SCA": "SC",
}
BUNDLES_DIRNAME = "bundles"
MERGED_DIRNAME = "merged"
REPORTS_DIRNAME = "reports"
LEGACY_OUTPUT_DIRNAME = "organized_output"
ORDINAL_ROUNDS = {
    "FIRST": "1",
    "SECOND": "2",
    "THIRD": "3",
    "FOURTH": "4",
}


@dataclass
class ParsedRecord:
    layout_type: str
    s_no: str
    appln_no: str
    candidate_name: str
    dob: str
    community: str
    aggregate_mark: str
    rank: str
    college_code: str
    branch_code: str
    allotted_category: str


STANDARDIZED_HEADERS = [
    "S NO",
    "APPLICATION NUMBER",
    "NAME OF THE CANDIDATE",
    "AGGREGATE MARK",
    "RANK",
    "COMMUNITY",
    "COLLEGE CODE",
    "BRANCH CODE",
    "ALLOTTED CATEGORY",
]


def compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run_pdftotext(pdf_path: Path) -> str:
    if shutil.which("pdftotext") is None:
        raise RuntimeError("`pdftotext` is required but not installed.")

    proc = subprocess.run(
        ["pdftotext", "-layout", str(pdf_path), "-"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.stdout


def split_pages(full_text: str) -> list[str]:
    pages = [page.rstrip("\n") for page in full_text.split("\f")]
    return [page for page in pages if page.strip()]


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def extract_title_line(lines: Iterable[str]) -> str:
    for line in lines:
        if "PROVISIONAL ALLOTMENT LIST" in line.upper():
            return normalize_space(line)
    return ""


def infer_year(first_page_lines: list[str], pdf_path: Path) -> str:
    for line in first_page_lines[:6]:
        match = YEAR_RE.search(line)
        if match:
            return match.group(1)

    for part in pdf_path.parts:
        if re.fullmatch(r"\d{4}", part):
            return part

    return "unknown_year"


def infer_round(title_line: str, pdf_path: Path) -> str:
    for source in (title_line, str(pdf_path)):
        match = ROUND_RE.search(source)
        if match:
            return match.group(1)
        ordinal_match = re.search(r"\b(FIRST|SECOND|THIRD|FOURTH)\s+ROUND\b", source, re.IGNORECASE)
        if ordinal_match:
            return ORDINAL_ROUNDS[ordinal_match.group(1).upper()]
        path_match = PATH_ROUND_RE.search(source)
        if path_match:
            return path_match.group(1)
    return "unknown_round"


def classify_line(text: str, page_number: int) -> str:
    stripped = text.strip()
    normalized = normalize_space(stripped).upper()

    if not stripped:
        return "blank"
    if PAGE_OF_RE.fullmatch(stripped):
        return "footer_page_of"
    if stripped.isdigit() and stripped == str(page_number):
        return "footer_page_number"
    if "TAMILNADU ENGINEERING ADMISSIONS" in normalized:
        return "header_title"
    if "DIRECTORATE OF TECHNICAL EDUCATION" in normalized:
        return "header_department"
    if "PROVISIONAL ALLOTMENT LIST" in normalized:
        return "header_allotment"
    if normalized.startswith("S NO"):
        return "header_columns"
    if "APPLICATION" in normalized and "NUMBER" not in normalized:
        return "header_columns"
    if "AGGREGATE" in normalized or "ALLOTTED" in normalized or "COLLEGE" in normalized:
        return "header_columns"
    if "MARK" in normalized or "RANK" in normalized or "COMMUNITY" in normalized:
        return "header_columns"
    if normalized == "NUMBER":
        return "header_columns"
    return "other"


def parse_record(record_text: str) -> ParsedRecord:
    compact = normalize_space(record_text)

    patterns: list[tuple[str, re.Pattern[str]]] = [
        (
            "name_with_dob",
            re.compile(
                r"^\s*(\d+)\s+(\d{6})\s+(.+?)\s+(\d{2}-\d{2}-\d{4})\s+([A-Z]+)\s+"
                r"(\d+(?:\.\d+)?)\s+(\d+[A-Z]*)\s+(\d+)\s+([A-Z]+)\s+([A-Z]+)\s*$"
            ),
        ),
        (
            "no_name_mark_first",
            re.compile(
                r"^\s*(\d+)\s+(\d{6})\s+(\d+(?:\.\d+)?)\s+(\d+[A-Z]*)\s+([A-Z]+)\s+"
                r"(\d+)\s+([A-Z]+)\s+([A-Z]+)\s*$"
            ),
        ),
        (
            "no_name_community_first",
            re.compile(
                r"^\s*(\d+)\s+(\d{6})\s+([A-Z]+)\s+(\d+(?:\.\d+)?)\s+(\d+[A-Z]*)\s+"
                r"(\d+)\s+([A-Z]+)\s+([A-Z]+)\s*$"
            ),
        ),
        (
            "name_without_dob",
            re.compile(
                r"^\s*(\d+)\s+(\d{6})\s+(.+?)\s+(\d+(?:\.\d+)?)\s+(\d+[A-Z]*)\s+"
                r"([A-Z]+)\s+(\d+)\s+([A-Z]+)\s+([A-Z]+)\s*$"
            ),
        ),
    ]

    for layout_type, pattern in patterns:
        match = pattern.match(compact)
        if not match:
            continue

        groups = match.groups()
        if layout_type == "name_with_dob":
            return ParsedRecord(
                layout_type=layout_type,
                s_no=groups[0],
                appln_no=groups[1],
                candidate_name=groups[2],
                dob=groups[3],
                community=groups[4],
                aggregate_mark=groups[5],
                rank=groups[6],
                college_code=groups[7],
                branch_code=groups[8],
                allotted_category=groups[9],
            )

        if layout_type == "no_name_mark_first":
            return ParsedRecord(
                layout_type=layout_type,
                s_no=groups[0],
                appln_no=groups[1],
                candidate_name="",
                dob="",
                community=groups[4],
                aggregate_mark=groups[2],
                rank=groups[3],
                college_code=groups[5],
                branch_code=groups[6],
                allotted_category=groups[7],
            )

        if layout_type == "no_name_community_first":
            return ParsedRecord(
                layout_type=layout_type,
                s_no=groups[0],
                appln_no=groups[1],
                candidate_name="",
                dob="",
                community=groups[2],
                aggregate_mark=groups[3],
                rank=groups[4],
                college_code=groups[5],
                branch_code=groups[6],
                allotted_category=groups[7],
            )

        return ParsedRecord(
            layout_type=layout_type,
            s_no=groups[0],
            appln_no=groups[1],
            candidate_name=groups[2],
            dob="",
            community=groups[5],
            aggregate_mark=groups[3],
            rank=groups[4],
            college_code=groups[6],
            branch_code=groups[7],
            allotted_category=groups[8],
        )

    tokens = compact.split()
    if len(tokens) >= 8 and MARK_RE.match(tokens[2]) and RANK_RE.match(tokens[3]):
        return ParsedRecord(
            layout_type="no_name_mark_first_fallback",
            s_no=tokens[0],
            appln_no=tokens[1],
            candidate_name="",
            dob="",
            community=tokens[4],
            aggregate_mark=tokens[2],
            rank=tokens[3],
            college_code=tokens[5],
            branch_code=tokens[6],
            allotted_category=tokens[7],
        )

    if len(tokens) >= 8 and MARK_RE.match(tokens[3]) and RANK_RE.match(tokens[4]):
        return ParsedRecord(
            layout_type="no_name_community_first_fallback",
            s_no=tokens[0],
            appln_no=tokens[1],
            candidate_name="",
            dob="",
            community=tokens[2],
            aggregate_mark=tokens[3],
            rank=tokens[4],
            college_code=tokens[5],
            branch_code=tokens[6],
            allotted_category=tokens[7],
        )

    token_parsed = parse_record_by_tokens(compact)
    if token_parsed is not None:
        return token_parsed

    raise ValueError(f"Unrecognized record layout: {compact}")


def is_mark_token(token: str) -> bool:
    return bool(MARK_RE.fullmatch(token))


def is_rank_token(token: str) -> bool:
    return bool(RANK_RE.fullmatch(token))


def is_community_token(token: str) -> bool:
    return token.upper() in COMMUNITY_VALUES


def split_trailing_mark(token: str) -> tuple[str, str] | None:
    match = re.match(r"^(.*?)(\d+(?:\.\d+)?)$", token)
    if match and match.group(1):
        prefix = match.group(1)
        mark = match.group(2)
        if 100 <= float(mark) <= 200:
            return prefix, mark

    heuristic = re.match(r"^(\d)([A-Za-z.]+)(\d{2,3}\.\d+)$", token)
    if heuristic:
        candidate_mark = heuristic.group(1) + heuristic.group(3)
        if 100 <= float(candidate_mark) <= 200:
            return heuristic.group(2), candidate_mark

    return None


def try_triplet(tokens: list[str], order: tuple[str, str, str]) -> dict[str, str] | None:
    if len(tokens) != 3:
        return None

    values: dict[str, str] = {}
    for token, role in zip(tokens, order, strict=True):
        if role == "community":
            if not is_community_token(token):
                return None
        elif role == "mark":
            if not is_mark_token(token):
                return None
        elif role == "rank":
            if not is_rank_token(token):
                return None
        values[role] = token
    return values


def normalize_token(token: str) -> str:
    time_like = re.fullmatch(r"(\d+):00", token)
    if time_like:
        return time_like.group(1)
    return token


def parse_record_by_tokens(compact: str) -> ParsedRecord | None:
    tokens = [normalize_token(token) for token in compact.split()]
    if len(tokens) < 8:
        return None
    if not tokens[0].isdigit() or not re.fullmatch(r"\d{6}", tokens[1]):
        return None
    if not tokens[-3].isdigit():
        return None

    s_no = tokens[0]
    appln_no = tokens[1]
    college_code = tokens[-3]
    branch_code = tokens[-2]
    allotted_category = tokens[-1]
    middle = tokens[2:-3]

    if not middle:
        return None

    dob_index = next((index for index, token in enumerate(middle) if DATE_RE.fullmatch(token)), None)
    if dob_index is not None:
        candidate_name = " ".join(middle[:dob_index])
        dob = middle[dob_index]
        tail = middle[dob_index + 1 :]
        for layout_type, order in [
            ("name_with_dob", ("community", "mark", "rank")),
            ("name_with_dob_mark_first", ("mark", "community", "rank")),
        ]:
            parsed = try_triplet(tail, order)
            if parsed is None:
                continue
            return ParsedRecord(
                layout_type=layout_type,
                s_no=s_no,
                appln_no=appln_no,
                candidate_name=candidate_name,
                dob=dob,
                community=parsed["community"],
                aggregate_mark=parsed["mark"],
                rank=parsed["rank"],
                college_code=college_code,
                branch_code=branch_code,
                allotted_category=allotted_category,
            )
        for layout_type, order in [
            ("name_with_dob_missing_rank", ("community", "mark")),
            ("name_with_dob_mark_first_missing_rank", ("mark", "community")),
        ]:
            if len(tail) != 2:
                continue
            values: dict[str, str] = {}
            matched = True
            for token, role in zip(tail, order, strict=True):
                if role == "community" and not is_community_token(token):
                    matched = False
                    break
                if role == "mark" and not is_mark_token(token):
                    matched = False
                    break
                values[role] = token
            if not matched:
                continue
            return ParsedRecord(
                layout_type=layout_type,
                s_no=s_no,
                appln_no=appln_no,
                candidate_name=candidate_name,
                dob=dob,
                community=values["community"],
                aggregate_mark=values["mark"],
                rank="",
                college_code=college_code,
                branch_code=branch_code,
                allotted_category=allotted_category,
            )
        return None

    if len(middle) == 3:
        for layout_type, order in [
            ("no_name_community_first", ("community", "mark", "rank")),
            ("no_name_mark_first", ("mark", "rank", "community")),
        ]:
            parsed = try_triplet(middle, order)
            if parsed is None:
                continue
            return ParsedRecord(
                layout_type=layout_type,
                s_no=s_no,
                appln_no=appln_no,
                candidate_name="",
                dob="",
                community=parsed["community"],
                aggregate_mark=parsed["mark"],
                rank=parsed["rank"],
                college_code=college_code,
                branch_code=branch_code,
                allotted_category=allotted_category,
            )

    if len(middle) >= 3:
        parsed = try_triplet(middle[-3:], ("community", "mark", "rank"))
        if parsed is not None:
            return ParsedRecord(
                layout_type="name_without_dob_community_mark_rank",
                s_no=s_no,
                appln_no=appln_no,
                candidate_name=" ".join(middle[:-3]),
                dob="",
                community=parsed["community"],
                aggregate_mark=parsed["mark"],
                rank=parsed["rank"],
                college_code=college_code,
                branch_code=branch_code,
                allotted_category=allotted_category,
            )

    if len(middle) >= 3:
        parsed = try_triplet(middle[-3:], ("community", "rank", "mark"))
        if parsed is not None:
            return ParsedRecord(
                layout_type="name_without_dob_community_rank_mark",
                s_no=s_no,
                appln_no=appln_no,
                candidate_name=" ".join(middle[:-3]),
                dob="",
                community=parsed["community"],
                aggregate_mark=parsed["mark"],
                rank=parsed["rank"],
                college_code=college_code,
                branch_code=branch_code,
                allotted_category=allotted_category,
            )

    if len(middle) >= 2 and is_rank_token(middle[-2]) and is_community_token(middle[-1]):
        prefix_tokens = middle[:-2]
        for index in range(len(prefix_tokens) - 1, -1, -1):
            token = prefix_tokens[index]
            mark = ""
            name_piece = ""
            if is_mark_token(token):
                mark = token
            else:
                split_mark = split_trailing_mark(token)
                if split_mark is None:
                    continue
                name_piece, mark = split_mark
            candidate_name_tokens = prefix_tokens[:index]
            if name_piece:
                candidate_name_tokens.append(name_piece)
            candidate_name_tokens.extend(prefix_tokens[index + 1 :])
            return ParsedRecord(
                layout_type="name_without_dob_mark_rank_community_fallback",
                s_no=s_no,
                appln_no=appln_no,
                candidate_name=" ".join(candidate_name_tokens),
                dob="",
                community=middle[-1],
                aggregate_mark=mark,
                rank=middle[-2],
                college_code=college_code,
                branch_code=branch_code,
                allotted_category=allotted_category,
            )

    return None


def derive_bundle_dir(output_root: Path, pdf_path: Path, year: str, round_number: str) -> Path:
    round_dir = f"round_{round_number}" if round_number.isdigit() else round_number
    bundle_name = f"{year}__{round_dir}__{pdf_path.stem}"
    return output_root / BUNDLES_DIRNAME / bundle_name


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def remove_if_exists(path: Path) -> None:
    if path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    ensure_dir(path.parent)
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize_round_value(raw_round: str) -> str:
    round_match = re.fullmatch(r"round_(\d+)", raw_round, re.IGNORECASE)
    if round_match:
        return round_match.group(1)
    digits_match = re.search(r"(\d+)", raw_round)
    if digits_match:
        return digits_match.group(1)
    return raw_round


def normalize_community_label(value: str) -> str:
    return COMMUNITY_NORMALIZATION.get(value, value)


def legacy_output_roots(output_root: Path) -> list[Path]:
    roots: list[Path] = []
    if output_root.name == LEGACY_OUTPUT_DIRNAME and output_root.exists():
        roots.append(output_root)
    candidate = output_root / LEGACY_OUTPUT_DIRNAME
    if candidate.exists():
        roots.append(candidate)
    return roots


def load_bundle_manifest(meta_path: Path) -> dict[str, str]:
    with meta_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Expected an object in {meta_path}")
    return {str(key): str(value) for key, value in payload.items()}


def collect_records_sources(output_root: Path) -> list[tuple[Path, str, str]]:
    output_root = output_root.resolve()
    candidates_by_source: dict[str, tuple[tuple[int, int, int], Path, str, str]] = {}
    seen_paths: set[Path] = set()

    def consider_candidate(records_path: Path, manifest: dict[str, str]) -> None:
        records_resolved = records_path.resolve()
        if records_resolved in seen_paths:
            return
        seen_paths.add(records_resolved)

        source_key = manifest.get("source_pdf_rel_path") or manifest.get("source_pdf_abs_path")
        if not source_key:
            source_key = str(records_resolved)

        raw_round = manifest.get("pdf_round", "")
        unknown_round_flag = 1 if raw_round.lower() in {"", "unknown_round"} else 0
        try:
            parse_error_blocks = int(manifest.get("parse_error_blocks", "0") or "0")
        except ValueError:
            parse_error_blocks = 0
        try:
            record_rows = int(manifest.get("record_rows", "0") or "0")
        except ValueError:
            record_rows = 0

        score = (unknown_round_flag, parse_error_blocks, -record_rows)
        candidate = (
            score,
            records_resolved,
            manifest.get("pdf_year", ""),
            raw_round,
        )
        current = candidates_by_source.get(source_key)
        if current is None or score < current[0]:
            candidates_by_source[source_key] = candidate

    bundles_root = output_root / BUNDLES_DIRNAME
    if bundles_root.exists():
        for bundle_dir in sorted(path for path in bundles_root.iterdir() if path.is_dir()):
            records_path = bundle_dir / "records.csv"
            meta_path = bundle_dir / "meta.json"
            if not records_path.exists() or not meta_path.exists():
                continue
            manifest = load_bundle_manifest(meta_path)
            consider_candidate(records_path, manifest)

    for legacy_root in legacy_output_roots(output_root):
        for records_path in sorted(legacy_root.glob("*/*/*/csv/records.csv")):
            meta_path = records_path.parents[1] / "meta.json"
            if not meta_path.exists():
                continue
            manifest = load_bundle_manifest(meta_path)
            consider_candidate(records_path, manifest)

    sources = [
        (records_path, year, raw_round)
        for _score, records_path, year, raw_round in candidates_by_source.values()
    ]
    sources.sort(key=lambda item: (item[1], normalize_round_value(item[2]), str(item[0])))
    return sources


def load_college_codes_for_year(output_root: Path, year: str) -> set[str]:
    codes: set[str] = set()
    for records_path, pdf_year, _raw_round in collect_records_sources(output_root):
        if pdf_year != year:
            continue
        with records_path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                code = row.get("COLLEGE CODE", "").strip()
                if code:
                    codes.add(code)
    return codes


def load_college_codes_from_json(reference_path: Path) -> set[str]:
    with reference_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise RuntimeError(f"Expected a list of colleges in {reference_path}")

    codes: set[str] = set()
    for item in data:
        if not isinstance(item, dict):
            continue
        code = str(item.get("College_Code", "")).strip()
        if code:
            codes.add(code)
    return codes


def merge_clean_csvs(
    output_root: Path,
    destination: Path | None = None,
    *,
    drop_abnormal_ranks: bool = False,
    normalize_communities: bool = False,
    retain_only_college_codes_from_year: str | None = None,
    retain_only_college_codes_from_json: Path | None = None,
) -> Path:
    output_root = output_root.resolve()
    if (
        retain_only_college_codes_from_year is not None
        and retain_only_college_codes_from_json is not None
    ):
        raise RuntimeError(
            "Use only one college-code filter source: year or JSON reference file"
        )
    allowed_college_codes: set[str] | None = None
    if retain_only_college_codes_from_year is not None:
        allowed_college_codes = load_college_codes_for_year(
            output_root, retain_only_college_codes_from_year
        )
        if not allowed_college_codes:
            raise RuntimeError(
                "No college codes found for "
                f"{retain_only_college_codes_from_year} under {output_root}"
            )
    if retain_only_college_codes_from_json is not None:
        retain_only_college_codes_from_json = retain_only_college_codes_from_json.resolve()
        allowed_college_codes = load_college_codes_from_json(
            retain_only_college_codes_from_json
        )
        if not allowed_college_codes:
            raise RuntimeError(
                f"No college codes found in JSON reference {retain_only_college_codes_from_json}"
            )
    if destination is None:
        if retain_only_college_codes_from_json is not None:
            filename = "merged_records_all_years_rounds_cleaned_reference_colleges_only.csv"
        elif retain_only_college_codes_from_year is not None:
            filename = (
                "merged_records_all_years_rounds_cleaned_"
                f"{retain_only_college_codes_from_year}_colleges_only.csv"
            )
        elif drop_abnormal_ranks or normalize_communities:
            filename = "merged_records_all_years_rounds_cleaned.csv"
        else:
            filename = "merged_records_all_years_rounds.csv"
        destination = output_root / MERGED_DIRNAME / filename
    else:
        destination = destination.resolve()

    merged_rows: list[dict[str, str]] = []
    records_sources = collect_records_sources(output_root)

    for records_path, year, raw_round in records_sources:
        round_value = normalize_round_value(raw_round)

        with records_path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                merged_row = {
                    "YEAR": year,
                    "ROUND": round_value,
                    "S NO": row.get("S NO", ""),
                    "APPLICATION NUMBER": row.get("APPLICATION NUMBER", ""),
                    "NAME OF THE CANDIDATE": row.get("NAME OF THE CANDIDATE", ""),
                    "AGGREGATE MARK": row.get("AGGREGATE MARK", ""),
                    "RANK": row.get("RANK", "").strip(),
                    "COMMUNITY": row.get("COMMUNITY", "").strip(),
                    "COLLEGE CODE": row.get("COLLEGE CODE", ""),
                    "BRANCH CODE": row.get("BRANCH CODE", ""),
                    "ALLOTTED CATEGORY": row.get("ALLOTTED CATEGORY", "").strip(),
                }
                if drop_abnormal_ranks and not merged_row["RANK"].isdigit():
                    continue
                if normalize_communities:
                    merged_row["COMMUNITY"] = normalize_community_label(merged_row["COMMUNITY"])
                    merged_row["ALLOTTED CATEGORY"] = normalize_community_label(
                        merged_row["ALLOTTED CATEGORY"]
                    )
                if (
                    allowed_college_codes is not None
                    and merged_row["COLLEGE CODE"].strip() not in allowed_college_codes
                ):
                    continue
                merged_rows.append(merged_row)

    if not merged_rows:
        raise RuntimeError(f"No per-round records.csv files found under {output_root}")

    write_csv(
        destination,
        merged_rows,
        ["YEAR", "ROUND", *STANDARDIZED_HEADERS],
    )
    return destination


def parse_pdf(
    pdf_path: Path,
    output_root: Path,
    input_root: Path,
    max_pages: int | None = None,
    copy_source: bool = False,
    with_audit_files: bool = False,
) -> dict[str, str | int]:
    raw_text = run_pdftotext(pdf_path)
    pages = split_pages(raw_text)
    if max_pages is not None:
        pages = pages[:max_pages]

    if not pages:
        raise RuntimeError(f"No text extracted from {pdf_path}")

    first_page_lines = [line.rstrip() for line in pages[0].splitlines() if line.strip()]
    title_line = extract_title_line(first_page_lines)
    year = infer_year(first_page_lines, pdf_path)
    round_number = infer_round(title_line, pdf_path)
    bundle_dir = derive_bundle_dir(output_root, pdf_path, year, round_number)
    audit_dir = bundle_dir / "audit"
    source_dir = bundle_dir / "source"
    ensure_dir(bundle_dir)
    if with_audit_files:
        ensure_dir(audit_dir)
    if copy_source:
        ensure_dir(source_dir)

    for stale_path in [
        bundle_dir / "records.csv",
        bundle_dir / "manifest.csv",
        audit_dir / "records_full.csv",
        audit_dir / "pages.csv",
        audit_dir / "unparsed_lines.csv",
        bundle_dir / "meta.json",
    ]:
        remove_if_exists(stale_path)
    if not with_audit_files:
        remove_if_exists(audit_dir)
    if not copy_source:
        remove_if_exists(source_dir)

    relative_source = str(pdf_path.resolve())
    try:
        relative_source = str(pdf_path.resolve().relative_to(input_root.resolve()))
    except ValueError:
        relative_source = str(pdf_path.resolve())

    file_size_bytes = pdf_path.stat().st_size
    sha256 = compute_sha256(pdf_path)

    page_rows: list[dict[str, str]] = []
    clean_rows: list[dict[str, str]] = []
    full_record_rows: list[dict[str, str]] = []
    unparsed_rows: list[dict[str, str]] = []

    layout_types: set[str] = set()
    parse_error_count = 0
    total_record_blocks = 0

    for page_number, page_text in enumerate(pages, start=1):
        lines = page_text.splitlines()
        carry_name_lines: list[str] = []
        record_start_indexes = [
            index
            for index, line in enumerate(lines)
            if RECORD_START_RE.match(line)
        ]
        assigned_indexes: set[int] = set()

        for block_pos, start_index in enumerate(record_start_indexes):
            end_index = (
                record_start_indexes[block_pos + 1]
                if block_pos + 1 < len(record_start_indexes)
                else len(lines)
            )
            raw_lines: list[str] = []
            raw_line_numbers: list[int] = []

            for line_index in range(start_index, end_index):
                line = lines[line_index]
                if not line.strip():
                    continue
                classification = classify_line(line, page_number)
                if line_index != start_index and classification.startswith("footer_"):
                    continue
                if line_index != start_index and classification.startswith("header_"):
                    continue
                raw_lines.append(line.rstrip())
                raw_line_numbers.append(line_index + 1)

            if not raw_lines:
                continue

            total_record_blocks += 1
            data_lines = [line for line in raw_lines if any(char.isdigit() for char in line)]
            name_only_lines = [
                normalize_space(line)
                for line in raw_lines
                if not any(char.isdigit() for char in line)
            ]
            parse_lines = data_lines or raw_lines
            raw_record_text = "\n".join(parse_lines)
            normalized_record_text = normalize_space(raw_record_text)

            try:
                parsed = parse_record(raw_record_text)
                leading_name = " ".join(carry_name_lines).strip()
                current_name = parsed.candidate_name.strip()
                if leading_name:
                    current_name = f"{leading_name} {current_name}".strip()
                if current_name:
                    carry_name_lines = name_only_lines
                else:
                    current_name = " ".join(carry_name_lines + name_only_lines).strip()
                    carry_name_lines = []
                parsed.candidate_name = current_name
                layout_types.add(parsed.layout_type)
                clean_rows.append(
                    {
                        "S NO": parsed.s_no,
                        "APPLICATION NUMBER": parsed.appln_no,
                        "NAME OF THE CANDIDATE": parsed.candidate_name,
                        "AGGREGATE MARK": parsed.aggregate_mark,
                        "RANK": parsed.rank,
                        "COMMUNITY": parsed.community,
                        "COLLEGE CODE": parsed.college_code,
                        "BRANCH CODE": parsed.branch_code,
                        "ALLOTTED CATEGORY": parsed.allotted_category,
                    }
                )
                full_record_rows.append(
                    {
                        "source_pdf_abs_path": str(pdf_path.resolve()),
                        "source_pdf_rel_path": relative_source,
                        "pdf_sha256": sha256,
                        "file_size_bytes": str(file_size_bytes),
                        "pdf_year": year,
                        "pdf_round": round_number,
                        "title_line": title_line,
                        "page_number": str(page_number),
                        "record_sequence": str(len(full_record_rows) + 1),
                        "s_no": parsed.s_no,
                        "appln_no": parsed.appln_no,
                        "candidate_name": parsed.candidate_name,
                        "dob": parsed.dob,
                        "community": parsed.community,
                        "aggregate_mark": parsed.aggregate_mark,
                        "rank": parsed.rank,
                        "college_code": parsed.college_code,
                        "branch_code": parsed.branch_code,
                        "allotted_category": parsed.allotted_category,
                        "layout_type": parsed.layout_type,
                        "record_line_numbers": ",".join(str(n) for n in raw_line_numbers),
                        "raw_record_text": raw_record_text,
                        "normalized_record_text": normalized_record_text,
                    }
                )
                assigned_indexes.update(line_number - 1 for line_number in raw_line_numbers)
            except ValueError as exc:
                parse_error_count += 1
                for line_number, line in zip(raw_line_numbers, raw_lines, strict=True):
                    unparsed_rows.append(
                        {
                            "source_pdf_abs_path": str(pdf_path.resolve()),
                            "source_pdf_rel_path": relative_source,
                            "pdf_sha256": sha256,
                            "pdf_year": year,
                            "pdf_round": round_number,
                            "page_number": str(page_number),
                            "line_number": str(line_number),
                            "classification": "parse_error",
                            "text": line,
                            "error": str(exc),
                        }
                    )
                assigned_indexes.update(line_number - 1 for line_number in raw_line_numbers)

        for carry_line in carry_name_lines:
            unparsed_rows.append(
                {
                    "source_pdf_abs_path": str(pdf_path.resolve()),
                    "source_pdf_rel_path": relative_source,
                    "pdf_sha256": sha256,
                    "pdf_year": year,
                    "pdf_round": round_number,
                    "page_number": str(page_number),
                    "line_number": "",
                    "classification": "dangling_name_continuation",
                    "text": carry_line,
                    "error": "",
                }
            )

        for line_index, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            if line_index - 1 in assigned_indexes:
                continue
            unparsed_rows.append(
                {
                    "source_pdf_abs_path": str(pdf_path.resolve()),
                    "source_pdf_rel_path": relative_source,
                    "pdf_sha256": sha256,
                    "pdf_year": year,
                    "pdf_round": round_number,
                    "page_number": str(page_number),
                    "line_number": str(line_index),
                    "classification": classify_line(line, page_number),
                    "text": line.rstrip(),
                    "error": "",
                }
            )

        page_rows.append(
            {
                "source_pdf_abs_path": str(pdf_path.resolve()),
                "source_pdf_rel_path": relative_source,
                "pdf_sha256": sha256,
                "pdf_year": year,
                "pdf_round": round_number,
                "page_number": str(page_number),
                "title_line": title_line,
                "raw_page_text": page_text,
            }
        )

    if copy_source:
        shutil.copy2(pdf_path, source_dir / pdf_path.name)

    manifest = {
        "source_pdf_abs_path": str(pdf_path.resolve()),
        "source_pdf_rel_path": relative_source,
        "pdf_sha256": sha256,
        "file_size_bytes": str(file_size_bytes),
        "pdf_year": year,
        "pdf_round": round_number,
        "title_line": title_line,
        "bundle_dir": str(bundle_dir.resolve()),
        "pages_extracted": str(len(page_rows)),
        "record_rows": str(len(clean_rows)),
        "record_blocks_seen": str(total_record_blocks),
        "parse_error_blocks": str(parse_error_count),
        "unparsed_nonblank_lines": str(len(unparsed_rows)),
        "layout_types": ",".join(sorted(layout_types)),
        "clean_csv_path": str((bundle_dir / "records.csv").resolve()),
        "audit_files_written": str(with_audit_files),
    }

    write_csv(
        bundle_dir / "records.csv",
        clean_rows,
        STANDARDIZED_HEADERS,
    )
    write_csv(bundle_dir / "manifest.csv", [manifest], list(manifest.keys()))

    if with_audit_files:
        write_csv(
            audit_dir / "records_full.csv",
            full_record_rows,
            [
                "source_pdf_abs_path",
                "source_pdf_rel_path",
                "pdf_sha256",
                "file_size_bytes",
                "pdf_year",
                "pdf_round",
                "title_line",
                "page_number",
                "record_sequence",
                "s_no",
                "appln_no",
                "candidate_name",
                "dob",
                "community",
                "aggregate_mark",
                "rank",
                "college_code",
                "branch_code",
                "allotted_category",
                "layout_type",
                "record_line_numbers",
                "raw_record_text",
                "normalized_record_text",
            ],
        )
        write_csv(
            audit_dir / "pages.csv",
            page_rows,
            [
                "source_pdf_abs_path",
                "source_pdf_rel_path",
                "pdf_sha256",
                "pdf_year",
                "pdf_round",
                "page_number",
                "title_line",
                "raw_page_text",
            ],
        )
        write_csv(
            audit_dir / "unparsed_lines.csv",
            unparsed_rows,
            [
                "source_pdf_abs_path",
                "source_pdf_rel_path",
                "pdf_sha256",
                "pdf_year",
                "pdf_round",
                "page_number",
                "line_number",
                "classification",
                "text",
                "error",
            ],
        )

    with (bundle_dir / "meta.json").open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")

    return {
        "source_pdf": str(pdf_path),
        "bundle_dir": str(bundle_dir),
        "pages_extracted": len(page_rows),
        "record_rows": len(clean_rows),
        "record_blocks_seen": total_record_blocks,
        "parse_error_blocks": parse_error_count,
        "unparsed_nonblank_lines": len(unparsed_rows),
    }


def run_batch(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    pdf_files = sorted(path for path in root.rglob("*.pdf") if path.is_file())
    if not pdf_files:
        print(f"No PDFs found under {root}", file=sys.stderr)
        return 1

    summary_rows: list[dict[str, str]] = []
    failed = False

    for pdf_path in pdf_files:
        try:
            result = parse_pdf(
                pdf_path=pdf_path,
                output_root=args.output_root.resolve(),
                input_root=root,
                max_pages=args.max_pages,
                copy_source=args.copy_source,
                with_audit_files=args.with_audit_files,
            )
            summary_rows.append({key: str(value) for key, value in result.items()})
            print(
                f"Parsed {pdf_path} -> {result['bundle_dir']} "
                f"({result['record_rows']} records, {result['parse_error_blocks']} parse-error blocks)"
            )
        except Exception as exc:  # noqa: BLE001
            failed = True
            summary_rows.append(
                {
                    "source_pdf": str(pdf_path),
                    "bundle_dir": "",
                    "pages_extracted": "",
                    "record_rows": "",
                    "record_blocks_seen": "",
                    "parse_error_blocks": "",
                    "unparsed_nonblank_lines": "",
                    "error": str(exc),
                }
            )
            print(f"Failed {pdf_path}: {exc}", file=sys.stderr)

    summary_path = args.output_root.resolve() / REPORTS_DIRNAME / "batch_manifest.csv"
    fieldnames = [
        "source_pdf",
        "bundle_dir",
        "pages_extracted",
        "record_rows",
        "record_blocks_seen",
        "parse_error_blocks",
        "unparsed_nonblank_lines",
        "error",
    ]
    normalized_summary = []
    for row in summary_rows:
        normalized = {field: row.get(field, "") for field in fieldnames}
        normalized_summary.append(normalized)
    write_csv(summary_path, normalized_summary, fieldnames)
    merged_path = merge_clean_csvs(args.output_root.resolve())
    cleaned_merged_path = merge_clean_csvs(
        args.output_root.resolve(),
        drop_abnormal_ranks=True,
        normalize_communities=True,
    )
    filtered_merged_path = merge_clean_csvs(
        args.output_root.resolve(),
        drop_abnormal_ranks=True,
        normalize_communities=True,
        retain_only_college_codes_from_year="2025",
    )
    print(f"Merged CSV -> {merged_path}")
    print(f"Cleaned merged CSV -> {cleaned_merged_path}")
    print(f"2025-colleges-only merged CSV -> {filtered_merged_path}")

    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Parse TNEA allotment PDFs into loss-preserving CSV bundles with "
            "structured records, raw page text, and unparsed line capture."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_cmd = subparsers.add_parser("parse", help="Parse a single PDF")
    parse_cmd.add_argument("pdf", type=Path, help="Path to the PDF file")
    parse_cmd.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/processed"),
        help="Root folder for processed bundles, merged files, and reports",
    )
    parse_cmd.add_argument(
        "--input-root",
        type=Path,
        default=Path("data/raw"),
        help="Base path used for relative source-path reporting",
    )
    parse_cmd.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional page limit for smoke tests",
    )
    parse_cmd.add_argument(
        "--copy-source",
        action="store_true",
        help="Copy the source PDF into each organized bundle",
    )
    parse_cmd.add_argument(
        "--with-audit-files",
        action="store_true",
        help="Also write raw/audit files with full extracted text and parse traces",
    )

    batch_cmd = subparsers.add_parser("batch", help="Parse every PDF under a folder")
    batch_cmd.add_argument(
        "root",
        type=Path,
        nargs="?",
        default=Path("data/raw"),
        help="Root folder to scan recursively for PDFs",
    )
    batch_cmd.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/processed"),
        help="Root folder for processed bundles, merged files, and reports",
    )
    batch_cmd.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Optional page limit per PDF for smoke tests",
    )
    batch_cmd.add_argument(
        "--copy-source",
        action="store_true",
        help="Copy each source PDF into its organized bundle",
    )
    batch_cmd.add_argument(
        "--with-audit-files",
        action="store_true",
        help="Also write raw/audit files with full extracted text and parse traces",
    )

    merge_cmd = subparsers.add_parser("merge", help="Merge all clean per-round CSVs into one file")
    merge_cmd.add_argument(
        "--output-root",
        type=Path,
        default=Path("data/processed"),
        help="Root folder containing processed bundles, merged files, and reports",
    )
    merge_cmd.add_argument(
        "--destination",
        type=Path,
        default=None,
        help="Optional explicit path for the merged CSV file",
    )
    merge_cmd.add_argument(
        "--clean",
        action="store_true",
        help=(
            "Drop rows with non-numeric ranks and normalize MBCDNC/MBCV to MBC "
            "and SCA to SC in COMMUNITY and ALLOTTED CATEGORY"
        ),
    )
    merge_cmd.add_argument(
        "--retain-only-college-codes-from-year",
        type=str,
        default=None,
        help=(
            "Keep only rows whose COLLEGE CODE exists in the given year's source data "
            "(for example, 2025)"
        ),
    )
    merge_cmd.add_argument(
        "--retain-only-college-codes-from-json",
        type=Path,
        default=None,
        help=(
            "Keep only rows whose COLLEGE CODE exists in the given JSON reference file "
            "containing College_Code entries"
        ),
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "parse":
        result = parse_pdf(
            pdf_path=args.pdf.resolve(),
            output_root=args.output_root.resolve(),
            input_root=args.input_root.resolve(),
            max_pages=args.max_pages,
            copy_source=args.copy_source,
            with_audit_files=args.with_audit_files,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "batch":
        return run_batch(args)

    if args.command == "merge":
        merged_path = merge_clean_csvs(
            output_root=args.output_root.resolve(),
            destination=args.destination,
            drop_abnormal_ranks=args.clean,
            normalize_communities=args.clean,
            retain_only_college_codes_from_year=args.retain_only_college_codes_from_year,
            retain_only_college_codes_from_json=args.retain_only_college_codes_from_json,
        )
        print(json.dumps({"merged_csv": str(merged_path)}, indent=2))
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
