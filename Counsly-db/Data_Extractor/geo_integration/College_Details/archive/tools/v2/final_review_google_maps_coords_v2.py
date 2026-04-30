#!/usr/bin/env python3
"""Second-pass reviewer for Google Maps college coordinates.

Workflow:
1) Start from an existing *_with_coordinates.json file.
2) Auto-correct obvious viewport mistakes using canonical place coordinates in maps_url.
3) Re-review only the records that still look invalid (missing/outside India/outside Tamil Nadu)
   by searching Google Maps again in a browser and inspecting multiple candidate place results.
4) If no confident Tamil Nadu match is found, null the coordinates instead of preserving junk.
5) Write a final cleaned JSON, plain lines output, unresolved list, and review report.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus, unquote

from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright

from validate_google_maps_coords_v2 import INDIA_BOUNDS, NAME_FIELDS, PLACE_PATTERNS, TAMIL_NADU_BOUNDS, distance_meters, extract_coords, within_bounds


INSTITUTION_KEYWORDS = {
    "college",
    "engineering",
    "institute",
    "school",
    "academy",
    "university",
    "technology",
    "polytechnic",
    "architecture",
}
CATEGORY_PATTERNS = [
    re.compile(r"\b(architecture school|engineering college|college of engineering and technology|college of technology|polytechnic college|women'?s college|arts and science college|college|university|institute|school|academy)\b", re.IGNORECASE),
]
COMMON_STOPWORDS = {
    "of",
    "and",
    "the",
    "for",
    "autonomous",
    "campus",
    "road",
    "district",
    "post",
    "taluk",
    "village",
    "nagar",
    "near",
    "old",
    "new",
    "main",
    "tamil",
    "nadu",
}
LOCATION_NOISE = {
    "iaf",
    "nh",
    "rs",
    "bag",
    "po",
    "so",
    "via",
    "road",
    "highway",
    "campus",
    "village",
    "post",
    "district",
    "taluk",
}


@dataclass
class Candidate:
    query: str
    source: str
    title: str
    latitude: float | None
    longitude: float | None
    maps_url: str
    body_snippet: str
    score: float
    accepted: bool
    reasons: list[str] = field(default_factory=list)
    signals: dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewOutcome:
    action: str
    latitude: float | None
    longitude: float | None
    maps_url: str | None
    reviewer_query: str | None
    confidence: float | None
    reason: str
    candidates: list[dict[str, Any]]


class MapsSecondPassReviewer:
    def __init__(self, browser_name: str, headless: bool, timeout_ms: int, delay_seconds: float) -> None:
        self.browser_name = browser_name
        self.headless = headless
        self.timeout_ms = timeout_ms
        self.delay_seconds = delay_seconds
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.context: BrowserContext | None = None
        self.page: Page | None = None

    def __enter__(self) -> "MapsSecondPassReviewer":
        self.playwright = sync_playwright().start()
        executable_path = self._resolve_executable_path()
        launch_args: dict[str, Any] = {
            "headless": self.headless,
            "args": ["--disable-blink-features=AutomationControlled", "--start-maximized"],
        }
        if executable_path:
            launch_args["executable_path"] = executable_path

        if self.browser_name == "firefox":
            self.browser = self.playwright.firefox.launch(**launch_args)
        else:
            self.browser = self.playwright.chromium.launch(**launch_args)

        self.context = self.browser.new_context(viewport={"width": 1440, "height": 980})
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout_ms)
        self.page.goto("https://www.google.com/maps", wait_until="domcontentloaded")
        self._handle_consent(self.page)
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

    def _handle_consent(self, page: Page) -> None:
        selectors = [
            "button:has-text('Accept all')",
            "button:has-text('I agree')",
            "button:has-text('Accept')",
            "button:has-text('Reject all')",
            "form button",
        ]
        for selector in selectors:
            try:
                locator = page.locator(selector).first
                if locator.is_visible(timeout=1200):
                    text = (locator.inner_text(timeout=1200) or "").strip().lower()
                    if any(token in text for token in ["accept", "agree", "reject"]):
                        locator.click(timeout=1200)
                        page.wait_for_timeout(800)
                        return
            except Exception:
                continue

    def search_best(self, name: str) -> ReviewOutcome:
        assert self.page is not None
        queries = build_queries(name)
        collected: list[Candidate] = []
        best: Candidate | None = None

        for query in queries:
            candidate_batch = self._collect_candidates_for_query(query, name)
            collected.extend(candidate_batch)
            for candidate in candidate_batch:
                if candidate.accepted and (best is None or candidate.score > best.score):
                    best = candidate
            if best and best.score >= 0.82:
                break
            if self.delay_seconds:
                time.sleep(self.delay_seconds)

        if best:
            return ReviewOutcome(
                action="corrected_second_pass",
                latitude=best.latitude,
                longitude=best.longitude,
                maps_url=best.maps_url,
                reviewer_query=best.query,
                confidence=round(best.score, 4),
                reason="Accepted best Tamil Nadu candidate from second-pass Google Maps review.",
                candidates=[candidate_to_dict(candidate) for candidate in collected],
            )

        return ReviewOutcome(
            action="nullified_unmatched",
            latitude=None,
            longitude=None,
            maps_url=None,
            reviewer_query=queries[0] if queries else None,
            confidence=None,
            reason="No confident Tamil Nadu match found during second-pass review; coordinates were nulled.",
            candidates=[candidate_to_dict(candidate) for candidate in collected],
        )

    def _collect_candidates_for_query(self, query: str, original_name: str) -> list[Candidate]:
        assert self.page is not None
        page = self.page
        search_url = f"https://www.google.com/maps/search/{quote_plus(query)}"
        page.goto(search_url, wait_until="domcontentloaded")
        self._handle_consent(page)
        page.wait_for_timeout(4200)

        hrefs: list[tuple[str, str]] = []
        try:
            links = page.locator("a.hfpxzc")
            count = min(links.count(), 5)
            for idx in range(count):
                href = links.nth(idx).get_attribute("href", timeout=1200)
                if href and href not in {h for h, _ in hrefs}:
                    hrefs.append((href, f"results_link_{idx}"))
        except Exception:
            pass

        if not hrefs and "/maps/search/" in page.url:
            try:
                page.wait_for_timeout(1800)
                links = page.locator("a.hfpxzc")
                count = min(links.count(), 5)
                for idx in range(count):
                    href = links.nth(idx).get_attribute("href", timeout=1200)
                    if href and href not in {h for h, _ in hrefs}:
                        hrefs.append((href, f"results_link_{idx}"))
            except Exception:
                pass

        candidates: list[Candidate] = []
        direct = self._inspect_page(page, query, "direct_place", original_name)
        if direct:
            candidates.append(direct)

        for href, source in hrefs:
            inspected = self._inspect_href(href, query, source, original_name)
            if inspected:
                candidates.append(inspected)
        return candidates

    def _inspect_href(self, href: str, query: str, source: str, original_name: str) -> Candidate | None:
        assert self.context is not None
        temp_page = self.context.new_page()
        temp_page.set_default_timeout(self.timeout_ms)
        try:
            temp_page.goto(href, wait_until="domcontentloaded")
            self._handle_consent(temp_page)
            temp_page.wait_for_timeout(2200)
            return self._inspect_page(temp_page, query, source, original_name)
        except Exception:
            return None
        finally:
            temp_page.close()

    def _inspect_page(self, page: Page, query: str, source: str, original_name: str) -> Candidate | None:
        try:
            title = clean_title(page.title())
        except Exception:
            title = ""
        try:
            body = page.locator("body").inner_text(timeout=4000)
        except Exception:
            body = ""

        place = extract_coords(page.url, PLACE_PATTERNS)
        signals = extract_structured_signals(body)
        score, accepted, reasons = score_candidate(original_name, title, body, place, signals)
        return Candidate(
            query=query,
            source=source,
            title=title,
            latitude=place[0] if place else None,
            longitude=place[1] if place else None,
            maps_url=page.url,
            body_snippet=shorten(body, 800),
            score=score,
            accepted=accepted,
            reasons=reasons,
            signals=signals,
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Second-pass reviewer for Google Maps college coordinates")
    parser.add_argument("input", help="Path to *_with_coordinates.json")
    parser.add_argument("--browser", choices=["chrome", "chromium", "firefox"], default="chrome")
    parser.add_argument("--headless", action="store_true", help="Run browser invisibly")
    parser.add_argument("--timeout-ms", type=int, default=25000)
    parser.add_argument("--delay-seconds", type=float, default=0.75)
    parser.add_argument("--distance-threshold-m", type=float, default=150.0)
    return parser.parse_args()


def clean_title(title: str) -> str:
    title = title.replace(" - Google Maps", "")
    return " ".join(title.split())


def shorten(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text[:limit]


def extract_structured_signals(body_text: str) -> dict[str, Any]:
    normalized = " ".join(body_text.split())
    websites = re.findall(r"\b(?:[a-z0-9-]+\.)+(?:ac|edu|org|com|in)(?:\.[a-z]{2})?\b", normalized, flags=re.IGNORECASE)
    phones = re.findall(r"(?:\+91[-\s]?)?(?:0)?[6-9]\d{9}|(?:\b0\d{2,4}[ -]\d{5,8}\b)", normalized)
    pincodes = re.findall(r"\b\d{6}\b", normalized)
    plus_codes = re.findall(r"\b[23456789CFGHJMPQRVWX]{4,8}\+[23456789CFGHJMPQRVWX]{2,3}\b", normalized)

    category = None
    for pattern in CATEGORY_PATTERNS:
        match = pattern.search(normalized)
        if match:
            category = match.group(1).lower()
            break

    address_snippet = ""
    pivot = None
    for needle in list(plus_codes) + list(pincodes):
        idx = normalized.find(needle)
        if idx >= 0:
            pivot = idx
            break
    if pivot is not None:
        start = max(0, pivot - 90)
        end = min(len(normalized), pivot + 140)
        address_snippet = normalized[start:end].strip(" |,")

    return {
        "website": websites[0] if websites else None,
        "phone": phones[0] if phones else None,
        "pincode": pincodes[0] if pincodes else None,
        "plus_code": plus_codes[0] if plus_codes else None,
        "category": category,
        "address_snippet": address_snippet or None,
    }


def first_name(item: dict[str, Any]) -> str:
    for key in NAME_FIELDS:
        if item.get(key):
            return str(item[key])
    return ""


def normalize_query(text: str) -> str:
    text = text.replace("＜½", " ")
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"[^\w\s,.-]", " ", text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+,", ",", text)
    return text.strip(" ,")


def compact_location_part(part: str) -> str:
    tokens = [token for token in tokenize(part) if token not in LOCATION_NOISE]
    return " ".join(tokens)



def build_queries(name: str) -> list[str]:
    cleaned = normalize_query(name)
    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    first = parts[0] if parts else cleaned
    hints = extract_location_hints(cleaned)

    locality_parts = [compact_location_part(part) for part in parts[1:]]
    locality_parts = [part for part in locality_parts if part]
    locality_chain = " ".join(locality_parts[:4]).strip()
    city_chain = " ".join(hints["city"][:3]).strip()
    pincode = hints["pincode"][0] if hints["pincode"] else ""
    district = hints["district"][0] if hints["district"] else ""
    taluk = hints["taluk"][0] if hints["taluk"] else ""

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
    queries.append(first)
    if "tamil nadu" not in cleaned.lower():
        queries.append(f"{cleaned}, Tamil Nadu")
        if city_chain:
            queries.append(f"{first} {city_chain} Tamil Nadu")
        elif district:
            queries.append(f"{first} {district} Tamil Nadu")

    uppercase_variants = [candidate.upper() for candidate in queries if any(ch.isalpha() for ch in candidate)]
    queries.extend(uppercase_variants)

    deduped: list[str] = []
    seen: set[str] = set()
    for query in queries:
        query = query.strip(" ,")
        if query and query not in seen:
            seen.add(query)
            deduped.append(query)
    return deduped[:20]


def tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def name_score(original_name: str, candidate_title: str) -> tuple[float, list[str]]:
    original_tokens = tokenize(normalize_query(original_name))
    candidate_tokens = tokenize(normalize_query(candidate_title))
    if not candidate_tokens:
        return 0.0, ["missing_candidate_title"]

    common = set(original_tokens) & set(candidate_tokens)
    base = len(common) / max(len(set(original_tokens)), 1)
    reasons = [f"token_overlap={len(common)}/{len(set(original_tokens))}"]

    original_institution = {token for token in original_tokens if token in INSTITUTION_KEYWORDS}
    candidate_institution = {token for token in candidate_tokens if token in INSTITUTION_KEYWORDS}
    missing_institution = original_institution - candidate_institution
    if missing_institution:
        penalty = 0.12 * len(missing_institution)
        base -= penalty
        reasons.append(f"institution_penalty={sorted(missing_institution)}")
    elif original_institution:
        base += 0.08
        reasons.append("institution_match_bonus")

    base = max(0.0, min(base, 1.0))
    return base, reasons


def extract_location_hints(original_name: str) -> dict[str, list[str]]:
    cleaned = normalize_query(original_name)
    hints: dict[str, list[str]] = {"district": [], "taluk": [], "city": [], "pincode": []}

    for match in re.finditer(r"([A-Za-z][A-Za-z .'-]{1,40}?)\s+District\b", cleaned, flags=re.IGNORECASE):
        value = " ".join(tokenize(match.group(1)))
        if value:
            hints["district"].append(value)

    for match in re.finditer(r"([A-Za-z][A-Za-z .'-]{1,40}?)\s+Taluk\b", cleaned, flags=re.IGNORECASE):
        value = " ".join(tokenize(match.group(1)))
        if value:
            hints["taluk"].append(value)

    hints["pincode"] = re.findall(r"\b\d{6}\b", cleaned)

    parts = [part.strip() for part in cleaned.split(",") if part.strip()]
    if len(parts) > 1:
        for part in parts[1:]:
            lowered = part.lower()
            if "district" in lowered or "taluk" in lowered:
                continue
            city = compact_location_part(re.sub(r"\b\d{6}\b", " ", part))
            if city and len(city.split()) <= 5:
                hints["city"].append(city)

    for key in hints:
        deduped: list[str] = []
        seen: set[str] = set()
        for value in hints[key]:
            if value and value not in seen:
                seen.add(value)
                deduped.append(value)
        hints[key] = deduped
    return hints


def location_score(original_name: str, body_text: str) -> tuple[float, list[str], dict[str, Any]]:
    name_tokens = tokenize(normalize_query(original_name))
    body = body_text.lower()
    location_tokens = [token for token in name_tokens if token not in COMMON_STOPWORDS and token not in INSTITUTION_KEYWORDS and len(token) >= 4]
    matched = [token for token in location_tokens[:10] if token in body]

    hints = extract_location_hints(original_name)
    matched_pincode = [code for code in hints["pincode"] if code in body]
    matched_district = [value for value in hints["district"] if value in body]
    matched_taluk = [value for value in hints["taluk"] if value in body]
    matched_city = [value for value in hints["city"] if value in body]

    raw_score = min(
        0.55,
        0.04 * len(matched)
        + 0.22 * len(matched_pincode)
        + 0.14 * len(matched_district)
        + 0.10 * len(matched_taluk)
        + 0.08 * len(matched_city),
    )
    reasons: list[str] = []
    if matched:
        reasons.append(f"location_tokens={matched[:6]}")
    if matched_pincode:
        reasons.append(f"pincode_match={matched_pincode}")
    if matched_district:
        reasons.append(f"district_match={matched_district}")
    if matched_taluk:
        reasons.append(f"taluk_match={matched_taluk}")
    if matched_city:
        reasons.append(f"city_match={matched_city[:4]}")

    evidence = {
        "location_token_count": len(matched),
        "pincode_match": bool(matched_pincode),
        "district_match": bool(matched_district),
        "taluk_match": bool(matched_taluk),
        "city_match": bool(matched_city),
    }
    return raw_score, reasons, evidence


def signal_score(original_name: str, candidate_title: str, signals: dict[str, Any]) -> tuple[float, list[str], dict[str, Any]]:
    hints = extract_location_hints(original_name)
    address = (signals.get("address_snippet") or "").lower()
    category = (signals.get("category") or "").lower()
    pincode = signals.get("pincode") or ""
    website = (signals.get("website") or "").lower()

    original_tokens = set(tokenize(normalize_query(original_name)))
    candidate_tokens = set(tokenize(normalize_query(candidate_title)))
    institution_overlap = sorted((original_tokens & candidate_tokens) & INSTITUTION_KEYWORDS)
    wants_architecture = "architecture" in original_tokens
    wants_engineering = "engineering" in original_tokens

    score = 0.0
    reasons: list[str] = []

    if pincode and pincode in hints["pincode"]:
        score += 0.18
        reasons.append(f"signal_pincode_match={pincode}")
    if any(value in address for value in hints["district"]):
        score += 0.10
        reasons.append("signal_district_match")
    if any(value in address for value in hints["taluk"]):
        score += 0.08
        reasons.append("signal_taluk_match")
    if any(value in address for value in hints["city"]):
        score += 0.08
        reasons.append("signal_city_match")
    if institution_overlap:
        score += min(0.08, 0.03 * len(institution_overlap))
        reasons.append(f"signal_institution_overlap={institution_overlap}")
    if category:
        if wants_architecture and "architecture" in category:
            score += 0.08
            reasons.append(f"signal_category_match={category}")
        elif wants_engineering and ("engineering" in category or "college" in category or "technology" in category):
            score += 0.06
            reasons.append(f"signal_category_match={category}")
        elif any(token in category for token in ["college", "university", "institute", "school", "academy"]):
            score += 0.03
            reasons.append(f"signal_category_support={category}")
    if website.endswith(".ac.in") or website.endswith(".edu") or website.endswith(".edu.in"):
        score += 0.03
        reasons.append(f"signal_edu_website={website}")

    evidence = {
        "signal_pincode_match": bool(pincode and pincode in hints["pincode"]),
        "signal_district_match": any(value in address for value in hints["district"]),
        "signal_taluk_match": any(value in address for value in hints["taluk"]),
        "signal_city_match": any(value in address for value in hints["city"]),
        "signal_category": category or None,
        "signal_edu_website": bool(website.endswith(".ac.in") or website.endswith(".edu") or website.endswith(".edu.in")),
    }
    return min(score, 0.35), reasons, evidence


def institution_type_penalty(original_name: str, candidate_title: str, signals: dict[str, Any]) -> tuple[float, list[str], dict[str, Any]]:
    original_tokens = set(tokenize(normalize_query(original_name)))
    candidate_text = " ".join(
        part for part in [candidate_title.lower(), (signals.get("category") or "").lower(), (signals.get("address_snippet") or "").lower()]
        if part
    )

    wants_architecture = "architecture" in original_tokens
    wants_engineering = "engineering" in original_tokens
    wants_polytechnic = "polytechnic" in original_tokens
    wants_women = "women" in original_tokens or "womens" in original_tokens or "womens" in original_tokens

    penalties = 0.0
    reasons: list[str] = []

    if "trust" in candidate_text and "trust" not in original_tokens:
        penalties += 0.18
        reasons.append("penalty_trust_instead_of_institution")
    if ("arts and science" in candidate_text or "arts science" in candidate_text) and not ({"arts", "science"} & original_tokens):
        penalties += 0.18
        reasons.append("penalty_arts_science_mismatch")
    if "women" in candidate_text and not wants_women:
        penalties += 0.16
        reasons.append("penalty_womens_college_mismatch")
    if wants_architecture and "architecture" not in candidate_text:
        penalties += 0.20
        reasons.append("penalty_missing_architecture_type")
    if wants_polytechnic and "polytechnic" not in candidate_text:
        penalties += 0.18
        reasons.append("penalty_missing_polytechnic_type")
    if wants_engineering and not any(token in candidate_text for token in ["engineering", "technology", "engg"]):
        if any(token in candidate_text for token in ["arts and science", "women", "trust", "academy"]):
            penalties += 0.14
            reasons.append("penalty_missing_engineering_type")

    evidence = {
        "penalty_total": round(min(penalties, 0.45), 4),
        "candidate_type_text": candidate_text[:200] if candidate_text else None,
    }
    return min(penalties, 0.45), reasons, evidence


def score_candidate(original_name: str, candidate_title: str, body_text: str, coords: tuple[float, float] | None, signals: dict[str, Any] | None = None) -> tuple[float, bool, list[str]]:
    title_score, reasons = name_score(original_name, candidate_title)
    loc_score, loc_reasons, loc_evidence = location_score(original_name, body_text)
    signal_score_value, signal_reasons, signal_evidence = signal_score(original_name, candidate_title, signals or {})
    type_penalty_value, type_penalty_reasons, type_penalty_evidence = institution_type_penalty(original_name, candidate_title, signals or {})
    reasons.extend(loc_reasons)
    reasons.extend(signal_reasons)
    reasons.extend(type_penalty_reasons)
    total = title_score + loc_score + signal_score_value - type_penalty_value

    if not coords:
        reasons.append("missing_place_coords")
        return total, False, reasons

    lat, lng = coords
    if not within_bounds(lat, lng, INDIA_BOUNDS):
        reasons.append("outside_india")
        return total, False, reasons
    if not within_bounds(lat, lng, TAMIL_NADU_BOUNDS):
        reasons.append("outside_tamil_nadu")
        return total, False, reasons

    strong_location = (
        loc_evidence["pincode_match"]
        or signal_evidence["signal_pincode_match"]
        or (loc_evidence["district_match"] and (loc_evidence["city_match"] or loc_evidence["taluk_match"]))
        or (signal_evidence["signal_district_match"] and (signal_evidence["signal_city_match"] or signal_evidence["signal_taluk_match"]))
        or loc_evidence["location_token_count"] >= 4
    )
    strong_signals = signal_evidence["signal_pincode_match"] or signal_evidence["signal_edu_website"] or bool(signal_evidence["signal_category"])

    if title_score >= 0.55:
        reasons.append("accepted_tamil_nadu_match")
        return min(total + 0.1, 1.0), True, reasons

    if title_score >= 0.35 and strong_location and total >= 0.72:
        reasons.append("accepted_by_location_evidence")
        return min(total + 0.08, 1.0), True, reasons

    if title_score >= 0.28 and strong_location and strong_signals and total >= 0.8:
        reasons.append("accepted_by_structured_signals")
        return min(total + 0.08, 1.0), True, reasons

    reasons.append("low_name_score")
    return total, False, reasons


def candidate_to_dict(candidate: Candidate) -> dict[str, Any]:
    return {
        "query": candidate.query,
        "source": candidate.source,
        "title": candidate.title,
        "latitude": candidate.latitude,
        "longitude": candidate.longitude,
        "maps_url": candidate.maps_url,
        "score": round(candidate.score, 4),
        "accepted": candidate.accepted,
        "reasons": candidate.reasons,
        "signals": candidate.signals,
        "body_snippet": candidate.body_snippet,
    }


def extract_title_from_maps_url(url: str | None) -> str:
    if not url or "/maps/place/" not in url:
        return ""
    try:
        tail = url.split("/maps/place/", 1)[1]
        raw = tail.split("/", 1)[0]
        return clean_title(unquote(raw).replace("+", " "))
    except Exception:
        return ""


def existing_result_suspicious(original_name: str, maps_url: str | None) -> tuple[bool, list[str]]:
    candidate_title = extract_title_from_maps_url(maps_url)
    if not candidate_title:
        return False, []
    penalty_value, penalty_reasons, _ = institution_type_penalty(original_name, candidate_title, {})
    if penalty_value >= 0.16:
        return True, [f"existing_result_{reason}" for reason in penalty_reasons]
    return False, []


def write_lines(path: Path, records: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for item in records:
            name = first_name(item) or item.get("name") or ""
            lat = item.get("latitude")
            lng = item.get("longitude")
            if lat is None or lng is None:
                fh.write(f"{name},NOT_FOUND,NOT_FOUND,\n")
            else:
                fh.write(f"{name},{lat},{lng},\n")


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    data = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit("Input JSON must be an array of objects")

    corrected_from_url = 0
    reviewed_second_pass = 0
    corrected_second_pass = 0
    nulled_unmatched = 0
    unchanged = 0
    report_entries: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []

    # Stage 1: canonical place coords from existing maps_url
    stage1: list[dict[str, Any]] = []
    review_targets: list[tuple[int, dict[str, Any], dict[str, Any], list[str]]] = []
    for idx, item in enumerate(data):
        if not isinstance(item, dict):
            stage1.append(item)
            continue

        updated = dict(item)
        name = first_name(updated) or f"record_{idx}"
        old_lat = updated.get("latitude")
        old_lng = updated.get("longitude")
        maps_url = updated.get("maps_url") if isinstance(updated.get("maps_url"), str) else None
        notes: list[str] = []
        action = "unchanged"

        old_lat_f = float(old_lat) if isinstance(old_lat, (int, float)) else None
        old_lng_f = float(old_lng) if isinstance(old_lng, (int, float)) else None
        place = extract_coords(maps_url, PLACE_PATTERNS) if maps_url else None

        if place:
            needs_url_fix = (
                old_lat_f is None
                or old_lng_f is None
                or not within_bounds(old_lat_f, old_lng_f, INDIA_BOUNDS)
                or distance_meters(old_lat_f, old_lng_f, place[0], place[1]) > args.distance_threshold_m
            )
            if needs_url_fix:
                updated["latitude"] = place[0]
                updated["longitude"] = place[1]
                action = "autofixed_url_place"
                corrected_from_url += 1
                notes.append("Applied canonical place coordinates from existing maps_url.")

        lat = updated.get("latitude")
        lng = updated.get("longitude")
        lat_f = float(lat) if isinstance(lat, (int, float)) else None
        lng_f = float(lng) if isinstance(lng, (int, float)) else None

        suspicious_existing_result, suspicious_reasons = existing_result_suspicious(name, maps_url)
        needs_second_pass = (
            lat_f is None
            or lng_f is None
            or not within_bounds(lat_f, lng_f, INDIA_BOUNDS)
            or not within_bounds(lat_f, lng_f, TAMIL_NADU_BOUNDS)
            or suspicious_existing_result
        )
        if suspicious_reasons:
            notes.extend(suspicious_reasons)

        review_meta = {
            "initial_action": action,
            "notes": notes[:],
            "original_latitude": old_lat,
            "original_longitude": old_lng,
        }

        stage1.append(updated)
        if needs_second_pass:
            review_targets.append((idx, updated, review_meta, notes))
        else:
            unchanged += 1
            report_entries.append(
                {
                    "index": idx,
                    "name": name,
                    "final_action": action,
                    "final_latitude": lat_f,
                    "final_longitude": lng_f,
                    "notes": notes,
                }
            )

    # Stage 2: browser review only for remaining problematic records
    if review_targets:
        with MapsSecondPassReviewer(
            browser_name=args.browser,
            headless=args.headless,
            timeout_ms=args.timeout_ms,
            delay_seconds=args.delay_seconds,
        ) as reviewer:
            total = len(review_targets)
            for pos, (idx, item, review_meta, notes) in enumerate(review_targets, start=1):
                name = first_name(item) or f"record_{idx}"
                print(f"[{pos}/{total}] Reviewing: {name}")
                reviewed_second_pass += 1
                outcome = reviewer.search_best(name)
                if outcome.action == "corrected_second_pass":
                    item["latitude"] = outcome.latitude
                    item["longitude"] = outcome.longitude
                    item["maps_url"] = outcome.maps_url
                    corrected_second_pass += 1
                    notes.append(outcome.reason)
                    print(f"    -> corrected to {outcome.latitude}, {outcome.longitude}")
                else:
                    item["latitude"] = None
                    item["longitude"] = None
                    if outcome.maps_url:
                        item["maps_url"] = outcome.maps_url
                    nulled_unmatched += 1
                    notes.append(outcome.reason)
                    unresolved.append(
                        {
                            "index": idx,
                            "name": name,
                            "reason": outcome.reason,
                            "candidates": outcome.candidates,
                        }
                    )
                    print("    -> unresolved, coordinates nulled")

                item["review"] = {
                    **review_meta,
                    "final_action": outcome.action,
                    "reviewer_query": outcome.reviewer_query,
                    "confidence": outcome.confidence,
                    "notes": notes,
                }
                report_entries.append(
                    {
                        "index": idx,
                        "name": name,
                        "final_action": outcome.action,
                        "final_latitude": item.get("latitude"),
                        "final_longitude": item.get("longitude"),
                        "reviewer_query": outcome.reviewer_query,
                        "confidence": outcome.confidence,
                        "notes": notes,
                        "candidates": outcome.candidates,
                    }
                )
    
    stem = input_path.with_suffix("")
    final_json = stem.with_name(stem.name + "_final_cleaned.json")
    final_lines = stem.with_name(stem.name + "_final_cleaned_lines.txt")
    final_report = stem.with_name(stem.name + "_final_review_report.json")
    final_unresolved = stem.with_name(stem.name + "_final_unresolved.json")

    final_json.write_text(json.dumps(stage1, ensure_ascii=False, indent=2), encoding="utf-8")
    write_lines(final_lines, [item for item in stage1 if isinstance(item, dict)])
    final_unresolved.write_text(json.dumps(unresolved, ensure_ascii=False, indent=2), encoding="utf-8")
    final_report.write_text(
        json.dumps(
            {
                "summary": {
                    "input": str(input_path),
                    "total_records": len(data),
                    "autofixed_from_url": corrected_from_url,
                    "reviewed_second_pass": reviewed_second_pass,
                    "corrected_second_pass": corrected_second_pass,
                    "nulled_unmatched": nulled_unmatched,
                    "unchanged_after_review": unchanged,
                },
                "entries": report_entries,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\nDone.")
    print(f"Autofixed from URL: {corrected_from_url}")
    print(f"Second-pass reviewed: {reviewed_second_pass}")
    print(f"Second-pass corrected: {corrected_second_pass}")
    print(f"Nulled unresolved: {nulled_unmatched}")
    print(f"Final JSON: {final_json}")
    print(f"Final lines: {final_lines}")
    print(f"Report: {final_report}")
    print(f"Unresolved: {final_unresolved}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
