"""Train LightGBM rank-fraction models from the general rank list."""

from __future__ import annotations

import json
import math
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

ROOT = Path(__file__).resolve().parents[1]
GRL_PATH = ROOT / "data/raw/general_rank_list_2020_2025.csv"
MODEL_DIR = ROOT / "models"
METRICS_PATH = ROOT / "reports/rank_model_metrics.json"
PREPROCESSOR_PATH = MODEL_DIR / "rank_preprocessors.joblib"

COMMUNITIES = ["OC", "BC", "BCM", "MBC", "SC", "ST"]
COMMUNITY_ALIASES = {"SCA": "SC"}
MODEL_SPECS = {
    "OC": ["OC"],
    "BC": ["BC"],
    "BCM": ["BCM"],
    "MBC": ["MBC"],
    "SC": ["SC"],
    "ST": ["ST"],
}
COMMUNITY_MODEL = {
    "OC": "OC",
    "BC": "BC",
    "BCM": "BCM",
    "MBC": "MBC",
    "SC": "SC",
    "ST": "ST",
}
FEATURE_COLUMNS = [
    "aggregate_mark",
    "mark_bucket",
    "year",
    "total_students",
    "mark_percentile_hist",
    "mark_rank_fraction_hist",
    "community",
]
CATEGORICAL_FEATURES = ["community"]
MODEL_VERSION = "rank_fraction_lgbm_v1"
FOLDS = [
    ([2020, 2021], 2022),
    ([2020, 2021, 2022], 2023),
    ([2020, 2021, 2022, 2023], 2024),
    ([2020, 2021, 2022, 2023, 2024], 2025),
]
PARAMS = {
    "objective": "regression",
    "metric": "rmse",
    "num_leaves": 31,
    "learning_rate": 0.04,
    "feature_fraction": 0.9,
    "bagging_fraction": 0.9,
    "bagging_freq": 5,
    "min_child_samples": 5,
    "verbosity": -1,
    "seed": 43,
}


def _normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame.columns = [column.strip().replace("\ufeff", "") for column in frame.columns]
    return frame


def load_rank_buckets() -> pd.DataFrame:
    frame = _normalize_columns(pd.read_csv(GRL_PATH, encoding="utf-8-sig"))
    frame = frame.rename(
        columns={
            "YEAR": "year",
            "GENERAL RANK": "general_rank",
            "AGGREGATE MARK": "aggregate_mark",
            "COMMUNITY": "community",
            "COMMUNITY RANK": "community_rank",
        }
    )
    frame["year"] = pd.to_numeric(frame["year"], errors="coerce").astype("Int64")
    frame["aggregate_mark"] = pd.to_numeric(frame["aggregate_mark"], errors="coerce")
    frame["general_rank"] = pd.to_numeric(frame["general_rank"], errors="coerce")
    frame["community_rank"] = pd.to_numeric(frame["community_rank"], errors="coerce")
    frame["community"] = frame["community"].astype(str).str.upper().str.strip().replace(COMMUNITY_ALIASES)
    frame = frame.dropna(subset=["year", "aggregate_mark", "community_rank"])
    frame = frame[frame["community"].isin(COMMUNITIES)]
    frame["year"] = frame["year"].astype(int)
    frame["mark_bucket"] = np.floor(frame["aggregate_mark"]).clip(0, 200).astype(int)

    community_totals = frame.groupby(["year", "community"], as_index=False).size().rename(columns={"size": "community_total_students"})
    year_totals = frame.groupby("year", as_index=False).size().rename(columns={"size": "year_total_students"})
    frame = frame.merge(community_totals, on=["year", "community"], how="left")
    frame = frame.merge(year_totals, on="year", how="left")
    frame = frame.sort_values(["year", "community", "general_rank"]).reset_index(drop=True)
    frame["merged_community_rank"] = frame.groupby(["year", "community"]).cumcount() + 1
    frame["rank_basis"] = np.where(frame["community"] == "OC", frame["general_rank"], frame["merged_community_rank"])
    frame["total_students"] = np.where(frame["community"] == "OC", frame["year_total_students"], frame["community_total_students"])
    frame["rank_fraction"] = (frame["rank_basis"].astype(float) / frame["total_students"].astype(float)).clip(1e-6, 1 - 1e-6)

    buckets = (
        frame.groupby(["year", "community", "mark_bucket"], as_index=False)
        .agg(
            aggregate_mark=("mark_bucket", "first"),
            total_students=("total_students", "first"),
            bucket_size=("rank_fraction", "size"),
            rank_fraction=("rank_fraction", "mean"),
        )
        .sort_values(["community", "mark_bucket", "year"])
        .reset_index(drop=True)
    )
    buckets["mark_percentile"] = buckets["rank_fraction"] * 100
    group = buckets.groupby(["community", "mark_bucket"], sort=False)
    buckets["mark_percentile_hist"] = group["mark_percentile"].transform(lambda values: values.shift(1).expanding().mean())
    buckets["mark_rank_fraction_hist"] = group["rank_fraction"].transform(lambda values: values.shift(1).expanding().mean())
    buckets["rank_fraction_logit"] = np.log(buckets["rank_fraction"] / (1 - buckets["rank_fraction"]))
    return buckets


