"""Generate 2026 prediction CSV and SQL files from trained ML models."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd

from build_training_data import CATEGORICAL_FEATURES, FEATURE_COLUMNS, build_prediction_frame

ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = ROOT / "models"
REPORT_DIR = ROOT / "reports"
PREDICTION_DIR = ROOT / "predictions"

CLOSING_MODEL_PATH = MODEL_DIR / "closing_rank_model_v1.txt"
CLOSING_PREPROCESSOR_PATH = MODEL_DIR / "preprocessors.joblib"
CLOSING_METRICS_PATH = REPORT_DIR / "cv_metrics.json"
RANK_PREPROCESSOR_PATH = MODEL_DIR / "rank_preprocessors.joblib"

TARGET_YEAR = 2026
ROUND_NUMBER = 1
COMMUNITIES = ["OC", "BC", "BCM", "MBC", "SC", "ST"]


def _sql_string(value: object) -> str:
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def _sql_int(value: object) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "NULL"
    return str(int(value))


def _confidence(predicted: int, lower: int, upper: int) -> str:
    if predicted <= 0:
        return "Low"
    ratio = (upper - lower) / predicted
    if ratio <= 0.20:
        return "High"
    if ratio <= 0.50:
        return "Medium"
    return "Low"


def _apply_categories(frame: pd.DataFrame, categories: dict[str, list[str]]) -> pd.DataFrame:
    frame = frame.copy()
    for column in CATEGORICAL_FEATURES:
        values = frame[column].astype(str)
        known = set(categories[column])
        frame[column] = pd.Categorical(values.where(values.isin(known)), categories=categories[column])
    return frame


def generate_closing_predictions() -> list[dict[str, object]]:
    preprocessor = joblib.load(CLOSING_PREPROCESSOR_PATH)
    model = lgb.Booster(model_file=str(CLOSING_MODEL_PATH))
    metrics = json.loads(CLOSING_METRICS_PATH.read_text(encoding="utf-8"))
    residual_std = float(metrics["summary"]["residual_std_raw"])

    frame = build_prediction_frame(target_year=TARGET_YEAR, round_number=ROUND_NUMBER)
    frame = _apply_categories(frame, preprocessor["categories"])
    raw = np.expm1(model.predict(frame[FEATURE_COLUMNS]))
    blend = preprocessor.get("prediction_blend", {})
    if blend.get("feature") in frame.columns:
        weight = float(blend.get("weight", 0))
        prior = frame[blend["feature"]].to_numpy()
        prior = np.where(np.isnan(prior), raw, prior)
        raw = ((1 - weight) * raw) + (weight * prior)
    rows: list[dict[str, object]] = []
    for source, predicted in zip(frame.itertuples(index=False), raw):
        predicted_rank = max(1, int(round(float(predicted))))
        lower = max(1, int(round(predicted_rank - residual_std)))
        upper = max(lower, int(round(predicted_rank + residual_std)))
        rows.append(
            {
                "season_year": TARGET_YEAR,
                "round_number": ROUND_NUMBER,
                "community_quota": source.community,
                "college_code": source.college_code,
                "branch_code": source.branch_code,
                "predicted_closing_rank": predicted_rank,
                "prediction_lower": lower,
                "prediction_upper": upper,
                "confidence_label": _confidence(predicted_rank, lower, upper),
                "model_version": preprocessor["model_version"],
            }
        )
    return rows


def _hist_feature(preprocessor: dict[str, object], community: str, mark: int) -> dict[str, float]:
    hist = preprocessor["historical_mark_features"]
    direct = hist.get(f"{community}|{mark}")
    if direct:
        return direct
    candidates = [
        (abs(int(key.split("|", 1)[1]) - mark), value)
        for key, value in hist.items()
        if key.startswith(f"{community}|")
    ]
    if not candidates:
        return {"mark_percentile_hist": 50.0, "mark_rank_fraction_hist": 0.5}
    return min(candidates, key=lambda item: item[0])[1]


def generate_rank_predictions() -> list[dict[str, object]]:
    preprocessor = joblib.load(RANK_PREPROCESSOR_PATH)
    rows: list[dict[str, object]] = []
    model_cache: dict[str, lgb.Booster] = {}
    for community in COMMUNITIES:
        model_name = preprocessor["community_model"][community]
        if model_name not in model_cache:
            model_cache[model_name] = lgb.Booster(model_file=str(MODEL_DIR / f"rank_model_{model_name}.txt"))
        model = model_cache[model_name]
        total_students = int(preprocessor["predicted_community_totals_2026"][community])
        residual_std = float(preprocessor["residual_std_fraction_by_model"][model_name])
        for mark in range(0, 201):
            hist = _hist_feature(preprocessor, community, mark)
            features = pd.DataFrame(
                [
                    {
                        "aggregate_mark": float(mark),
                        "mark_bucket": mark,
                        "year": TARGET_YEAR,
                        "total_students": total_students,
                        "mark_percentile_hist": hist["mark_percentile_hist"],
                        "mark_rank_fraction_hist": hist["mark_rank_fraction_hist"],
                        "community": community,
                    }
                ]
            )
            features["community"] = pd.Categorical(features["community"], categories=preprocessor["categories"]["community"])
            raw_prediction = float(model.predict(features[preprocessor["feature_columns"]])[0])
            predicted_fraction = float(1 / (1 + math.exp(-raw_prediction)))
            predicted_rank = max(1, int(round(predicted_fraction * total_students)))
            margin = max(25, int(round(residual_std * total_students)))
            lower = max(1, predicted_rank - margin)
            upper = max(lower, min(total_students, predicted_rank + margin))
            rows.append(
                {
                    "aggregate_mark": f"{mark:.4f}",
                    "community_quota": community,
                    "predicted_rank_min": lower,
                    "predicted_rank_max": upper,
                    "predicted_total_students": total_students,
                    "confidence_label": _confidence(predicted_rank, lower, upper),
                    "model_version": preprocessor["model_version"],
                }
            )
    return rows


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_closing_sql(path: Path, rows: list[dict[str, object]]) -> None:
    lines = [
        "INSERT INTO predicted_closing_ranks (season_year, round_number, community_quota, college_code, branch_code, predicted_closing_rank, prediction_lower, prediction_upper, confidence_label, model_version) VALUES"
    ]
    values = []
    for row in rows:
        values.append(
            "("
            + ", ".join(
                [
                    _sql_int(row["season_year"]),
                    _sql_int(row["round_number"]),
                    _sql_string(row["community_quota"]),
                    _sql_string(row["college_code"]),
                    _sql_string(row["branch_code"]),
                    _sql_int(row["predicted_closing_rank"]),
                    _sql_int(row["prediction_lower"]),
                    _sql_int(row["prediction_upper"]),
                    _sql_string(row["confidence_label"]),
                    _sql_string(row["model_version"]),
                ]
            )
            + ")"
        )
    lines.append(",\n".join(values))
    lines.append(
        "ON CONFLICT (season_year, round_number, community_quota, college_code, branch_code) DO UPDATE SET "
        "predicted_closing_rank = EXCLUDED.predicted_closing_rank, prediction_lower = EXCLUDED.prediction_lower, "
        "prediction_upper = EXCLUDED.prediction_upper, confidence_label = EXCLUDED.confidence_label, "
        "model_version = EXCLUDED.model_version, predicted_at = now();"
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_rank_sql(path: Path, rows: list[dict[str, object]]) -> None:
    lines = [
        "INSERT INTO predicted_rank_bands (aggregate_mark, community_quota, predicted_rank_min, predicted_rank_max, predicted_total_students, confidence_label, model_version) VALUES"
    ]
    values = []
    for row in rows:
        values.append(
            "("
            + ", ".join(
                [
                    row["aggregate_mark"],
                    _sql_string(row["community_quota"]),
                    _sql_int(row["predicted_rank_min"]),
                    _sql_int(row["predicted_rank_max"]),
                    _sql_int(row["predicted_total_students"]),
                    _sql_string(row["confidence_label"]),
                    _sql_string(row["model_version"]),
                ]
            )
            + ")"
        )
    lines.append(",\n".join(values))
    lines.append(
        "ON CONFLICT (aggregate_mark, community_quota) DO UPDATE SET "
        "predicted_rank_min = EXCLUDED.predicted_rank_min, predicted_rank_max = EXCLUDED.predicted_rank_max, "
        "predicted_total_students = EXCLUDED.predicted_total_students, confidence_label = EXCLUDED.confidence_label, "
        "model_version = EXCLUDED.model_version, predicted_at = now();"
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    PREDICTION_DIR.mkdir(parents=True, exist_ok=True)
    closing_rows = generate_closing_predictions()
    rank_rows = generate_rank_predictions()
    write_csv(PREDICTION_DIR / "closing_ranks_2026.csv", closing_rows)
    write_closing_sql(PREDICTION_DIR / "closing_ranks_2026.sql", closing_rows)
    write_csv(PREDICTION_DIR / "rank_bands_2026.csv", rank_rows)
    write_rank_sql(PREDICTION_DIR / "rank_bands_2026.sql", rank_rows)
    print(f"Wrote {len(closing_rows):,} closing-rank predictions")
    print(f"Wrote {len(rank_rows):,} rank-band predictions")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
