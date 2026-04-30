#!/usr/bin/env python3
"""
Canonical TNEA college ranking CLI.

This version ranks colleges from the cleaned allotment dataset plus reference
metadata and cached/live web-scrape evidence. Seat-matrix signals are not used.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ranking.aggregator import (  # noqa: E402
    compute_composite_score,
    generate_branch_rankings,
    generate_community_rankings,
    generate_district_rankings,
)
from ranking.config import RANKINGS_DIR  # noqa: E402
from ranking.data_loader import load_allotment_data, load_college_info  # noqa: E402
from ranking.dimensions import (  # noqa: E402
    compute_academic_quality,
    compute_branch_strength,
    compute_institutional_quality,
    compute_selectivity,
    compute_trend,
    compute_web_reputation,
)
from ranking.output import generate_output  # noqa: E402
from ranking.scraper import load_cached_results, scrape_all_colleges  # noqa: E402


def setup_logging(verbose: bool = False) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def compute_all_dimensions(
    allotment,
    college_info,
    scraped_data,
) -> dict[str, "pd.DataFrame"]:
    """Compute the canonical ranking dimensions."""
    logger = logging.getLogger(__name__)
    logger.info("Computing ranking dimensions...")
    allowed_codes = set(college_info["college_code"].astype(str))
    scoped_scraped_data = {
        str(code): payload
        for code, payload in scraped_data.items()
        if str(code) in allowed_codes
    }

    return {
        "selectivity": compute_selectivity(allotment),
        "academic_quality": compute_academic_quality(allotment),
        "branch_strength": compute_branch_strength(allotment),
        "institutional_quality": compute_institutional_quality(college_info),
        "web_reputation": compute_web_reputation(scoped_scraped_data),
        "trend": compute_trend(allotment),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Rank TNEA colleges using the cleaned canonical algorithm",
    )
    parser.add_argument("--college", type=str, default=None, help="Rank only a specific college code")
    parser.add_argument(
        "--community",
        type=str,
        default=None,
        choices=["OC", "BC", "BCM", "MBC", "SC", "ST"],
        help="Print the ranking view for one community after generation",
    )
    parser.add_argument("--branch", type=str, default=None, help="Print the ranking view for one branch")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output JSON path")
    parser.add_argument(
        "--skip-scrape",
        action="store_true",
        help="Skip live scraping and use only cached scrape results if present",
    )
    parser.add_argument(
        "--max-scrape",
        type=int,
        default=None,
        help="Limit how many colleges are scraped live",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    logger.info("Loading ranking inputs...")
    allotment = load_allotment_data()
    college_info = load_college_info()

    if args.college:
        code = str(args.college).strip()
        allotment = allotment[allotment["COLLEGE_CODE"].astype(str) == code]
        college_info = college_info[college_info["college_code"] == code]
        logger.info("Filtered to college %s", code)

    if allotment.empty or college_info.empty:
        logger.error("No data available after filters")
        return 1

    logger.info("Allotment rows: %s", len(allotment))
    logger.info("College metadata rows: %s", len(college_info))

    college_urls = dict(
        zip(
            college_info["college_code"].astype(str),
            college_info["website"].fillna("").astype(str),
        )
    )
    if args.skip_scrape:
        logger.info("Loading cached scrape results only...")
        scraped_data = load_cached_results()
    else:
        scraped_data = scrape_all_colleges(
            college_urls=college_urls,
            skip_existing=True,
            max_colleges=args.max_scrape,
        )

    scores = compute_all_dimensions(allotment, college_info, scraped_data)
    overall = compute_composite_score(scores)

    community_rankings = {}
    branch_rankings = {}
    district_rankings = {}

    if not args.college:
        community_rankings = generate_community_rankings(
            allotment=allotment,
            college_info=college_info,
            scraped_data=scraped_data,
            dimension_compute_fn=compute_all_dimensions,
        )

        if args.branch:
            branch_data = allotment[allotment["BRANCH_CODE"] == args.branch]
            branch_colleges = set(branch_data["COLLEGE_CODE"].astype(str))
            branch_info = college_info[college_info["college_code"].isin(branch_colleges)]
            branch_scores = compute_all_dimensions(branch_data, branch_info, scraped_data)
            branch_rankings[args.branch] = compute_composite_score(branch_scores)
        else:
            branch_rankings = generate_branch_rankings(
                allotment=allotment,
                college_info=college_info,
                scraped_data=scraped_data,
                dimension_compute_fn=compute_all_dimensions,
                top_branches=20,
            )

        district_rankings = generate_district_rankings(overall, college_info)

    output_path = Path(args.output) if args.output else None
    result_path = generate_output(
        overall=overall,
        community_rankings=community_rankings,
        branch_rankings=branch_rankings,
        district_rankings=district_rankings,
        college_info=college_info,
        scraped_data=scraped_data,
        output_path=output_path,
    )

    logger.info("=" * 70)
    logger.info("TOP 15 COLLEGES")
    logger.info("=" * 70)
    for _, row in overall.head(15).iterrows():
        code = str(row["college_code"])
        info = college_info[college_info["college_code"] == code]
        name = info.iloc[0]["college_name"] if not info.empty else code
        logger.info(
            "#%3s  %6.2f  %-58s SEL=%5.1f ACD=%5.1f WEB=%5.1f",
            int(row["rank"]),
            float(row["composite_score"]),
            name[:58],
            float(row.get("selectivity_score", 0)),
            float(row.get("academic_quality_score", 0)),
            float(row.get("web_reputation_score", 0)),
        )

    if args.community and args.community in community_rankings:
        logger.info("Community %s top 10:", args.community)
        for _, row in community_rankings[args.community].head(10).iterrows():
            code = str(row["college_code"])
            info = college_info[college_info["college_code"] == code]
            name = info.iloc[0]["college_name"] if not info.empty else code
            logger.info("  #%3s %6.2f %s", int(row["rank"]), float(row["composite_score"]), name)

    if args.branch and args.branch in branch_rankings:
        logger.info("Branch %s top 10:", args.branch)
        for _, row in branch_rankings[args.branch].head(10).iterrows():
            code = str(row["college_code"])
            info = college_info[college_info["college_code"] == code]
            name = info.iloc[0]["college_name"] if not info.empty else code
            logger.info("  #%3s %6.2f %s", int(row["rank"]), float(row["composite_score"]), name)

    logger.info("=" * 70)
    logger.info("Output: %s", result_path or (RANKINGS_DIR / "college_rankings.json"))
    logger.info("Total colleges ranked: %s", len(overall))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