def _dataset(frame: pd.DataFrame) -> lgb.Dataset:
    return lgb.Dataset(
        frame[FEATURE_COLUMNS],
        label=frame["rank_fraction_logit"],
        weight=frame["bucket_size"],
        categorical_feature=CATEGORICAL_FEATURES,
        free_raw_data=False,
    )


def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.copy()
    frame["community"] = frame["community"].astype(str).astype("category")
    return frame


def _sigmoid(values: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-values))


def _metrics(actual_fraction: np.ndarray, predicted_fraction: np.ndarray, total_students: np.ndarray) -> dict[str, float]:
    predicted_fraction = np.clip(predicted_fraction, 0, 1)
    actual_rank = actual_fraction * total_students
    predicted_rank = predicted_fraction * total_students
    rank_mask = actual_rank > 1000
    mape = float(np.mean(np.abs((predicted_rank[rank_mask] - actual_rank[rank_mask]) / actual_rank[rank_mask])) * 100) if rank_mask.any() else 0.0
    within_10 = float(np.mean(np.abs(predicted_rank - actual_rank) <= (actual_rank * 0.10)) * 100)
    return {
        "rmse_rank_fraction": round(math.sqrt(mean_squared_error(actual_fraction, predicted_fraction)), 6),
        "mape_raw_rank_gt_1000_pct": round(mape, 2),
        "within_10pct_rank_accuracy_pct": round(within_10, 2),
        "residual_std_fraction": round(float(np.std(predicted_fraction - actual_fraction)), 6),
        "predicted_fraction_min": round(float(predicted_fraction.min()), 6),
        "predicted_fraction_max": round(float(predicted_fraction.max()), 6),
    }


