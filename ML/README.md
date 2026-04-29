# Counsly ML Pipeline

This workspace builds production prediction data for Counsly. Raw inputs are
read-only copies from the Supabase seed workspace; generated training data,
models, metrics, and SQL load files stay under `ML/`.

## Architecture

The production pipeline uses LightGBM, not the earlier TinyMLP experiment.

1. **Closing-rank model** predicts `predicted_closing_rank` for each
   `(year, round, community, college, branch)` row. The target is
   `log1p(closing_rank)`, where closing rank is the historical max rank from
   allotment cutoffs. Production output blends the LightGBM prediction with the
   exact-combo historical prior recorded in `combo_avg_closing`.
2. **Rank-band models** predict community rank fraction from whole-mark buckets.
   Separate LightGBM models are trained for OC, BC, BCM, MBC, SC, plus one
   shared sparse-community model for SCA and ST.

Rank modeling uses 1-point mark buckets only. Percentiles are stored as whole
numbers where bucket reports need percentile values.

## Raw Inputs

| File | Purpose |
|---|---|
| `data/raw/cutoffs_2020_2025_training_ready.csv` | Closing-rank targets from allotment output |
| `data/raw/general_rank_list_2020_2025.csv` | Mark-to-community-rank training source |
| `../supabase_db/seed_data/community_seats/seat_matrix_2025_round_1.json` | Seat-count features and 2026 prediction combos |

## Run

Install dependencies:

```bash
python3 -m venv ML/.venv
ML/.venv/bin/pip install -r ML/requirements.txt
```

Build closing-rank training rows:

```bash
python3 ML/scripts/build_training_data.py
```

Train the closing-rank model:

```bash
python3 ML/scripts/train_closing_rank_model.py
```

Train rank-band models:

```bash
python3 ML/scripts/train_rank_model.py
```

Generate 2026 CSV and SQL prediction files:

```bash
python3 ML/scripts/generate_predictions.py
```

Load predictions into Supabase/PostgreSQL:

```bash
DATABASE_URL='postgresql://...' python3 backend/scripts/load_predictions.py
```

## Outputs

| Output | Purpose |
|---|---|
| `data/training_data_closing_ranks.csv` | Feature table for closing-rank training |
| `models/closing_rank_model_v1.txt` | LightGBM closing-rank model |
| `models/preprocessors.joblib` | Closing-rank feature metadata |
| `models/rank_model_*.txt` | LightGBM rank-fraction models |
| `models/rank_preprocessors.joblib` | Rank feature metadata and 2026 cohort estimates |
| `reports/cv_metrics.json` | Closing-rank CV metrics |
| `reports/rank_model_metrics.json` | Rank-model CV metrics |
| `reports/feature_importance.csv` | Closing-rank feature importances |
| `predictions/closing_ranks_2026.csv` | DB-ready predicted closing ranks |
| `predictions/closing_ranks_2026.sql` | Bulk insert SQL for closing ranks |
| `predictions/rank_bands_2026.csv` | DB-ready predicted rank bands |
| `predictions/rank_bands_2026.sql` | Bulk insert SQL for rank bands |

## Evaluation

Closing-rank CV uses year-based folds:

- Train 2020-2021, validate 2022
- Train 2020-2022, validate 2023
- Train 2020-2023, validate 2024
- Train 2020-2024, validate 2025

Metrics are RMSE on log rank, raw-rank MAPE for ranks above 1000, and within
10% band accuracy. `reports/cv_metrics.json` is the launch check source.

Rank-band CV uses the same year split and checks rank-fraction RMSE, raw-rank
MAPE for ranks above 1000, within-10% rank accuracy, and verifies predictions
do not collapse to rank fraction `1.0`.

## Production Flow

`generate_predictions.py` writes rows for:

- `predicted_closing_ranks`: used first by recommendations.
- `predicted_rank_bands`: used first by onboarding rank guidance.

The backend keeps `cutoff_data` and `rank_lookup` as fallback tables. UI copy
labels whether data came from ML predictions or historical fallback.

## Retraining

When a new year arrives:

1. Add the new raw cutoff and GRL rows under `ML/data/raw/`.
2. Replace the latest seat matrix JSON under `supabase_db/seed_data`.
3. Re-run build, train, and generate scripts.
4. Review `reports/cv_metrics.json` and `reports/rank_model_metrics.json`.
5. Apply `backend/migrations/005_predicted_closing_ranks.sql` if not already
   applied.
6. Load the generated CSVs with `backend/scripts/load_predictions.py`.
