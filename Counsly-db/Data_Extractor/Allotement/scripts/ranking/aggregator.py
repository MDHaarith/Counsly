"""
Aggregate dimension scores into final college rankings.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import COMMUNITIES, WEIGHTS

logger = logging.getLogger(__name__)

# Strongly evidence-based dimensions should be penalized when missing.
PENALIZED_MISSING_DIMS = {"selectivity", "academic_quality", "branch_strength"}

# Trend is directional, not absolute quality. Missing trend should stay neutral.
NEUTRAL_MISSING_DIMS = {"trend", "web_reputation"}


def compute_composite_score(
    dimension_scores: dict[str, pd.DataFrame],
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Merge all dimension tables and compute the weighted composite score."""
    w = weights or WEIGHTS
    if not dimension_scores:
        return pd.DataFrame()

    college_codes: set[str] = set()
    for dim_df in dimension_scores.values():
        if dim_df.empty or "college_code" not in dim_df.columns:
            continue
        college_codes.update(dim_df["college_code"].astype(str).tolist())

    if not college_codes:
        return pd.DataFrame()

    result = pd.DataFrame({"college_code": sorted(college_codes)})

    for dim_name, dim_df in dimension_scores.items():
        score_col = f"{dim_name}_score"
        if dim_df.empty or score_col not in dim_df.columns:
            continue
        merge_df = dim_df[["college_code", score_col]].copy()
        merge_df["college_code"] = merge_df["college_code"].astype(str)
        result = result.merge(merge_df, on="college_code", how="left")

    for dim_name in w:
        score_col = f"{dim_name}_score"
        if score_col not in result.columns:
            result[score_col] = np.nan

        if dim_name in PENALIZED_MISSING_DIMS:
            fill_value = result[score_col].quantile(0.15)
            if pd.isna(fill_value):
                fill_value = 15.0
        elif dim_name in NEUTRAL_MISSING_DIMS:
            fill_value = 50.0
        else:
            fill_value = result[score_col].median()
            if pd.isna(fill_value):
                fill_value = 50.0

        result[score_col] = result[score_col].fillna(fill_value)

    composite = np.zeros(len(result), dtype=float)
    for dim_name, weight in w.items():
        score_col = f"{dim_name}_score"
        composite += result[score_col].to_numpy(dtype=float) * float(weight)

    result["composite_score"] = composite.clip(0, 100)
    result = result.sort_values(
        ["composite_score", "college_code"],
        ascending=[False, True],
    ).reset_index(drop=True)
    result["rank"] = result["composite_score"].rank(
        ascending=False,
        method="min",
    ).astype(int)

    logger.info("Composite ranking computed for %s colleges", len(result))
    return result


def generate_community_rankings(
    allotment: pd.DataFrame,
    college_info: pd.DataFrame,
    scraped_data: dict[str, dict],
    dimension_compute_fn,
    weights: dict[str, float] | None = None,
) -> dict[str, pd.DataFrame]:
    """Generate rankings for each major community bucket."""
    w = weights or WEIGHTS
    rankings: dict[str, pd.DataFrame] = {}

    for community in COMMUNITIES:
        community_allotment = allotment[allotment["COMMUNITY"] == community]
        if community_allotment.empty:
            continue

        scores = dimension_compute_fn(
            allotment=community_allotment,
            college_info=college_info,
            scraped_data=scraped_data,
        )
        rankings[community] = compute_composite_score(scores, w)
        logger.info("Community %s: ranked %s colleges", community, len(rankings[community]))

    return rankings


def generate_branch_rankings(
    allotment: pd.DataFrame,
    college_info: pd.DataFrame,
    scraped_data: dict[str, dict],
    dimension_compute_fn,
    weights: dict[str, float] | None = None,
    top_branches: int | None = None,
) -> dict[str, pd.DataFrame]:
    """Generate rankings within each branch."""
    w = weights or WEIGHTS

    branch_counts = allotment.groupby("BRANCH_CODE").size().sort_values(ascending=False)
    if top_branches:
        branches = branch_counts.head(top_branches).index.tolist()
    else:
        branches = branch_counts[branch_counts >= 100].index.tolist()

    rankings: dict[str, pd.DataFrame] = {}
    for branch in branches:
        branch_allotment = allotment[allotment["BRANCH_CODE"] == branch]
        if branch_allotment.empty:
            continue

        branch_colleges = set(branch_allotment["COLLEGE_CODE"].astype(str))
        branch_info = college_info[college_info["college_code"].isin(branch_colleges)]

        scores = dimension_compute_fn(
            allotment=branch_allotment,
            college_info=branch_info,
            scraped_data=scraped_data,
        )
        rankings[branch] = compute_composite_score(scores, w)

    logger.info("Generated branch rankings for %s branches", len(rankings))
    return rankings


def generate_district_rankings(
    overall_rankings: pd.DataFrame,
    college_info: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Split the overall ranking into district-level views."""
    merged = overall_rankings.merge(
        college_info[["college_code", "district_clean"]],
        on="college_code",
        how="left",
    )
    merged["district_clean"] = merged["district_clean"].fillna("Unknown")

    rankings: dict[str, pd.DataFrame] = {}
    for district, group in merged.groupby("district_clean"):
        if not district or district == "Unknown":
            continue
        group = group.copy().sort_values(
            ["composite_score", "college_code"],
            ascending=[False, True],
        )
        group["rank"] = group["composite_score"].rank(
            ascending=False,
            method="min",
        ).astype(int)
        rankings[district] = group

    logger.info("Generated district rankings for %s districts", len(rankings))
    return rankings
