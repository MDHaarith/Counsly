"""
Web scraper for college website quality signals.

The scraper is intentionally a support source, not the dominant ranking signal.
Its job is to extract a few coarse public indicators and cache them.
"""

from __future__ import annotations

import json
import logging
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from .config import (
    CTC_PATTERN,
    FACULTY_PATTERN,
    NAAC_PATTERN,
    NIRF_PATTERN,
    PLACEMENT_PCT_PATTERN,
    RESEARCH_PATTERN,
    SCRAPE_CACHE_DIR,
    SCRAPE_MAX_WORKERS,
    SCRAPE_PATHS,
    SCRAPE_RETRIES,
    SCRAPE_TIMEOUT,
    SCRAPE_USER_AGENT,
)

logger = logging.getLogger(__name__)


def scrape_all_colleges(
    college_urls: dict[str, str],
    skip_existing: bool = True,
    max_colleges: int | None = None,
) -> dict[str, dict]:
    """Scrape colleges in parallel and cache per-college results."""
    SCRAPE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}

    targets = {
        str(code).strip(): str(url).strip()
        for code, url in college_urls.items()
        if str(code).strip()
    }
    if max_colleges is not None:
        targets = dict(list(targets.items())[:max_colleges])

    todo: list[tuple[str, str]] = []
    skipped = 0
    for code, url in targets.items():
        cache_file = SCRAPE_CACHE_DIR / f"{code}.json"
        if skip_existing and cache_file.exists():
            try:
                with cache_file.open("r", encoding="utf-8") as handle:
                    results[code] = json.load(handle)
                skipped += 1
                continue
            except (json.JSONDecodeError, OSError):
                pass
        todo.append((code, url))

    if not todo:
        logger.info("Scraping skipped entirely: all %s colleges loaded from cache", len(results))
        return results

    logger.info(
        "Scraping %s colleges with %s workers (%s loaded from cache)",
        len(todo),
        SCRAPE_MAX_WORKERS,
        skipped,
    )

    scraped = 0
    failed = 0
    with ThreadPoolExecutor(max_workers=SCRAPE_MAX_WORKERS) as executor:
        future_map = {
            executor.submit(_scrape_one, code, url): (code, url)
            for code, url in todo
        }
        for future in as_completed(future_map):
            code, _ = future_map[future]
            try:
                data = future.result()
                results[code] = data
                scraped += 1
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to scrape college %s: %s", code, exc)
                results[code] = _neutral_result(code=code)
                results[code]["error"] = str(exc)
                failed += 1

    logger.info(
        "Scraping complete: %s scraped, %s cached/skipped, %s failed, %s total",
        scraped,
        skipped,
        failed,
        len(targets),
    )
    return results


def scrape_college(session: requests.Session, code: str, base_url: str) -> dict:
    """Scrape a single college website and extract coarse public signals."""
    result = _neutral_result(code=code)
    result["website"] = base_url

    all_text = []
    for path in SCRAPE_PATHS:
        url = base_url.rstrip("/") + path
        text = _fetch_page(session, url)
        if text:
            all_text.append(text)

    merged_text = "\n".join(all_text).strip()
    if not merged_text:
        result["error"] = "No pages could be fetched"
        return result

    result["naac_grade"] = _extract_naac(merged_text)
    result["nirf_rank"] = _extract_nirf(merged_text)
    result["faculty_count"] = _extract_faculty(merged_text)
    result["avg_ctc"] = _extract_ctc(merged_text)
    result["placement_pct_web"] = _extract_placement_pct(merged_text)
    result["research_count"] = _extract_research(merged_text)
    result["scraped"] = True
    result["scraped_at_epoch"] = int(time.time())
    return result


def load_cached_results() -> dict[str, dict]:
    """Load all cached scrape results from disk."""
    results: dict[str, dict] = {}
    if not SCRAPE_CACHE_DIR.exists():
        return results

    for cache_file in SCRAPE_CACHE_DIR.glob("*.json"):
        code = cache_file.stem
        try:
            with cache_file.open("r", encoding="utf-8") as handle:
                results[code] = json.load(handle)
        except (json.JSONDecodeError, OSError):
            continue

    return results


def _scrape_one(code: str, url: str) -> dict:
    if not url:
        return _neutral_result(code=code)

    cache_file = SCRAPE_CACHE_DIR / f"{code}.json"
    session = requests.Session()
    session.headers.update({"User-Agent": SCRAPE_USER_AGENT})
    try:
        data = scrape_college(session, code, url)
    finally:
        session.close()

    with cache_file.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
    return data


def _fetch_page(session: requests.Session, url: str) -> str | None:
    for attempt in range(SCRAPE_RETRIES + 1):
        try:
            response = session.get(url, timeout=SCRAPE_TIMEOUT, allow_redirects=True)
            if response.status_code != 200:
                return None
            soup = BeautifulSoup(response.text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            return soup.get_text(separator=" ", strip=True)
        except requests.RequestException:
            if attempt == SCRAPE_RETRIES:
                return None
            time.sleep(0.3)
    return None


def _extract_naac(text: str) -> str | None:
    match = re.search(NAAC_PATTERN, text, re.IGNORECASE)
    return match.group(1).strip().upper() if match else None


def _extract_nirf(text: str) -> int | None:
    match = re.search(NIRF_PATTERN, text, re.IGNORECASE)
    if not match:
        return None
    try:
        rank = int(match.group(1))
    except ValueError:
        return None
    return rank if 1 <= rank <= 500 else None


def _extract_faculty(text: str) -> int | None:
    matches = re.findall(FACULTY_PATTERN, text, re.IGNORECASE)
    if not matches:
        return None
    values = [int(value) for value in matches if int(value) < 10000]
    return max(values) if values else None


def _extract_ctc(text: str) -> float | None:
    match = re.search(CTC_PATTERN, text, re.IGNORECASE)
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    return value if 0 <= value <= 100 else None


def _extract_placement_pct(text: str) -> float | None:
    match = re.search(PLACEMENT_PCT_PATTERN, text, re.IGNORECASE)
    if not match:
        return None
    try:
        value = float(match.group(1))
    except ValueError:
        return None
    return value if 0 <= value <= 100 else None


def _extract_research(text: str) -> int | None:
    matches = re.findall(RESEARCH_PATTERN, text, re.IGNORECASE)
    if not matches:
        return None
    values = [int(value) for value in matches if int(value) < 100000]
    return max(values) if values else None


def _neutral_result(code: str = "") -> dict:
    return {
        "college_code": code,
        "website": "",
        "naac_grade": None,
        "nirf_rank": None,
        "faculty_count": None,
        "avg_ctc": None,
        "placement_pct_web": None,
        "research_count": None,
        "scraped": False,
        "error": None,
    }
