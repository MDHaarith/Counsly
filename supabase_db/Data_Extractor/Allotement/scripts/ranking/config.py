"""
Configuration for the canonical TNEA college ranking algorithm.

The ranking is intentionally driven by the clean allotment data first, with
reference metadata and website-scrape evidence used only as capped support
signals.
"""

from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────

ALLOTMENT_DIR = Path(__file__).resolve().parents[2]  # Inputs/Allotement/
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # Inputs/
DATA_DIR = ALLOTMENT_DIR / "data"
RANKINGS_DIR = DATA_DIR / "rankings"
SCRAPE_CACHE_DIR = RANKINGS_DIR / "scraped_cache"

ALLOTMENT_CSV = (
    DATA_DIR
    / "processed"
    / "merged"
    / "merged_records_all_years_rounds_training_ready.csv"
)

RAW_COLLEGE_INFO_JSON = PROJECT_ROOT / "College_Info_Done" / "output.json"
FILTERED_COLLEGE_INFO_JSON = (
    PROJECT_ROOT / "College_Info_Done" / "output_present_non_architecture.json"
)
COLLEGE_INFO_JSON = (
    FILTERED_COLLEGE_INFO_JSON
    if FILTERED_COLLEGE_INFO_JSON.exists()
    else RAW_COLLEGE_INFO_JSON
)

# ── Dimension Weights ──────────────────────────────────────────────────────────

WEIGHTS = {
    "selectivity": 0.35,
    "academic_quality": 0.35,
    "branch_strength": 0.12,
    "institutional_quality": 0.08,
    "web_reputation": 0.06,
    "trend": 0.04,
}

# ── Ranking Windows ────────────────────────────────────────────────────────────

RANKING_ROUND = 1
RECENCY_WEIGHTS = {2025: 0.50, 2024: 0.30, 2023: 0.20}
RECENT_YEARS = sorted(RECENCY_WEIGHTS.keys())

TREND_YEARS = [2020, 2021, 2022, 2023, 2024, 2025]
TREND_MIN_YEARS = 3

MIN_BRANCH_PEERS = 5

# ── Communities ────────────────────────────────────────────────────────────────

COMMUNITIES = ["OC", "BC", "BCM", "MBC", "SC", "ST"]

# ── Scraping ───────────────────────────────────────────────────────────────────

SCRAPE_MAX_WORKERS = 10
SCRAPE_TIMEOUT = 6
SCRAPE_RETRIES = 1
SCRAPE_USER_AGENT = (
    "TNEA-College-Ranking-Bot/3.0 "
    "(Academic Research; +https://github.com/tnea-data-extractor)"
)
SCRAPE_PATHS = ["", "/about", "/placements", "/placement", "/naac", "/nirf"]

NAAC_PATTERN = r"NAAC\s*(?:Grade|Rating|Accreditation)?\s*[:\-]?\s*([ABCD][\+\+]?)"
NIRF_PATTERN = r"NIRF\s*(?:Rank|Ranking)?\s*[:\-]?\s*(\d+)"
FACULTY_PATTERN = r"(\d+)\s*(?:Faculty|Faculty Members|Teaching Staff|Professors)"
CTC_PATTERN = r"(?:Avg|Average|Highest|Mean)\s*(?:CTC|Package|Salary)\s*[:\-]?\s*[\u20b9$]?\s*([\d.]+)\s*(?:LPA|Lakhs|L)"
PLACEMENT_PCT_PATTERN = r"(\d+(?:\.\d+)?)\s*%\s*(?:placed|placement|students placed)"
RESEARCH_PATTERN = r"(\d+)\s*(?:Publications|Research Papers|Patents|Funded Projects)"
