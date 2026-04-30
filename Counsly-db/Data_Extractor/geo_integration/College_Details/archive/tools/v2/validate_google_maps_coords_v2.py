#!/usr/bin/env python3
"""Validate Google Maps-derived coordinates for college datasets.

Checks for:
- missing or non-numeric coordinates
- invalid coordinate ranges
- outside India / outside Tamil Nadu bounds
- duplicates
- mismatch between saved coordinates and canonical place coordinates embedded in maps_url

Can also emit an autofixed file using canonical place coordinates from the URL.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

INDIA_BOUNDS = {
    "min_lat": 6.0,
    "max_lat": 38.5,
    "min_lng": 68.0,
    "max_lng": 97.5,
}

TAMIL_NADU_BOUNDS = {
    "min_lat": 7.5,
    "max_lat": 13.75,
    "min_lng": 76.0,
    "max_lng": 80.5,
}

VIEW_PATTERNS = [
    re.compile(r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?),"),
    re.compile(r"[?&]ll=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)"),
]

PLACE_PATTERNS = [
    re.compile(r"!8m2!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)"),
    re.compile(r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)"),
]

NAME_FIELDS = ["name", "college", "title", "query", "institution"]
LAT_FIELDS = ["latitude", "lat"]
LNG_FIELDS = ["longitude", "lng", "lon", "long"]


@dataclass
class Issue:
    code: str
    severity: str
    message: str


@dataclass
class Record:
    index: int
    name: str
    latitude: float | None
    longitude: float | None
    maps_url: str | None
    raw: Any
    issues: list[Issue] = field(default_factory=list)
    suggested_latitude: float | None = None
    suggested_longitude: float | None = None
    place_latitude: float | None = None
    place_longitude: float | None = None
    view_latitude: float | None = None
    view_longitude: float | None = None

    @property
    def has_issue(self) -> bool:
        return any(issue.severity in {"warn", "error"} for issue in self.issues)

    @property
    def has_info(self) -> bool:
        return any(issue.severity == "info" for issue in self.issues)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate coordinate outputs from google_maps_coords.py")
    parser.add_argument("input", help="Input JSON file, usually *_with_coordinates.json")
    parser.add_argument("--distance-threshold-m", type=float, default=150.0, help="Flag saved-vs-place URL mismatches above this many meters")
    parser.add_argument("--duplicate-precision", type=int, default=6, help="Decimal precision for duplicate detection")
    parser.add_argument("--autofix-url-place", action="store_true", help="Write a corrected JSON using canonical place coordinates from maps_url when available")
    return parser.parse_args()


def load_records(path: Path) -> tuple[list[Any], list[Record]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Expected a JSON array")

    records: list[Record] = []
    for idx, item in enumerate(data):
        if isinstance(item, dict):
            name = first_value(item, NAME_FIELDS) or f"record_{idx}"
            lat = parse_float(first_value(item, LAT_FIELDS))
            lng = parse_float(first_value(item, LNG_FIELDS))
            maps_url = item.get("maps_url") if isinstance(item.get("maps_url"), str) else None
        elif isinstance(item, str):
            name = item
            lat = None
            lng = None
            maps_url = None
        else:
            name = f"record_{idx}"
            lat = None
            lng = None
            maps_url = None

        records.append(
            Record(
                index=idx,
                name=str(name),
                latitude=lat,
                longitude=lng,
                maps_url=maps_url,
                raw=item,
            )
        )
    return data, records


def first_value(item: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in item and item[key] not in (None, ""):
            return item[key]
    return None


def parse_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def extract_coords(url: str | None, patterns: list[re.Pattern[str]]) -> tuple[float, float] | None:
    if not url:
        return None
    for pattern in patterns:
        match = pattern.search(url)
        if match:
            return float(match.group(1)), float(match.group(2))
    return None


def within_bounds(lat: float, lng: float, bounds: dict[str, float]) -> bool:
    return bounds["min_lat"] <= lat <= bounds["max_lat"] and bounds["min_lng"] <= lng <= bounds["max_lng"]


def distance_meters(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def add_issue(record: Record, code: str, severity: str, message: str) -> None:
    record.issues.append(Issue(code=code, severity=severity, message=message))


def validate_records(records: list[Record], distance_threshold_m: float, duplicate_precision: int) -> None:
    coord_buckets: defaultdict[tuple[float, float], list[Record]] = defaultdict(list)

    for record in records:
        if record.latitude is None or record.longitude is None:
            add_issue(record, "missing_coordinates", "error", "Missing latitude/longitude")
            continue

        lat = record.latitude
        lng = record.longitude

        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            add_issue(record, "invalid_range", "error", f"Coordinates out of numeric range: {lat}, {lng}")
            continue

        if not within_bounds(lat, lng, INDIA_BOUNDS):
            add_issue(record, "outside_india", "error", f"Coordinates outside India bounds: {lat}, {lng}")
        elif not within_bounds(lat, lng, TAMIL_NADU_BOUNDS):
            add_issue(record, "outside_tamil_nadu", "warn", f"Coordinates outside Tamil Nadu bounds: {lat}, {lng}")

        if lat == 0 and lng == 0:
            add_issue(record, "zero_coordinates", "error", "Coordinates are 0,0")

        if record.maps_url:
            place = extract_coords(record.maps_url, PLACE_PATTERNS)
            view = extract_coords(record.maps_url, VIEW_PATTERNS)
            if place:
                record.place_latitude, record.place_longitude = place
                record.suggested_latitude, record.suggested_longitude = place
                d = distance_meters(lat, lng, place[0], place[1])
                if d > distance_threshold_m:
                    add_issue(
                        record,
                        "url_place_mismatch",
                        "warn",
                        f"Saved coordinates differ from place coordinates in URL by {d:.1f} m",
                    )
            if view:
                record.view_latitude, record.view_longitude = view
                if place:
                    dv = distance_meters(view[0], view[1], place[0], place[1])
                    if dv > distance_threshold_m:
                        add_issue(
                            record,
                            "viewport_offset",
                            "info",
                            f"Map viewport center differs from place coordinates by {dv:.1f} m",
                        )

        rounded = (round(lat, duplicate_precision), round(lng, duplicate_precision))
        coord_buckets[rounded].append(record)

    for coord, bucket in coord_buckets.items():
        if len(bucket) > 1:
            names = "; ".join(record.name for record in bucket[:5])
            extra = "" if len(bucket) <= 5 else f" (+{len(bucket) - 5} more)"
            for record in bucket:
                add_issue(
                    record,
                    "duplicate_coordinates",
                    "warn",
                    f"Same rounded coordinates {coord[0]}, {coord[1]} shared by {len(bucket)} records: {names}{extra}",
                )


def build_summary(records: list[Record]) -> dict[str, Any]:
    total = len(records)
    with_issues = [record for record in records if record.has_issue]
    actionable_issues = [issue for record in with_issues for issue in record.issues if issue.severity in {"warn", "error"}]
    info_issues = [issue for record in records for issue in record.issues if issue.severity == "info"]
    issue_counts = Counter(issue.code for issue in actionable_issues)
    severity_counts = Counter(issue.severity for issue in actionable_issues)
    info_counts = Counter(issue.code for issue in info_issues)
    return {
        "total_records": total,
        "records_with_issues": len(with_issues),
        "clean_records": total - len(with_issues),
        "issue_counts": dict(issue_counts),
        "severity_counts": dict(severity_counts),
        "info_counts": dict(info_counts),
    }


def write_outputs(input_path: Path, original_data: list[Any], records: list[Record], autofix: bool) -> dict[str, Path]:
    stem = input_path.with_suffix("")
    report_path = stem.with_name(stem.name + "_validation_report.json")
    summary_path = stem.with_name(stem.name + "_validation_summary.txt")
    suspects_path = stem.with_name(stem.name + "_suspect_coordinates.json")
    autofix_path = stem.with_name(stem.name + "_url_fixed.json")

    summary = build_summary(records)
    suspects = []
    for record in records:
        if not record.has_issue:
            continue
        suspects.append(
            {
                "index": record.index,
                "name": record.name,
                "latitude": record.latitude,
                "longitude": record.longitude,
                "maps_url": record.maps_url,
                "place_latitude": record.place_latitude,
                "place_longitude": record.place_longitude,
                "view_latitude": record.view_latitude,
                "view_longitude": record.view_longitude,
                "suggested_latitude": record.suggested_latitude,
                "suggested_longitude": record.suggested_longitude,
                "issues": [issue.__dict__ for issue in record.issues if issue.severity in {"warn", "error"}],
                "info": [issue.__dict__ for issue in record.issues if issue.severity == "info"],
            }
        )

    report = {
        "summary": summary,
        "suspects": suspects,
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    suspects_path.write_text(json.dumps(suspects, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"Total records: {summary['total_records']}",
        f"Clean records: {summary['clean_records']}",
        f"Records with issues: {summary['records_with_issues']}",
        "",
        "Issue counts:",
    ]
    for code, count in sorted(summary["issue_counts"].items()):
        lines.append(f"- {code}: {count}")
    if summary["info_counts"]:
        lines.append("")
        lines.append("Informational notes:")
        for code, count in sorted(summary["info_counts"].items()):
            lines.append(f"- {code}: {count}")
    lines.append("")
    lines.append("Top suspect examples:")
    for suspect in suspects[:15]:
        issue_codes = ", ".join(issue["code"] for issue in suspect["issues"])
        suggestion = ""
        if suspect["suggested_latitude"] is not None and suspect["suggested_longitude"] is not None:
            suggestion = f" -> suggested {suspect['suggested_latitude']}, {suspect['suggested_longitude']}"
        lines.append(
            f"- {suspect['name']} :: {suspect['latitude']}, {suspect['longitude']} :: {issue_codes}{suggestion}"
        )
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    outputs = {
        "report": report_path,
        "summary": summary_path,
        "suspects": suspects_path,
    }

    if autofix:
        fixed_data = []
        for idx, item in enumerate(original_data):
            record = records[idx]
            if isinstance(item, dict):
                updated = dict(item)
                if record.suggested_latitude is not None and record.suggested_longitude is not None:
                    updated["latitude"] = record.suggested_latitude
                    updated["longitude"] = record.suggested_longitude
                    updated["validation_fixed_from_url"] = True
                fixed_data.append(updated)
            else:
                fixed_data.append(item)
        autofix_path.write_text(json.dumps(fixed_data, ensure_ascii=False, indent=2), encoding="utf-8")
        outputs["autofix"] = autofix_path

    return outputs


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    original_data, records = load_records(input_path)
    validate_records(records, args.distance_threshold_m, args.duplicate_precision)
    outputs = write_outputs(input_path, original_data, records, args.autofix_url_place)
    summary = build_summary(records)

    print(f"Validated: {input_path}")
    print(f"Total records: {summary['total_records']}")
    print(f"Clean records: {summary['clean_records']}")
    print(f"Records with issues: {summary['records_with_issues']}")
    print("Issue counts:")
    for code, count in sorted(summary["issue_counts"].items()):
        print(f"  - {code}: {count}")
    if summary["info_counts"]:
        print("Informational notes:")
        for code, count in sorted(summary["info_counts"].items()):
            print(f"  - {code}: {count}")
    print("Outputs:")
    for key, path in outputs.items():
        print(f"  - {key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
