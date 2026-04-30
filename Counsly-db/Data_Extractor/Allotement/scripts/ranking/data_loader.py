"""
Load and clean the data sources used by the ranking algorithm.

Inputs:
1. Cleaned allotment CSV
2. Filtered non-architecture college reference JSON
3. Raw college reference JSON for name recovery
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd

from .config import ALLOTMENT_CSV, COLLEGE_INFO_JSON, RAW_COLLEGE_INFO_JSON

logger = logging.getLogger(__name__)


def load_allotment_data(csv_path: Path | None = None) -> pd.DataFrame:
    """Load the training-ready allotment CSV into a normalized DataFrame."""
    path = csv_path or ALLOTMENT_CSV
    if not path.exists():
        raise FileNotFoundError(f"Allotment CSV not found: {path}")

    df = pd.read_csv(path, low_memory=False)
    df.columns = [c.strip().upper().replace(" ", "_") for c in df.columns]

    for col in ["RANK", "COLLEGE_CODE", "YEAR", "ROUND", "AGGREGATE_MARK"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["COLLEGE_CODE", "BRANCH_CODE", "COMMUNITY", "ALLOTTED_CATEGORY"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.upper()

    if "COLLEGE_CODE" in df.columns:
        numeric_codes = pd.to_numeric(df["COLLEGE_CODE"], errors="coerce")
        df = df[numeric_codes.notna()].copy()
        df["COLLEGE_CODE"] = numeric_codes[numeric_codes.notna()].astype(int).astype(str)

    if "COMMUNITY" in df.columns:
        df["COMMUNITY"] = df["COMMUNITY"].replace(
            {"MBCDNC": "MBC", "MBCV": "MBC", "SCA": "SC"}
        )

    logger.info(
        "Loaded allotment data: %s rows across %s colleges",
        len(df),
        df["COLLEGE_CODE"].nunique() if "COLLEGE_CODE" in df.columns else 0,
    )
    return df


def load_college_info(
    json_path: Path | None = None,
    raw_json_path: Path | None = None,
) -> pd.DataFrame:
    """Load the reference JSON and recover clean college-level metadata."""
    filtered_path = json_path or COLLEGE_INFO_JSON
    raw_path = raw_json_path or RAW_COLLEGE_INFO_JSON

    filtered_colleges = _load_json_list(filtered_path)
    raw_colleges = _load_json_list(raw_path) if raw_path.exists() else filtered_colleges

    raw_by_code = {
        str(item.get("College_Code", "")).strip(): item
        for item in raw_colleges
        if isinstance(item, dict)
    }
    clean_name_map = _build_clean_name_map(raw_colleges)

    records: list[dict] = []
    for college in filtered_colleges:
        if not isinstance(college, dict):
            continue

        code = str(college.get("College_Code", "")).strip()
        if not code:
            continue

        raw_ref = raw_by_code.get(code, college)
        placement_pct = _extract_percentage(college.get("Placement_Record", ""))
        if placement_pct is None:
            placement_pct = _extract_percentage(raw_ref.get("Placement_Record", ""))

        courses = college.get("courses", [])
        if not isinstance(courses, list):
            courses = []

        approved_intake_total = 0.0
        nba_count = 0
        branch_codes: list[str] = []
        valid_start_years: list[int] = []

        for course in courses:
            if not isinstance(course, dict):
                continue

            branch_code = str(course.get("Branch_Code", "")).strip().upper()
            if branch_code:
                branch_codes.append(branch_code)

            intake = pd.to_numeric(course.get("Approved_Intake", 0), errors="coerce")
            if pd.notna(intake):
                approved_intake_total += float(intake)

            year_start = pd.to_numeric(course.get("Year_Starting"), errors="coerce")
            if pd.notna(year_start) and int(year_start) > 1900:
                valid_start_years.append(int(year_start))

            if str(course.get("NBA_Accredited", "")).strip().lower() == "yes":
                nba_count += 1

        college_name = (
            clean_name_map.get(code)
            or _normalize_spaces(college.get("College_Name", ""))
            or code
        )
        district_raw = college.get("District", "") or raw_ref.get("District", "")
        website = _clean_url(college.get("Website", "") or raw_ref.get("Website", ""))

        records.append(
            {
                "college_code": code,
                "college_name": college_name,
                "district_raw": str(district_raw).strip(),
                "district_clean": _clean_district(str(district_raw)),
                "address": _normalize_spaces(college.get("Address", "") or raw_ref.get("Address", "")),
                "website": website,
                "minority_status": str(college.get("Minority_Status", "")).strip(),
                "placement_record": str(college.get("Placement_Record", "")).strip(),
                "placement_pct": placement_pct,
                "autonomous": str(college.get("Autonomous_Status", "")).strip(),
                "is_autonomous": (
                    str(college.get("Autonomous_Status", "")).strip().lower() == "autonomous"
                ),
                "hostel_boys": str(college.get("Hostel_Boys_Permanent_or_Rental", "")).strip(),
                "hostel_girls": str(college.get("Hostel_Girls_Permanent_or_Rental", "")).strip(),
                "mess_type": str(college.get("Type_of_Mess", "")).strip(),
                "transport": str(college.get("Transport_Facilities", "")).strip(),
                "num_branches": len(branch_codes),
                "approved_intake_total": approved_intake_total,
                "branches": branch_codes,
                "nba_accredited_count": nba_count,
                "nba_accredited_ratio": nba_count / len(courses) if courses else np.nan,
                "avg_year_starting": (
                    sum(valid_start_years) / len(valid_start_years)
                    if valid_start_years
                    else np.nan
                ),
            }
        )

    df = pd.DataFrame(records)
    logger.info("Loaded college info: %s colleges from %s", len(df), filtered_path)
    return df


def _load_json_list(path: Path) -> list[dict]:
    data = _load_json(path)
    if not isinstance(data, list):
        raise RuntimeError(f"Expected a list payload in {path}")
    return [item for item in data if isinstance(item, dict)]


def _load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _build_clean_name_map(raw_colleges: list[dict]) -> dict[str, str]:
    """
    Recover the true college name from the raw PDF-derived JSON.

    The current raw JSON stores the trailing remainder of the source PDF inside
    `College_Name`. We recover each college name by truncating that tail at the
    start of the next college entry.
    """
    cleaned: dict[str, str] = {}

    for idx, college in enumerate(raw_colleges):
        code = str(college.get("College_Code", "")).strip()
        if not code:
            continue

        text = _normalize_spaces(college.get("College_Name", ""))
        if not text:
            continue

        cutoff = len(text)
        next_idx = idx + 1
        if next_idx < len(raw_colleges):
            next_code = str(raw_colleges[next_idx].get("College_Code", "")).strip()
            next_serial = next_idx + 1
            if next_code:
                marker = re.compile(rf"\s+{next_serial}\s+{re.escape(next_code)}\s+")
                match = marker.search(text)
                if match:
                    cutoff = min(cutoff, match.start())

        section = re.search(
            r"\b3\.LIST OF COLLEGE CODE AND ITS BRANCHES\b",
            text,
            flags=re.IGNORECASE,
        )
        if section:
            cutoff = min(cutoff, section.start())

        candidate = text[:cutoff].strip(" ,;:-")
        candidate = re.sub(rf"\s+{re.escape(code)}$", "", candidate).strip(" ,;:-")
        cleaned[code] = candidate or code

    return cleaned


def _extract_percentage(value) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", str(value))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _clean_district(raw: str) -> str:
    """Extract a usable district from a noisy source field."""
    if not raw:
        return ""

    raw = raw.strip()
    if raw.replace(" ", "").replace(".", "").isdigit():
        return ""

    known_districts = {
        "Ariyalur",
        "Chengalpattu",
        "Chennai",
        "Coimbatore",
        "Cuddalore",
        "Dharmapuri",
        "Dindigul",
        "Erode",
        "Kallakurichi",
        "Kancheepuram",
        "Kanyakumari",
        "Karur",
        "Krishnagiri",
        "Madurai",
        "Nagapattinam",
        "Namakkal",
        "Perambalur",
        "Pudukkottai",
        "Ramanathapuram",
        "Ranipet",
        "Salem",
        "Sivagangai",
        "Sivakasi",
        "Tenkasi",
        "Thanjavur",
        "Theni",
        "The Nilgiris",
        "Thiruvallur",
        "Thiruvannamalai",
        "Thoothukudi",
        "Tiruchirappalli",
        "Tirunelveli",
        "Tirupattur",
        "Tiruppur",
        "Vellore",
        "Villupuram",
        "Virudhunagar",
    }

    for district in known_districts:
        if district.lower() in raw.lower():
            return district

    return ""


def _clean_url(url: str) -> str:
    if not url:
        return ""

    url = str(url).strip()
    if url in {"None", "null", "-", "0"}:
        return ""

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    return url.rstrip("/")


def _normalize_spaces(value) -> str:
    text = str(value).replace("\\", ", ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()
