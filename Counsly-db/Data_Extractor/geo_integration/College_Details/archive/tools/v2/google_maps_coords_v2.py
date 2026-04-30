#!/usr/bin/env python3
"""Google Maps browser automation for extracting college coordinates.

No Maps API. This drives a real browser, searches each college on Google Maps,
and extracts coordinates from the live result page.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from playwright.sync_api import Browser, Page, Playwright, TimeoutError as PlaywrightTimeoutError, sync_playwright


VIEW_COORD_PATTERNS = [
    re.compile(r"@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?),"),
    re.compile(r"[?&]ll=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)"),
]
PLACE_COORD_PATTERNS = [
    re.compile(r"!8m2!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)"),
    re.compile(r"!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)"),
]
TEXT_COORD_PATTERN = re.compile(r"(-?\d{1,2}\.\d{4,}),\s*(-?\d{1,3}\.\d{4,})")
DEFAULT_QUERY_FIELDS = ["name", "college", "title", "query", "institution"]
DEFAULT_ADDRESS_FIELDS = ["address", "location", "district", "city", "state", "pincode"]
TAMIL_NADU_BOUNDS = {"min_lat": 7.5, "max_lat": 13.75, "min_lng": 76.0, "max_lng": 80.5}
INDIA_BOUNDS = {"min_lat": 6.0, "max_lat": 38.5, "min_lng": 68.0, "max_lng": 97.5}
LOCATION_NOISE = {"iaf", "nh", "rs", "bag", "po", "so", "via", "road", "highway", "campus", "village", "post", "district", "taluk"}


@dataclass
class InputItem:
    index: int
    original: str
    line_label: str
    query: str
    payload: Any


@dataclass
class Result:
    index: int
    original: str
    query: str
    latitude: float | None
    longitude: float | None
    maps_url: str
    status: str
    error: str | None = None


class GoogleMapsExtractor:
    def __init__(
        self,
        browser_name: str,
        headless: bool,
        profile_dir: str | None,
        delay_seconds: float,
        timeout_ms: int,
    ) -> None:
        self.browser_name = browser_name
        self.headless = headless
        self.profile_dir = profile_dir
        self.delay_seconds = delay_seconds
        self.timeout_ms = timeout_ms
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None

    def __enter__(self) -> "GoogleMapsExtractor":
        self.playwright = sync_playwright().start()
        executable_path = self._resolve_executable_path()
        launch_args = {
            "headless": self.headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--start-maximized",
            ],
        }
        if executable_path:
            launch_args["executable_path"] = executable_path

        if self.browser_name == "firefox":
            self.browser = self.playwright.firefox.launch(**launch_args)
        else:
            self.browser = self.playwright.chromium.launch(**launch_args)

        context = self.browser.new_context(viewport={"width": 1440, "height": 980})
        self.page = context.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        self.page.goto("https://www.google.com/maps", wait_until="domcontentloaded")
        self._handle_consent()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        try:
            if self.browser:
                self.browser.close()
        finally:
            if self.playwright:
                self.playwright.stop()

    def _resolve_executable_path(self) -> str | None:
        if self.browser_name == "chrome":
            return shutil.which("google-chrome")
        if self.browser_name == "chromium":
            return shutil.which("chromium") or shutil.which("chromium-browser")
        if self.browser_name == "firefox":
            return shutil.which("firefox")
        return None

    def _handle_consent(self) -> None:
        assert self.page is not None
        candidates = [
            "button:has-text('Accept all')",
            "button:has-text('I agree')",
            "button:has-text('Accept')",
            "button:has-text('Reject all')",
            "form button",
        ]
        for selector in candidates:
            try:
                locator = self.page.locator(selector).first
                if locator.is_visible(timeout=1500):
                    text = (locator.inner_text(timeout=1500) or "").strip().lower()
                    if any(k in text for k in ["accept", "agree", "reject"]):
                        locator.click(timeout=1500)
                        self.page.wait_for_timeout(1000)
                        return
            except Exception:
                continue

    def extract(self, item: InputItem) -> Result:
        assert self.page is not None
        page = self.page

        try:
            fallback: Result | None = None
            for query_variant in build_query_variants(item.query):
                search_url = f"https://www.google.com/maps/search/{quote_plus(query_variant)}"
                page.goto(search_url, wait_until="domcontentloaded")
                self._handle_consent()
                page.wait_for_timeout(3000)

                self._click_first_result_if_needed()
                coords = self._wait_for_coordinates()
                if not coords:
                    coords = self._search_via_box(query_variant)
                if not coords:
                    coords = self._right_click_map_fallback()
                if not coords:
                    continue

                lat, lng = coords
                result = Result(
                    index=item.index,
                    original=item.original,
                    query=query_variant,
                    latitude=lat,
                    longitude=lng,
                    maps_url=page.url,
                    status="ok",
                )
                if within_bounds(lat, lng, TAMIL_NADU_BOUNDS):
                    if self.delay_seconds:
                        time.sleep(self.delay_seconds)
                    return result
                if fallback is None and within_bounds(lat, lng, INDIA_BOUNDS):
                    fallback = result
                elif fallback is None:
                    fallback = result

            if fallback is not None:
                if self.delay_seconds:
                    time.sleep(self.delay_seconds)
                return fallback

            return Result(
                index=item.index,
                original=item.original,
                query=item.query,
                latitude=None,
                longitude=None,
                maps_url=page.url,
                status="not_found",
                error="Could not extract coordinates from Google Maps page.",
            )
        except Exception as exc:  # noqa: BLE001
            return Result(
                index=item.index,
                original=item.original,
                query=item.query,
                latitude=None,
                longitude=None,
                maps_url=page.url,
                status="error",
                error=str(exc),
            )

    def _search_via_box(self, query: str) -> tuple[float, float] | None:
        assert self.page is not None
        page = self.page
        page.goto("https://www.google.com/maps", wait_until="domcontentloaded")
        page.wait_for_timeout(5000)
        selectors = ["#searchboxinput", "input[name='q']", "input[aria-label*='Search']"]
        for selector in selectors:
            try:
                box = page.locator(selector).first
                if not box.is_visible(timeout=2000):
                    continue
                box.click()
                box.press("ControlOrMeta+A")
                box.fill("")
                box.type(query, delay=20)
                box.press("Enter")
                page.wait_for_timeout(2500)
                self._click_first_result_if_needed()
                return self._wait_for_coordinates()
            except Exception:
                continue
        return None

    def _wait_for_coordinates(self) -> tuple[float, float] | None:
        assert self.page is not None
        page = self.page
        deadline = time.time() + (self.timeout_ms / 1000)
        while time.time() < deadline:
            coords = extract_coords_from_url(page.url)
            if coords:
                return coords
            try:
                page.wait_for_timeout(800)
            except PlaywrightTimeoutError:
                break
        return None

    def _click_first_result_if_needed(self) -> None:
        assert self.page is not None
        page = self.page
        candidates = [
            "a.hfpxzc",
            "div[role='article'] a[href*='/maps/place/']",
            "div.Nv2PK a[href*='/maps/place/']",
        ]
        for selector in candidates:
            try:
                locator = page.locator(selector).first
                if locator.is_visible(timeout=2000):
                    locator.click(timeout=2000)
                    page.wait_for_timeout(2500)
                    return
            except Exception:
                continue

    def _right_click_map_fallback(self) -> tuple[float, float] | None:
        assert self.page is not None
        page = self.page
        candidates = ["canvas", "div[aria-label*='Map']", "div.widget-scene-canvas"]
        for selector in candidates:
            try:
                locator = page.locator(selector).first
                if not locator.is_visible(timeout=1500):
                    continue
                box = locator.bounding_box()
                if not box:
                    continue
                x = box["x"] + box["width"] / 2
                y = box["y"] + box["height"] / 2
                page.mouse.click(x, y, button="right")
                page.wait_for_timeout(1200)
                text = page.locator("body").inner_text(timeout=1500)
                match = TEXT_COORD_PATTERN.search(text)
                page.keyboard.press("Escape")
                if match:
                    return float(match.group(1)), float(match.group(2))
            except Exception:
                continue
        return None


def extract_coords_from_url(url: str) -> tuple[float, float] | None:
    for pattern in PLACE_COORD_PATTERNS:
        match = pattern.search(url)
        if match:
            return float(match.group(1)), float(match.group(2))
    for pattern in VIEW_COORD_PATTERNS:
        match = pattern.search(url)
        if match:
            return float(match.group(1)), float(match.group(2))
    return None


def within_bounds(lat: float, lng: float, bounds: dict[str, float]) -> bool:
    return bounds["min_lat"] <= lat <= bounds["max_lat"] and bounds["min_lng"] <= lng <= bounds["max_lng"]


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def compact_location_part(part: str) -> str:
    tokens = [token for token in tokenize(part) if token not in LOCATION_NOISE]
    return " ".join(tokens)


def extract_location_hints(query: str) -> dict[str, list[str]]:
    hints: dict[str, list[str]] = {"district": [], "taluk": [], "city": [], "pincode": []}
    for match in re.finditer(r"([A-Za-z][A-Za-z .'-]{1,40}?)\s+District\b", query, flags=re.IGNORECASE):
        value = compact_location_part(match.group(1))
        if value:
            hints["district"].append(value)
    for match in re.finditer(r"([A-Za-z][A-Za-z .'-]{1,40}?)\s+Taluk\b", query, flags=re.IGNORECASE):
        value = compact_location_part(match.group(1))
        if value:
            hints["taluk"].append(value)
    hints["pincode"] = re.findall(r"\b\d{6}\b", query)
    parts = [part.strip() for part in query.split(",") if part.strip()]
    if len(parts) > 1:
        for part in parts[1:]:
            lowered = part.lower()
            if "district" in lowered or "taluk" in lowered:
                continue
            city = compact_location_part(re.sub(r"\b\d{6}\b", " ", part))
            if city and len(city.split()) <= 5:
                hints["city"].append(city)
    for key in hints:
        hints[key] = list(dict.fromkeys([value for value in hints[key] if value]))
    return hints


def build_query_variants(query: str) -> list[str]:
    cleaned = " ".join(query.replace("＜½", " ").split())
    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    first = parts[0] if parts else cleaned
    hints = extract_location_hints(cleaned)
    locality_parts = [compact_location_part(part) for part in parts[1:]]
    locality_parts = [part for part in locality_parts if part]
    locality_chain = " ".join(locality_parts[:4]).strip()
    city_chain = " ".join(hints["city"][:3]).strip()
    district = hints["district"][0] if hints["district"] else ""
    taluk = hints["taluk"][0] if hints["taluk"] else ""
    pincode = hints["pincode"][0] if hints["pincode"] else ""

    queries = [cleaned]
    if parts and len(parts) > 1:
        queries.append(", ".join(parts[: min(3, len(parts))]))
    if locality_chain:
        queries.append(f"{first} {locality_chain}")
    if city_chain and pincode:
        queries.append(f"{first} {city_chain} {pincode}")
    if city_chain:
        queries.append(f"{first} {city_chain}")
    if district and pincode:
        queries.append(f"{first} {district} {pincode}")
    if district:
        queries.append(f"{first} {district}")
    if taluk and district:
        queries.append(f"{first} {taluk} {district}")
    if pincode:
        queries.append(f"{first} {pincode}")
    if "tamil nadu" not in cleaned.lower():
        queries.append(f"{cleaned} Tamil Nadu")
        if city_chain:
            queries.append(f"{first} {city_chain} Tamil Nadu")
        elif district:
            queries.append(f"{first} {district} Tamil Nadu")

    uppercase_variants = [candidate.upper() for candidate in queries if any(ch.isalpha() for ch in candidate)]
    queries.extend(uppercase_variants)

    deduped: list[str] = []
    seen: set[str] = set()
    for candidate in queries:
        candidate = candidate.strip(" ,")
        if candidate and candidate not in seen:
            seen.add(candidate)
            deduped.append(candidate)
    return deduped[:20]


def detect_input_format(path: Path, explicit: str) -> str:
    if explicit != "auto":
        return explicit
    suffix = path.suffix.lower()
    if suffix == ".json":
        return "json"
    if suffix == ".csv":
        return "csv"
    return "txt"


def load_items(path: Path, input_format: str, query_field: str | None, address_fields: list[str]) -> list[InputItem]:
    if input_format == "txt":
        lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines()]
        return [
            InputItem(index=i, original=line, line_label=line, query=line, payload=line)
            for i, line in enumerate(lines)
            if line
        ]

    if input_format == "csv":
        with path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            fieldnames = reader.fieldnames or []
            chosen_field = query_field or first_present(fieldnames, DEFAULT_QUERY_FIELDS) or (fieldnames[0] if fieldnames else None)
            if not chosen_field:
                raise ValueError("Could not determine which CSV column contains the college name.")
            items: list[InputItem] = []
            for i, row in enumerate(reader):
                name = (row.get(chosen_field) or "").strip()
                if not name:
                    continue
                extra = [row.get(field, "").strip() for field in address_fields if row.get(field)]
                query = ", ".join([name] + [part for part in extra if part])
                items.append(InputItem(index=i, original=name, line_label=name, query=query, payload=row))
            return items

    if input_format == "json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError("JSON input must be an array of strings or objects.")
        items: list[InputItem] = []
        for i, entry in enumerate(data):
            if isinstance(entry, str):
                text = entry.strip()
                if not text:
                    continue
                items.append(InputItem(index=i, original=text, line_label=text, query=text, payload=entry))
                continue
            if isinstance(entry, dict):
                chosen_field = query_field or first_present(entry.keys(), DEFAULT_QUERY_FIELDS)
                if not chosen_field or not entry.get(chosen_field):
                    raise ValueError(f"JSON object at index {i} has no usable college-name field.")
                name = str(entry[chosen_field]).strip()
                extra = [str(entry[field]).strip() for field in address_fields if entry.get(field)]
                query = ", ".join([name] + [part for part in extra if part])
                items.append(InputItem(index=i, original=name, line_label=name, query=query, payload=entry))
                continue
            raise ValueError(f"Unsupported JSON entry type at index {i}: {type(entry)!r}")
        return items

    raise ValueError(f"Unsupported input format: {input_format}")


def first_present(candidates: Any, preferred: list[str]) -> str | None:
    candidate_set = {str(candidate) for candidate in candidates}
    for field in preferred:
        if field in candidate_set:
            return field
    return None


def default_output_paths(input_path: Path, input_format: str) -> tuple[Path, Path, Path]:
    base = input_path.with_suffix("")
    if input_format == "json":
        structured = base.with_name(base.name + "_with_coordinates.json")
    elif input_format == "csv":
        structured = base.with_name(base.name + "_with_coordinates.csv")
    else:
        structured = base.with_name(base.name + "_with_coordinates.txt")
    lines = base.with_name(base.name + "_coords_lines.txt")
    failures = base.with_name(base.name + "_failed.txt")
    return structured, lines, failures


def write_outputs(
    items: list[InputItem],
    results: list[Result],
    input_path: Path,
    input_format: str,
    structured_output: Path,
    line_output: Path,
    failed_output: Path,
) -> None:
    by_index = {result.index: result for result in results}

    line_output.parent.mkdir(parents=True, exist_ok=True)
    with line_output.open("w", encoding="utf-8") as fh:
        for item in items:
            result = by_index[item.index]
            if result.latitude is None or result.longitude is None:
                fh.write(f"{item.line_label},NOT_FOUND,NOT_FOUND,\n")
            else:
                fh.write(f"{item.line_label},{result.latitude},{result.longitude},\n")

    with failed_output.open("w", encoding="utf-8") as fh:
        for item in items:
            result = by_index[item.index]
            if result.status != "ok":
                fh.write(f"{item.line_label} :: {result.status} :: {result.error or ''}\n")

    if input_format == "txt":
        with structured_output.open("w", encoding="utf-8") as fh:
            for item in items:
                result = by_index[item.index]
                if result.latitude is None or result.longitude is None:
                    fh.write(f"{item.original},NOT_FOUND,NOT_FOUND,\n")
                else:
                    fh.write(f"{item.original},{result.latitude},{result.longitude},\n")
        return

    if input_format == "csv":
        with input_path.open("r", encoding="utf-8", newline="") as src:
            reader = csv.DictReader(src)
            rows = list(reader)
            fieldnames = list(reader.fieldnames or [])
        extra_fields = ["latitude", "longitude", "maps_url", "status", "error"]
        final_fields = fieldnames + [field for field in extra_fields if field not in fieldnames]
        for i, row in enumerate(rows):
            result = by_index.get(i)
            if result:
                row.update(
                    {
                        "latitude": result.latitude,
                        "longitude": result.longitude,
                        "maps_url": result.maps_url,
                        "status": result.status,
                        "error": result.error,
                    }
                )
        with structured_output.open("w", encoding="utf-8", newline="") as dst:
            writer = csv.DictWriter(dst, fieldnames=final_fields)
            writer.writeheader()
            writer.writerows(rows)
        return

    if input_format == "json":
        original_data = json.loads(input_path.read_text(encoding="utf-8"))
        merged: list[Any] = []
        for i, entry in enumerate(original_data):
            result = by_index.get(i)
            if isinstance(entry, str):
                merged.append(
                    {
                        "name": entry,
                        "latitude": result.latitude if result else None,
                        "longitude": result.longitude if result else None,
                        "maps_url": result.maps_url if result else None,
                        "status": result.status if result else "missing",
                        "error": result.error if result else None,
                    }
                )
            elif isinstance(entry, dict):
                enriched = dict(entry)
                if result:
                    enriched.update(
                        {
                            "latitude": result.latitude,
                            "longitude": result.longitude,
                            "maps_url": result.maps_url,
                            "status": result.status,
                            "error": result.error,
                        }
                    )
                merged.append(enriched)
            else:
                merged.append(entry)
        structured_output.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Browser-only Google Maps coordinate extractor")
    parser.add_argument("input", help="Path to a TXT, CSV, or JSON file containing college names")
    parser.add_argument("--input-format", choices=["auto", "txt", "csv", "json"], default="auto")
    parser.add_argument("--query-field", help="Field/column that contains the college name for CSV/JSON object inputs")
    parser.add_argument(
        "--address-fields",
        default=",".join(DEFAULT_ADDRESS_FIELDS),
        help="Comma-separated extra fields to include in the Google Maps search query",
    )
    parser.add_argument("--output", help="Structured output path (defaults based on the input format)")
    parser.add_argument("--line-output", help="Plain text output path with 'college,lat,lng,' lines")
    parser.add_argument("--failed-output", help="Path for unresolved colleges")
    parser.add_argument("--browser", choices=["chrome", "chromium", "firefox"], default="chrome")
    parser.add_argument("--headless", action="store_true", help="Run the browser invisibly")
    parser.add_argument("--delay-seconds", type=float, default=1.0, help="Delay between searches")
    parser.add_argument("--timeout-ms", type=int, default=25000, help="Per-college timeout in milliseconds")
    parser.add_argument("--limit", type=int, help="Only process the first N items")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    input_format = detect_input_format(input_path, args.input_format)
    address_fields = [field.strip() for field in args.address_fields.split(",") if field.strip()]
    items = load_items(input_path, input_format, args.query_field, address_fields)
    if args.limit:
        items = items[: args.limit]
    if not items:
        print("No input items found.", file=sys.stderr)
        return 1

    structured_default, line_default, failed_default = default_output_paths(input_path, input_format)
    structured_output = Path(args.output).expanduser().resolve() if args.output else structured_default
    line_output = Path(args.line_output).expanduser().resolve() if args.line_output else line_default
    failed_output = Path(args.failed_output).expanduser().resolve() if args.failed_output else failed_default

    results: list[Result] = []
    with GoogleMapsExtractor(
        browser_name=args.browser,
        headless=args.headless,
        profile_dir=None,
        delay_seconds=args.delay_seconds,
        timeout_ms=args.timeout_ms,
    ) as extractor:
        total = len(items)
        for idx, item in enumerate(items, start=1):
            print(f"[{idx}/{total}] Searching: {item.query}")
            result = extractor.extract(item)
            results.append(result)
            if result.status == "ok":
                print(f"    -> {result.latitude}, {result.longitude}")
            else:
                print(f"    -> {result.status}: {result.error}")

    write_outputs(items, results, input_path, input_format, structured_output, line_output, failed_output)
    ok_count = sum(1 for result in results if result.status == "ok")
    print("\nDone.")
    print(f"Successful: {ok_count}/{len(results)}")
    print(f"Structured output: {structured_output}")
    print(f"Line output:       {line_output}")
    print(f"Failures:          {failed_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
