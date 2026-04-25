# Counsly Supabase Data Pipeline

This folder keeps both the working extractor pipeline and the seed data used for Supabase.

## Structure

- `Data_Extractor/` - active extractor workspace for PDFs, parsers, generated JSON/CSV, QA reports, and reruns.
- `seed_data/` - compact staged CSV/JSON snapshots copied from the extractor outputs.
- `scripts/` - direct database ingestion tools for Supabase.
- `requirements.txt` - Python packages for extractor and ingestion work.

## Seat Matrix Round Update

After extracting a new round, make sure these files are current:

```bash
supabase_db/Data_Extractor/Seat_Matrix/output/seat_matrix_data.json
supabase_db/Data_Extractor/Seat_Matrix/output/branch_codes_filtered.json
```

Dry-run the upload:

```bash
DATABASE_URL="postgresql://..." python3 supabase_db/scripts/ingest_seat_matrix.py --season-year 2026 --round-number 1 --dry-run
```

Upload to Supabase:

```bash
DATABASE_URL="postgresql://..." python3 supabase_db/scripts/ingest_seat_matrix.py --season-year 2026 --round-number 1
```

The script upserts:

- `branches`
- `college_branches`
- one separate 2026 seat-matrix table per round, for example `seat_matrix_2026_r1`
- `seat_matrix_round_tables`

Use `--sync-current` when this uploaded round should also replace the app-facing `seat_matrix_current` mirror. The app uses this mirror to mimic real choice filling: college-branch rows with `total = 0` disappear from recommendations, explore details, and choice filing.

```bash
DATABASE_URL="postgresql://..." python3 supabase_db/scripts/ingest_seat_matrix.py --season-year 2026 --round-number 1 --sync-current
```

## Validation

Validate the active extractor outputs:

```bash
rtk python3 backend/scripts/reference_validate.py
```

## Historical Launch Load

Apply all migrations before loading:

```bash
psql "$DATABASE_URL" -f backend/migrations/001_initial_schema.sql
psql "$DATABASE_URL" -f backend/migrations/002_launch_schema_gaps.sql
psql "$DATABASE_URL" -f backend/migrations/003_decimal_aggregate_marks.sql
```

Load the large historical datasets with the direct loaders rather than generating one massive SQL file:

```bash
DATABASE_URL="postgresql://..." python3 backend/scripts/load_cutoffs.py
python3 backend/scripts/build_rank_lookup.py --out /tmp/counsly-rank-lookup.csv
DATABASE_URL="postgresql://..." python3 backend/scripts/load_rank_lookup.py /tmp/counsly-rank-lookup.csv
```

The loaders preserve decimal aggregate marks and update `data_freshness` so recommendations and rank-band gates can open.
