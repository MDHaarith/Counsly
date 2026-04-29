"""Build LightGBM training features for closing-rank prediction."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent

CUTOFF_PATH = ROOT / "data/raw/cutoffs_2020_2025_training_ready.csv"
GRL_PATH = ROOT / "data/raw/general_rank_list_2020_2025.csv"
SEAT_MATRIX_PATH = REPO_ROOT / "supabase_db/seed_data/community_seats/seat_matrix_2025_round_1.json"
OUTPUT_PATH = ROOT / "data/training_data_closing_ranks.csv"

COMMUNITIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]
CATEGORICAL_FEATURES = ["community", "college_code", "branch_code"]
FEATURE_COLUMNS = [
    "year",
    "round_number",
    "community",
    "college_code",
    "branch_code",
    "closing_rank_lag_1",
    "closing_rank_lag_2",
    "closing_rank_delta_1",
    "closing_rank_ema_3",
    "seats_community",
    "seats_total",
    "seats_ratio",
    "total_applicants",
    "community_applicants",
    "applicant_ratio",
    "community_applicants_lag_1",
    "total_applicants_lag_1",
    "lag_1_applicant_scaled",
    "lag_1_community_scaled",
    "combo_avg_closing",
    "college_avg_closing",
    "branch_avg_closing",
    "combo_years_of_data",
    "seats_per_applicant",
    "competition_score",
]


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [column.strip().replace("\ufeff", "") for column in df.columns]
    return df


def _safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator.astype(float) / denominator.replace({0: np.nan}).astype(float)


def load_closing_targets() -> pd.DataFrame:
    cutoffs = _normalize_columns(
        pd.read_csv(
            CUTOFF_PATH,
            encoding="utf-8-sig",
            usecols=["YEAR", "ROUND", "COMMUNITY", "COLLEGE CODE", "BRANCH CODE", "RANK"],
        )
    )
    cutoffs = cutoffs.rename(
        columns={
            "YEAR": "year",
            "ROUND": "round_number",
            "COMMUNITY": "community",
            "COLLEGE CODE": "college_code",
            "BRANCH CODE": "branch_code",
            "RANK": "rank",
        }
    )
    cutoffs["year"] = pd.to_numeric(cutoffs["year"], errors="coerce").astype("Int64")
    cutoffs["round_number"] = pd.to_numeric(cutoffs["round_number"], errors="coerce").astype("Int64")
    cutoffs["rank"] = pd.to_numeric(cutoffs["rank"], errors="coerce")
    cutoffs["community"] = cutoffs["community"].astype(str).str.upper().str.strip()
    cutoffs["college_code"] = cutoffs["college_code"].astype(str).str.strip()
    cutoffs["branch_code"] = cutoffs["branch_code"].astype(str).str.upper().str.strip()
    cutoffs = cutoffs.dropna(subset=["year", "round_number", "rank"])
    cutoffs = cutoffs[cutoffs["community"].isin(COMMUNITIES)]

    closing = (
        cutoffs.groupby(["year", "round_number", "community", "college_code", "branch_code"], as_index=False)
        .agg(closing_rank=("rank", "max"))
        .sort_values(["community", "college_code", "branch_code", "round_number", "year"])
        .reset_index(drop=True)
    )
    closing["year"] = closing["year"].astype(int)
    closing["round_number"] = closing["round_number"].astype(int)
    closing["closing_rank"] = closing["closing_rank"].round().astype(int)
    return closing


def load_seat_features() -> tuple[pd.DataFrame, dict[str, float]]:
    rows = json.loads(SEAT_MATRIX_PATH.read_text(encoding="utf-8"))
    seat_matrix = pd.DataFrame(rows)
    seat_matrix.columns = [str(column).lower() for column in seat_matrix.columns]
    seat_matrix["college_code"] = seat_matrix["college_code"].astype(str).str.strip()
    seat_matrix["branch_code"] = seat_matrix["branch_code"].astype(str).str.upper().str.strip()
    seat_matrix["total"] = pd.to_numeric(seat_matrix["total"], errors="coerce").fillna(0)

    long_rows: list[dict[str, object]] = []
    for _, row in seat_matrix.iterrows():
        seats_total = float(row["total"])
        for community in COMMUNITIES:
            seats_community = float(pd.to_numeric(row.get(community.lower(), 0), errors="coerce") or 0)
            long_rows.append(
                {
                    "college_code": row["college_code"],
                    "branch_code": row["branch_code"],
                    "community": community,
                    "seats_community": seats_community,
                    "seats_total": seats_total,
                    "seats_ratio": seats_community / seats_total if seats_total else np.nan,
                }
            )

    seat_features = pd.DataFrame(long_rows)
    seat_totals = seat_features.groupby("community")["seats_community"].sum().to_dict()
    seat_totals["_all"] = float(seat_matrix["total"].sum())
    return seat_features, seat_totals


def load_cohort_features() -> pd.DataFrame:
    grl = _normalize_columns(pd.read_csv(GRL_PATH, encoding="utf-8-sig", usecols=["YEAR", "COMMUNITY"]))
    grl = grl.rename(columns={"YEAR": "year", "COMMUNITY": "community"})
    grl["year"] = pd.to_numeric(grl["year"], errors="coerce").astype("Int64")
    grl["community"] = grl["community"].astype(str).str.upper().str.strip()
    grl = grl.dropna(subset=["year"])
    grl = grl[grl["community"].isin(COMMUNITIES)]
    community_counts = (
        grl.groupby(["year", "community"], as_index=False)
        .size()
        .rename(columns={"size": "community_applicants"})
    )
    total_counts = grl.groupby("year", as_index=False).size().rename(columns={"size": "total_applicants"})
    cohorts = community_counts.merge(total_counts, on="year", how="left")
    cohorts["applicant_ratio"] = _safe_divide(cohorts["community_applicants"], cohorts["total_applicants"])
    cohorts["year"] = cohorts["year"].astype(int)
    return cohorts


def _add_time_features(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.sort_values(["community", "college_code", "branch_code", "round_number", "year"]).reset_index(drop=True)
    combo_round = frame.groupby(["community", "college_code", "branch_code", "round_number"], sort=False)
    frame["closing_rank_lag_1"] = combo_round["closing_rank"].shift(1)
    frame["closing_rank_lag_2"] = combo_round["closing_rank"].shift(2)
    frame["closing_rank_delta_1"] = frame["closing_rank_lag_1"] - frame["closing_rank_lag_2"]
    frame["closing_rank_ema_3"] = combo_round["closing_rank"].transform(
        lambda values: values.shift(1).ewm(span=3, adjust=False).mean()
    )
    combo = frame.groupby(["community", "college_code", "branch_code"], sort=False)
    frame["combo_years_of_data"] = combo["closing_rank"].transform("count")
    frame["combo_avg_closing"] = frame.groupby(
        ["community", "college_code", "branch_code", "round_number"], sort=False
    )["closing_rank"].transform("mean")
    frame["college_avg_closing"] = frame.groupby("college_code", sort=False)["closing_rank"].transform("mean")
    frame["branch_avg_closing"] = frame.groupby("branch_code", sort=False)["closing_rank"].transform("mean")
    return frame


def _add_external_features(frame: pd.DataFrame) -> pd.DataFrame:
    seat_features, seat_totals = load_seat_features()
    cohorts = load_cohort_features()
    latest_cohort_year = int(cohorts["year"].max())
    latest_cohorts = cohorts[cohorts["year"] == latest_cohort_year].drop(columns=["year"])

    frame = frame.merge(seat_features, on=["community", "college_code", "branch_code"], how="left")
    frame = frame.merge(cohorts, on=["year", "community"], how="left")
    missing_cohorts = frame["community_applicants"].isna()
    if missing_cohorts.any():
        fallback = frame.loc[missing_cohorts, ["community"]].merge(latest_cohorts, on="community", how="left")
        for column in ["community_applicants", "total_applicants", "applicant_ratio"]:
            frame.loc[missing_cohorts, column] = fallback[column].to_numpy()

    frame["seats_community"] = frame["seats_community"].fillna(0)
    frame["seats_total"] = frame["seats_total"].fillna(0)
    frame["seats_ratio"] = _safe_divide(frame["seats_community"], frame["seats_total"])
    frame["seats_per_applicant"] = _safe_divide(frame["seats_community"], frame["community_applicants"])
    frame["competition_score"] = (
        frame["community_applicants"].astype(float) / seat_totals["_all"] if seat_totals["_all"] else np.nan
    )
    frame = frame.sort_values(["community", "college_code", "branch_code", "round_number", "year"]).reset_index(drop=True)
    combo_round = frame.groupby(["community", "college_code", "branch_code", "round_number"], sort=False)
    frame["community_applicants_lag_1"] = combo_round["community_applicants"].shift(1)
    frame["total_applicants_lag_1"] = combo_round["total_applicants"].shift(1)
    frame["lag_1_applicant_scaled"] = frame["closing_rank_lag_1"] * _safe_divide(frame["total_applicants"], frame["total_applicants_lag_1"])
    frame["lag_1_community_scaled"] = frame["closing_rank_lag_1"] * _safe_divide(
        frame["community_applicants"], frame["community_applicants_lag_1"]
    )
    return frame


def build_training_frame() -> pd.DataFrame:
    frame = _add_time_features(load_closing_targets())
    frame = _add_external_features(frame)
    return frame[["year", "round_number", "community", "college_code", "branch_code", "closing_rank", *FEATURE_COLUMNS[5:]]]


def build_prediction_frame(target_year: int = 2026, round_number: int = 1) -> pd.DataFrame:
    historical = load_closing_targets()
    seat_features, _ = load_seat_features()
    seat_combos = seat_features[["community", "college_code", "branch_code"]].drop_duplicates()
    historical_combos = historical[["community", "college_code", "branch_code"]].drop_duplicates()
    combos = pd.concat([seat_combos, historical_combos], ignore_index=True).drop_duplicates()
    target = combos.assign(year=target_year, round_number=round_number, closing_rank=np.nan)

    combined = pd.concat([historical, target], ignore_index=True, sort=False)
    combined = _add_time_features(combined)
    combined = _add_external_features(combined)
    prediction = combined[(combined["year"] == target_year) & (combined["round_number"] == round_number)].copy()
    return prediction[["year", "round_number", "community", "college_code", "branch_code", *FEATURE_COLUMNS[5:]]]


def main() -> int:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    frame = build_training_frame().sort_values(["year", "round_number", "community", "college_code", "branch_code"])
    frame.to_csv(OUTPUT_PATH, index=False)
    print(f"Wrote {OUTPUT_PATH} ({len(frame):,} rows, {len(frame.columns)} columns)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
