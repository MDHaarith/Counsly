#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from time import sleep
from urllib.parse import quote_plus

import pdfplumber
from geopy.geocoders import ArcGIS


ROOT = Path(__file__).resolve().parent
PDF_PATH = ROOT / "7_List_of_TFCs.pdf"
OUTPUT_JSON = ROOT / "tfc_locations.json"
OUTPUT_CSV = ROOT / "tfc_locations.csv"
UNRESOLVED_JSON = ROOT / "tfc_locations_unresolved.json"


def clean_text(value: str | None) -> str:
    text = str(value or "")
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,")


def normalize_address(raw: str) -> str:
    text = clean_text(raw)
    text = text.replace(" ,", ",")
    text = re.sub(r"(?<=\d) (?=\d{3}\b)", "", text)
    text = text.replace(" , ", ", ")
    return text


def split_name_and_address(raw: str) -> tuple[str, str]:
    parts = [clean_text(part) for part in str(raw or "").splitlines() if clean_text(part)]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], parts[0]
    return parts[0], normalize_address(", ".join(parts[1:]))


def parse_pdf_rows(pdf_path: Path) -> list[dict]:
    rows: list[dict] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for raw_row in table[1:]:
                    if not raw_row or not raw_row[0]:
                        continue
                    sl_no = clean_text(raw_row[0])
                    if not sl_no.isdigit():
                        continue
                    district = clean_text(raw_row[1])
                    tfc_number = clean_text(raw_row[2])
                    centre_full = str(raw_row[3] or "").strip()
                    centre_name, address = split_name_and_address(centre_full)
                    full_address = normalize_address(centre_full)
                    rows.append(
                        {
                            "sl_no": int(sl_no),
                            "district": district,
                            "tfc_number": int(tfc_number) if tfc_number.isdigit() else tfc_number,
                            "centre_name": centre_name,
                            "address": address,
                            "full_address": full_address,
                        }
                    )
    return rows


def build_query(row: dict) -> str:
    base = row["full_address"] or row["centre_name"]
    district = clean_text(row.get("district"))
    parts = [base]
    if district and district.lower() not in base.lower():
        parts.append(district)
    parts.extend(["Tamil Nadu", "India"])
    return clean_text(", ".join(part for part in parts if part))


def geocode_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    geocoder = ArcGIS(timeout=20)
    resolved: list[dict] = []
    unresolved: list[dict] = []

    for idx, row in enumerate(rows, start=1):
        query = build_query(row)
        google_maps_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(query)}"
        payload = dict(row)
        payload["search_query"] = query
        payload["google_maps_url"] = google_maps_url
        payload["latitude"] = None
        payload["longitude"] = None
        payload["geocode_provider"] = "arcgis"
        payload["geocode_address"] = ""
        payload["geocode_status"] = "unresolved"

        try:
            location = geocoder.geocode(query)
        except Exception:
            location = None

        if location is not None:
            payload["latitude"] = round(float(location.latitude), 7)
            payload["longitude"] = round(float(location.longitude), 7)
            payload["geocode_address"] = clean_text(location.address)
            payload["geocode_status"] = "resolved"
            resolved.append(payload)
        else:
            unresolved.append(payload)

        if idx < len(rows):
            sleep(0.35)

    return resolved, unresolved


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "sl_no",
                "district",
                "tfc_number",
                "centre_name",
                "address",
                "full_address",
                "search_query",
                "google_maps_url",
                "latitude",
                "longitude",
                "geocode_provider",
                "geocode_address",
                "geocode_status",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    rows = parse_pdf_rows(PDF_PATH)
    resolved, unresolved = geocode_rows(rows)
    all_rows = sorted([*resolved, *unresolved], key=lambda row: int(row["sl_no"]))
    write_json(OUTPUT_JSON, all_rows)
    write_csv(OUTPUT_CSV, all_rows)
    write_json(UNRESOLVED_JSON, unresolved)

    print(
        json.dumps(
            {
                "pdf_path": str(PDF_PATH),
                "output_json": str(OUTPUT_JSON),
                "output_csv": str(OUTPUT_CSV),
                "unresolved_json": str(UNRESOLVED_JSON),
                "total_rows": len(all_rows),
                "resolved_rows": len(resolved),
                "unresolved_rows": len(unresolved),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
