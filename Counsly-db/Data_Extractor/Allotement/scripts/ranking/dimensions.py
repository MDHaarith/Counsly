"""
Dimension scoring for the canonical TNEA college ranking algorithm.

The ranking is intentionally anchored to actual allotment behavior:
- who joins the college,
- how competitive the college is,
- how strong its branches are,
- and whether the institution shows accredited program depth.
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import (
    MIN_BRANCH_PEERS,
    RANKING_ROUND,
    RECENCY_WEIGHTS,
    RECENT_YEARS,
    TREND_MIN_YEARS,
    TREND_YEARS,
)

logger = logging.getLogger(__name__)

NAAC_GRADE_POINTS = {
    "A++": 100.0,
    "A+": 90.0,
    "A": 80.0,
    "B++": 70.0,
    "B+": 60.0,
    "B": 50.0,
    "C": 35.0,
    "D": 20.0,
}


def percentile_rank(
    series: pd.Series,
    higher_is_better: bool = True,
) -> pd.Series:
    """Convert raw values into 0-100 percentile ranks."""
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.nunique(dropna=True) <= 1:
        return pd.Series(50.0, index=series.index, dtype=float)

    ranks = numeric.rank(pct=True, method="average") * 100
    return ranks if higher_is_better else 100 - ranks


def compute_selectivity(allotment: pd.DataFrame) -> pd.DataFrame:
    """
    Rank colleges by the quality of ranks they attract in round 1.

    Uses within-year percentiles so each year is judged against its own field,
    then recency-weights 2023-2025.
    """
    yearly = _build_college_year_metrics(allotment, RECENT_YEARS)
    if yearly.empty:
        return pd.DataFrame(columns=["college_code", "selectivity_score"])

    scored = []
    for year, group in yearly.groupby("YEAR"):
        group = group.copy()
        raw_score = (
            percentile_rank(group["median_rank"], higher_is_better=False) * 0.50
            + percentile_rank(group["q75_rank"], higher_is_better=False) * 0.35
            + percentile_rank(group["q25_rank"], higher_is_better=False) * 0.15
        )
        group["selectivity_year_score"] = _shrink_to_neutral(
            raw_score,
            strength=group["admitted_students"],
            full_strength_at=150,
        )
        scored.append(group)

    scored_df = pd.concat(scored, ignore_index=True)
    result = _weighted_recent_average(scored_df, "selectivity_year_score", "selectivity_score")

    logger.info("Selectivity: scored %s colleges", len(result))
    return result


def compute_academic_quality(allotment: pd.DataFrame) -> pd.DataFrame:
    """
    Rank colleges by the aggregate marks of round-1 admitted students.

    Marks are less noisy than raw opening ranks for tie-heavy regions, so they
    complement selectivity without double-counting it entirely.
    """
    yearly = _build_college_year_metrics(allotment, RECENT_YEARS)
    if yearly.empty:
        return pd.DataFrame(columns=["college_code", "academic_quality_score"])

    scored = []
    for year, group in yearly.groupby("YEAR"):
        group = group.copy()
        raw_score = (
            percentile_rank(group["median_mark"], higher_is_better=True) * 0.60
            + percentile_rank(group["q75_mark"], higher_is_better=True) * 0.40
        )
        group["academic_quality_year_score"] = _shrink_to_neutral(
            raw_score,
            strength=group["admitted_students"],
            full_strength_at=150,
        )
        scored.append(group)

    scored_df = pd.concat(scored, ignore_index=True)
    result = _weighted_recent_average(
        scored_df,
        "academic_quality_year_score",
        "academic_quality_score",
    )

    logger.info("Academic quality: scored %s colleges", len(result))
    return result


def compute_branch_strength(allotment: pd.DataFrame) -> pd.DataFrame:
    """
    Measure how strong a college's branches are relative to direct peers.

    This is computed branch-by-branch, year-by-year, only when enough colleges
    offer the branch. It protects the ranking from being driven entirely by the
    college's branch mix.
    """
    round_one = _filter_round_and_years(allotment, RECENT_YEARS)
    if round_one.empty:
        return pd.DataFrame(columns=["college_code", "branch_strength_score"])

    branch_year = (
        round_one.groupby(["YEAR", "BRANCH_CODE", "COLLEGE_CODE"])
        .agg(
            branch_closing_rank=("RANK", lambda s: s.quantile(0.90)),
            admissions=("RANK", "size"),
        )
        .reset_index()
    )

    scored_groups = []
    for (_, _), group in branch_year.groupby(["YEAR", "BRANCH_CODE"]):
        if len(group) < MIN_BRANCH_PEERS:
            continue

        group = group.copy()
        group["branch_peer_score"] = percentile_rank(
            group["branch_closing_rank"],
            higher_is_better=False,
        )
        scored_groups.append(group)

    if not scored_groups:
        return pd.DataFrame(columns=["college_code", "branch_strength_score"])

    scored_df = pd.concat(scored_groups, ignore_index=True)
    scored_df["college_code"] = scored_df["COLLEGE_CODE"].astype(str)
    scored_df["combined_weight"] = (
        scored_df["YEAR"].map(RECENCY_WEIGHTS).fillna(0.0)
        * scored_df["admissions"].clip(lower=1)
    )

    records = []
    for college_code, group in scored_df.groupby("college_code"):
        weights = group["combined_weight"].to_numpy(dtype=float)
        scores = group["branch_peer_score"].to_numpy(dtype=float)
        if weights.sum() <= 0:
            value = float(np.nanmean(scores))
        else:
            value = float(np.average(scores, weights=weights))
        value = _shrink_scalar_to_neutral(
            value,
            strength=float(weights.sum()),
            full_strength_at=150,
        )
        records.append(
            {
                "college_code": str(college_code),
                "branch_strength_score": value,
            }
        )

    result = pd.DataFrame(records)
    logger.info("Branch strength: scored %s colleges", len(result))
    return result


def compute_institutional_quality(college_info: pd.DataFrame) -> pd.DataFrame:
    """
    Score colleges using relatively reliable institution-side metadata.

    This signal is intentionally capped at 10% overall so self-reported metadata
    cannot overpower allotment behavior.
    """
    if college_info.empty:
        return pd.DataFrame(columns=["college_code", "institutional_quality_score"])

    df = college_info[
        [
            "college_code",
            "nba_accredited_ratio",
            "placement_pct",
            "is_autonomous",
        ]
    ].copy()

    df["nba_accredited_ratio"] = pd.to_numeric(
        df["nba_accredited_ratio"],
        errors="coerce",
    )
    df["placement_pct"] = pd.to_numeric(df["placement_pct"], errors="coerce")
    df["nba_accredited_ratio"] = df["nba_accredited_ratio"].fillna(
        df["nba_accredited_ratio"].median()
    )
    df["placement_pct"] = df["placement_pct"].fillna(df["placement_pct"].median())
    df["autonomy_score"] = df["is_autonomous"].astype(float) * 100

    df["institutional_quality_score"] = (
        percentile_rank(df["nba_accredited_ratio"], higher_is_better=True) * 0.55
        + percentile_rank(df["placement_pct"], higher_is_better=True) * 0.30
        + df["autonomy_score"] * 0.15
    ).clip(0, 100)

    logger.info("Institutional quality: scored %s colleges", len(df))
    return df[["college_code", "institutional_quality_score"]]


def compute_web_reputation(scraped_data: dict[str, dict]) -> pd.DataFrame:
    """
    Score colleges from scraped website evidence.

    This stays capped and reliability-adjusted because website content is noisy.
    """
    if not scraped_data:
        return pd.DataFrame(columns=["college_code", "web_reputation_score"])

    rows = []
    for code, payload in scraped_data.items():
        if not isinstance(payload, dict):
            continue
        rows.append(
            {
                "college_code": str(code).strip(),
                "naac_grade": str(payload.get("naac_grade") or "").strip().upper(),
                "nirf_rank": pd.to_numeric(payload.get("nirf_rank"), errors="coerce"),
                "faculty_count": pd.to_numeric(payload.get("faculty_count"), errors="coerce"),
                "avg_ctc": pd.to_numeric(payload.get("avg_ctc"), errors="coerce"),
                "placement_pct_web": pd.to_numeric(payload.get("placement_pct_web"), errors="coerce"),
                "research_count": pd.to_numeric(payload.get("research_count"), errors="coerce"),
                "scraped": bool(payload.get("scraped")),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return pd.DataFrame(columns=["college_code", "web_reputation_score"])

    df["naac_score"] = df["naac_grade"].map(NAAC_GRADE_POINTS)

    available_scores: list[pd.Series] = []

    def add_component(column: str, higher_is_better: bool, weight: float):
        available = df[column].notna()
        component = pd.Series(50.0, index=df.index, dtype=float)
        if available.any():
            component.loc[available] = percentile_rank(
                df.loc[available, column],
                higher_is_better=higher_is_better,
            )
        available_scores.append((component, available, weight))

    add_component("naac_score", True, 0.30)
    add_component("nirf_rank", False, 0.25)
    add_component("placement_pct_web", True, 0.15)
    add_component("avg_ctc", True, 0.15)
    add_component("research_count", True, 0.10)
    add_component("faculty_count", True, 0.05)

    total_score = pd.Series(0.0, index=df.index, dtype=float)
    observed_weight = pd.Series(0.0, index=df.index, dtype=float)
    observed_count = pd.Series(0.0, index=df.index, dtype=float)

    for component, available, weight in available_scores:
        total_score += component * weight
        observed_weight += available.astype(float) * weight
        observed_count += available.astype(float)

    weight_reliability = (observed_weight / observed_weight.max()).fillna(0.0).clip(0.0, 1.0)
    metric_reliability = _reliability(observed_count, full_strength_at=4.0)
    scrape_reliability = df["scraped"].astype(float)
    combined_reliability = np.sqrt(weight_reliability * metric_reliability * scrape_reliability)
    df["web_reputation_score"] = 50.0 + (total_score - 50.0) * combined_reliability

    logger.info(
        "Web reputation: scored %s colleges, %s with at least one scraped signal",
        len(df),
        int((observed_count > 0).sum()),
    )
    return df[["college_code", "web_reputation_score"]]


def compute_trend(allotment: pd.DataFrame) -> pd.DataFrame:
    """Score colleges by improvement in selectivity over 2020-2025."""
    yearly = _build_college_year_metrics(allotment, TREND_YEARS)
    if yearly.empty:
        return pd.DataFrame(columns=["college_code", "trend_score"])

    scored = []
    for year, group in yearly.groupby("YEAR"):
        group = group.copy()
        raw_score = (
            percentile_rank(group["median_rank"], higher_is_better=False) * 0.50
            + percentile_rank(group["q75_rank"], higher_is_better=False) * 0.35
            + percentile_rank(group["q25_rank"], higher_is_better=False) * 0.15
        )
        group["selectivity_year_score"] = _shrink_to_neutral(
            raw_score,
            strength=group["admitted_students"],
            full_strength_at=150,
        )
        scored.append(group)

    scored_df = pd.concat(scored, ignore_index=True)
    records = []
    for college_code, group in scored_df.groupby("college_code"):
        if len(group) < TREND_MIN_YEARS:
            continue

        group = group.sort_values("YEAR")
        years = group["YEAR"].to_numpy(dtype=float)
        scores = group["selectivity_year_score"].to_numpy(dtype=float)
        slope = float(np.polyfit(years, scores, 1)[0])
        records.append({"college_code": str(college_code), "trend_raw": slope})

    if not records:
        return pd.DataFrame(columns=["college_code", "trend_score"])

    trend = pd.DataFrame(records)
    trend["trend_score"] = percentile_rank(trend["trend_raw"], higher_is_better=True)

    logger.info("Trend: scored %s colleges", len(trend))
    return trend[["college_code", "trend_score"]]


def _build_college_year_metrics(
    allotment: pd.DataFrame,
    years: list[int],
) -> pd.DataFrame:
    round_one = _filter_round_and_years(allotment, years)
    if round_one.empty:
        return pd.DataFrame()

    metrics = (
        round_one.groupby(["YEAR", "COLLEGE_CODE"])
        .agg(
            admitted_students=("RANK", "size"),
            median_rank=("RANK", "median"),
            q25_rank=("RANK", lambda s: s.quantile(0.25)),
            q75_rank=("RANK", lambda s: s.quantile(0.75)),
            median_mark=("AGGREGATE_MARK", "median"),
            q75_mark=("AGGREGATE_MARK", lambda s: s.quantile(0.75)),
        )
        .reset_index()
    )
    metrics["college_code"] = metrics["COLLEGE_CODE"].astype(str)
    return metrics


def _filter_round_and_years(allotment: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    df = allotment.copy()
    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")
    df["ROUND"] = pd.to_numeric(df["ROUND"], errors="coerce")
    df["RANK"] = pd.to_numeric(df["RANK"], errors="coerce")
    df["AGGREGATE_MARK"] = pd.to_numeric(df["AGGREGATE_MARK"], errors="coerce")

    filtered = df[
        (df["ROUND"] == RANKING_ROUND)
        & (df["YEAR"].isin(years))
        & df["COLLEGE_CODE"].notna()
        & df["RANK"].notna()
    ].copy()
    filtered["COLLEGE_CODE"] = filtered["COLLEGE_CODE"].astype(str)
    return filtered


def _weighted_recent_average(
    scored_df: pd.DataFrame,
    score_column: str,
    output_column: str,
) -> pd.DataFrame:
    records = []
    for college_code, group in scored_df.groupby("college_code"):
        weighted_values: list[float] = []
        weights: list[float] = []

        for _, row in group.iterrows():
            year = int(row["YEAR"])
            weight = float(RECENCY_WEIGHTS.get(year, 0.0))
            value = row.get(score_column)
            if weight <= 0 or pd.isna(value):
                continue
            weighted_values.append(float(value))
            weights.append(weight)

        if not weights:
            continue

        total_weight = sum(weights)
        score = sum(v * w for v, w in zip(weighted_values, weights)) / total_weight
        score = _shrink_scalar_to_neutral(
            score,
            strength=float(total_weight),
            full_strength_at=1.0,
        )
        records.append({"college_code": str(college_code), output_column: score})

    return pd.DataFrame(records)


def _shrink_to_neutral(
    score: pd.Series,
    strength: pd.Series,
    full_strength_at: float,
    neutral: float = 50.0,
) -> pd.Series:
    reliability = _reliability(strength, full_strength_at)
    return neutral + (pd.to_numeric(score, errors="coerce").fillna(neutral) - neutral) * reliability


def _shrink_scalar_to_neutral(
    score: float,
    strength: float,
    full_strength_at: float,
    neutral: float = 50.0,
) -> float:
    reliability = float(_reliability(pd.Series([strength]), full_strength_at).iloc[0])
    return neutral + (float(score) - neutral) * reliability


def _reliability(strength: pd.Series, full_strength_at: float) -> pd.Series:
    strength = pd.to_numeric(strength, errors="coerce").fillna(0.0).clip(lower=0.0)
    if full_strength_at <= 0:
        return pd.Series(1.0, index=strength.index, dtype=float)
    return np.sqrt((strength / float(full_strength_at)).clip(upper=1.0))
