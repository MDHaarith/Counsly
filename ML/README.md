# Counsly ML Workspace

This folder contains the local data inputs for rank-prediction experiments.
The source-of-truth copies remain under `supabase_db/seed_data`; files here are
working copies for ML analysis.

## Raw Data

| File | Source | Rows | Purpose |
|---|---|---:|---|
| `data/raw/general_rank_list_2020_2025.csv` | `supabase_db/seed_data/rank_lookup/general_rank_list_2020_2025.csv` | 1,017,768 | Primary training data for aggregate-mark to rank/percentile modeling |
| `data/raw/cutoffs_2020_2025_training_ready.csv` | `supabase_db/seed_data/cutoff_data/cutoffs_2020_2025_training_ready.csv` | 554,166 | Validation/outcome-analysis data for recommendation behavior |

## Recommended Rank Model

Use total students per year as a training feature or normalization factor.
Raw rank depends on cohort size, so the safer model is:

```text
aggregate_mark -> historical percentile band
historical percentile band * expected_total_students -> predicted rank band
```

For 2026, set an expected cohort size and convert percentile bands back into
rank bands. This avoids treating rank 20,000 as equivalent across years with
different applicant counts.

## Profiling

Generate yearly cohort totals and summary stats:

```bash
python3 ML/scripts/profile_rank_data.py
```

This writes:

- `ML/reports/rank_year_summary.csv`
- `ML/reports/community_year_counts.csv`

Use `rank_year_summary.csv` to choose `EXPECTED_TOTAL_STUDENTS` for 2026 or to
train a model with cohort size as an explicit feature.