def train_one_model(name: str, communities: list[str], frame: pd.DataFrame) -> dict[str, object]:
    subset = _prepare(frame[frame["community"].isin(communities)])
    fold_metrics = []
    best_iterations = []
    for train_years, valid_year in FOLDS:
        train = subset[subset["year"].isin(train_years)]
        valid = subset[subset["year"] == valid_year]
        if train.empty or valid.empty:
            continue
        model = lgb.train(
            PARAMS,
            _dataset(train),
            num_boost_round=800,
            valid_sets=[_dataset(valid)],
            valid_names=["valid"],
            callbacks=[lgb.early_stopping(50, verbose=False)],
        )
        predicted = _sigmoid(model.predict(valid[FEATURE_COLUMNS], num_iteration=model.best_iteration))
        metrics = _metrics(
            valid["rank_fraction"].to_numpy(),
            predicted,
            valid["total_students"].to_numpy(),
        )
        fold_metrics.append(
            {
                "train_years": train_years,
                "valid_year": valid_year,
                "rows_train": int(len(train)),
                "rows_valid": int(len(valid)),
                "best_iteration": int(model.best_iteration or 800),
                **metrics,
            }
        )
        best_iterations.append(int(model.best_iteration or 800))

    num_boost_round = max(50, int(np.mean(best_iterations))) if best_iterations else 200
    final_model = lgb.train(PARAMS, _dataset(subset), num_boost_round=num_boost_round)
    model_path = MODEL_DIR / f"rank_model_{name}.txt"
    final_model.save_model(str(model_path))

    residual_std = float(np.mean([metric["residual_std_fraction"] for metric in fold_metrics])) if fold_metrics else 0.05
    return {
        "model_name": name,
        "communities": communities,
        "model_path": str(model_path.relative_to(ROOT)),
        "rows": int(len(subset)),
        "final_num_boost_round": num_boost_round,
        "folds": fold_metrics,
        "summary": {
            "mean_rmse_rank_fraction": round(float(np.mean([metric["rmse_rank_fraction"] for metric in fold_metrics])), 6) if fold_metrics else None,
            "mean_mape_raw_rank_gt_1000_pct": round(float(np.mean([metric["mape_raw_rank_gt_1000_pct"] for metric in fold_metrics])), 2) if fold_metrics else None,
            "mean_within_10pct_rank_accuracy_pct": round(float(np.mean([metric["within_10pct_rank_accuracy_pct"] for metric in fold_metrics])), 2) if fold_metrics else None,
            "residual_std_fraction": round(residual_std, 6),
            "predictions_are_not_collapsed_to_1": all(
                not (metric["predicted_fraction_min"] > 0.99 and metric["predicted_fraction_max"] >= 0.999)
                for metric in fold_metrics
            ),
        },
    }


def build_preprocessor(frame: pd.DataFrame, model_metrics: dict[str, object]) -> dict[str, object]:
    latest_year = int(frame["year"].max())
    latest_totals = (
        frame[frame["year"] == latest_year]
        .groupby("community")["total_students"]
        .max()
        .astype(int)
        .to_dict()
    )
    predicted_totals: dict[str, int] = {}
    for community in COMMUNITIES:
        history = frame[frame["community"] == community].drop_duplicates(["year", "community"])[["year", "total_students"]]
        if len(history) >= 2:
            slope, intercept = np.polyfit(history["year"].to_numpy(), history["total_students"].to_numpy(), deg=1)
            predicted_totals[community] = max(1, int(round(slope * 2026 + intercept)))
        else:
            predicted_totals[community] = int(latest_totals.get(community, 1))

    hist = (
        frame.groupby(["community", "mark_bucket"], as_index=False)
        .agg(
            mark_percentile_hist=("mark_percentile", "mean"),
            mark_rank_fraction_hist=("rank_fraction", "mean"),
        )
    )
    hist_map = {
        f"{row.community}|{int(row.mark_bucket)}": {
            "mark_percentile_hist": float(row.mark_percentile_hist),
            "mark_rank_fraction_hist": float(row.mark_rank_fraction_hist),
        }
        for row in hist.itertuples(index=False)
    }
    residual_by_model = {
        name: float(metrics["summary"]["residual_std_fraction"] or 0.05)
        for name, metrics in model_metrics.items()
    }
    return {
        "model_version": MODEL_VERSION,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_features": CATEGORICAL_FEATURES,
        "categories": {"community": COMMUNITIES},
        "community_model": COMMUNITY_MODEL,
        "latest_training_year": latest_year,
        "latest_community_totals": latest_totals,
        "predicted_community_totals_2026": predicted_totals,
        "historical_mark_features": hist_map,
        "residual_std_fraction_by_model": residual_by_model,
    }


def main() -> int:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)
    frame = load_rank_buckets()
    metrics = {
        name: train_one_model(name, communities, frame)
        for name, communities in MODEL_SPECS.items()
    }
    preprocessor = build_preprocessor(frame, metrics)
    joblib.dump(preprocessor, PREPROCESSOR_PATH)
    report = {
        "model_version": MODEL_VERSION,
        "params": PARAMS,
            "target": "logit(rank_fraction), with OC using general rank / total-year students and quota communities using community rank / community total students",
        "feature_columns": FEATURE_COLUMNS,
        "categorical_features": CATEGORICAL_FEATURES,
        "model_specs": MODEL_SPECS,
        "community_model": COMMUNITY_MODEL,
        "models": metrics,
    }
    METRICS_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {METRICS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
