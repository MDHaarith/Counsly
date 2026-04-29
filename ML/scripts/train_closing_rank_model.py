"""Train the LightGBM closing-rank model with year-based CV."""

from __future__ import annotations

import json
import math
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error

from build_training_data import CATEGORICAL_FEATURES, FEATURE_COLUMNS

ROOT = Path(__file__).resolve().parents[1]
TRAINING_PATH = ROOT / "data/training_data_closing_ranks.csv"
MODEL_PATH = ROOT / "models/closing_rank_model_v1.txt"
PREPROCESSOR_PATH = ROOT / "models/preprocessors.joblib"
METRICS_PATH = ROOT / "reports/cv_metrics.json"
IMPORTANCE_PATH = ROOT / "reports/feature_importance.csv"

MODEL_VERSION = "closing_rank_lgbm_v1"
TARGET_COLUMN = "closing_rank"
COMBO_AVG_BLEND_WEIGHT = 0.5
FOLDS = [
    ([2020, 2021], 2022),
    ([2020, 2021, 2022], 2023),
    ([2020, 2021, 2022, 2023], 2024),
    ([2020, 2021, 2022, 2023, 2024], 2025),
]
PARAMS = {
    "objective": "regression",
    "metric": "rmse",
    "num_leaves": 63,
    "learning_rate": 0.05,
    "feature_fraction": 0.8,
    "bagging_fraction": 0.8,
    "bagging_freq": 5,
    "min_child_samples": 20,
    "verbosity": -1,
    "seed": 42,
}


def load_training_data() -> pd.DataFrame:
    if not TRAINING_PATH.exists():
        raise FileNotFoundError(f"Run build_training_data.py first: {TRAINING_PATH}")
    frame = pd.read_csv(TRAINING_PATH)
    for column in CATEGORICAL_FEATURES:
        frame[column] = frame[column].astype(str).astype("category")
    return frame


def _metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    actual_log = np.log1p(actual)
    predicted_log = np.log1p(np.clip(predicted, 0, None))
    rank_mask = actual > 1000
    mape = float(np.mean(np.abs((predicted[rank_mask] - actual[rank_mask]) / actual[rank_mask])) * 100) if rank_mask.any() else 0.0
    within_10 = float(np.mean(np.abs(predicted - actual) <= (actual * 0.10)) * 100)
    return {
        "rmse_log": round(math.sqrt(mean_squared_error(actual_log, predicted_log)), 4),
        "mape_raw_rank_gt_1000_pct": round(mape, 2),
        "within_10pct_accuracy_pct": round(within_10, 2),
        "residual_std_raw": round(float(np.std(predicted - actual)), 2),
    }


def _dataset(frame: pd.DataFrame) -> lgb.Dataset:
    return lgb.Dataset(
        frame[FEATURE_COLUMNS],
        label=np.log1p(frame[TARGET_COLUMN].to_numpy()),
        categorical_feature=CATEGORICAL_FEATURES,
        free_raw_data=False,
    )


def train_fold(frame: pd.DataFrame, train_years: list[int], valid_year: int) -> tuple[dict[str, object], int]:
    train = frame[frame["year"].isin(train_years)]
    valid = frame[frame["year"] == valid_year]
    model = lgb.train(
        PARAMS,
        _dataset(train),
        num_boost_round=1200,
        valid_sets=[_dataset(valid)],
        valid_names=["valid"],
        callbacks=[lgb.early_stopping(60, verbose=False)],
    )
    predicted = np.expm1(model.predict(valid[FEATURE_COLUMNS], num_iteration=model.best_iteration))
    combo_prior = valid["combo_avg_closing"].to_numpy()
    combo_prior = np.where(np.isnan(combo_prior), predicted, combo_prior)
    predicted = ((1 - COMBO_AVG_BLEND_WEIGHT) * predicted) + (COMBO_AVG_BLEND_WEIGHT * combo_prior)
    metrics = _metrics(valid[TARGET_COLUMN].to_numpy(), predicted)
    return {
        "train_years": train_years,
        "valid_year": valid_year,
        "rows_train": int(len(train)),
        "rows_valid": int(len(valid)),
        "best_iteration": int(model.best_iteration or 1200),
        **metrics,
    }, int(model.best_iteration or 1200)


def main() -> int:
    (ROOT / "models").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)
    frame = load_training_data()

    fold_metrics = []
    best_iterations = []
    for train_years, valid_year in FOLDS:
        metrics, best_iteration = train_fold(frame, train_years, valid_year)
        fold_metrics.append(metrics)
        best_iterations.append(best_iteration)

    num_boost_round = max(50, int(np.mean(best_iterations)))
    final_model = lgb.train(PARAMS, _dataset(frame), num_boost_round=num_boost_round)
    final_model.save_model(str(MODEL_PATH))

    importance = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "importance_gain": final_model.feature_importance(importance_type="gain"),
            "importance_split": final_model.feature_importance(importance_type="split"),
        }
    ).sort_values("importance_gain", ascending=False)
    importance.to_csv(IMPORTANCE_PATH, index=False)

    preprocessor = {
        "model_version": MODEL_VERSION,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_features": CATEGORICAL_FEATURES,
        "categories": {column: list(frame[column].cat.categories) for column in CATEGORICAL_FEATURES},
        "target_transform": "log1p",
        "target_inverse": "expm1",
        "prediction_blend": {
            "feature": "combo_avg_closing",
            "weight": COMBO_AVG_BLEND_WEIGHT,
        },
        "train_years": sorted(int(year) for year in frame["year"].unique()),
    }
    joblib.dump(preprocessor, PREPROCESSOR_PATH)

    residual_stds = [float(metric["residual_std_raw"]) for metric in fold_metrics]
    summary = {
        "model_version": MODEL_VERSION,
        "params": PARAMS,
        "feature_columns": FEATURE_COLUMNS,
        "categorical_features": CATEGORICAL_FEATURES,
        "folds": fold_metrics,
        "summary": {
            "mean_rmse_log": round(float(np.mean([metric["rmse_log"] for metric in fold_metrics])), 4),
            "mean_mape_raw_rank_gt_1000_pct": round(float(np.mean([metric["mape_raw_rank_gt_1000_pct"] for metric in fold_metrics])), 2),
            "mean_within_10pct_accuracy_pct": round(float(np.mean([metric["within_10pct_accuracy_pct"] for metric in fold_metrics])), 2),
            "residual_std_raw": round(float(np.mean(residual_stds)), 2),
            "final_num_boost_round": num_boost_round,
        },
    }
    METRICS_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MODEL_PATH}")
    print(f"Wrote {METRICS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
