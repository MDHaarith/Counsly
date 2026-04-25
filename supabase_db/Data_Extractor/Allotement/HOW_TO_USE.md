# How To Use The Code

## Prerequisite

All shell commands in this project should be run with the `rtk` prefix.

Examples:

```bash
rtk python3 scripts/tnea_pdf_parser.py batch
rtk python3 scripts/tnea_pdf_parser.py merge
```

## Project Layout

```text
data/
  raw/        # source PDFs
  processed/
    bundles/  # per-PDF parsed outputs
    merged/   # merged datasets
    reports/  # manifests and cleanup reports
  rankings/   # college ranking outputs
scripts/
  training_pipeline.py
  build_training_dataset.py   # compatibility wrapper
  tnea_pdf_parser.py
  filter_college_reference.py
  filter_allotment_reference.py
  college_ranking.py
algorithms/
  honest_ranking/
    run.py
```

## Main Scripts

### `scripts/tnea_pdf_parser.py`

Use this for:

- parsing one PDF
- parsing all PDFs
- merging all parsed records

### `scripts/filter_college_reference.py`

Use this for:

- filtering the college reference JSON
- removing architecture-only colleges from the college reference

### `scripts/filter_allotment_reference.py`

Use this for:

- filtering merged allotment data using the college reference JSON
- removing architecture-only colleges
- optionally removing architecture/design branch rows too

### `scripts/build_training_dataset.py`

Use this for:

- compatibility with the older command name
- forwarding to the canonical training pipeline

### `scripts/training_pipeline.py`

Use this for:

- one single end-to-end command
- parsing PDFs
- merging cleaned records
- filtering by the college reference JSON
- producing the final strict training-ready CSV

### `scripts/college_ranking.py`

Use this for:

- generating the canonical college ranking from the cleaned training dataset
- writing JSON and CSV ranking outputs
- producing overall, community, branch, and district ranking views

### `../tui/ranking_tui.ts`

Use this for:

- opening a repo-wide terminal UI for the extractor workspace
- browsing ranking output, QA summaries, pipeline manifest, and docs
- searching colleges and inspecting dimension scores
- refreshing ranking JSON or other common outputs from inside the TUI
- exploring community, branch, and district views without touching seat-matrix data

### `algorithms/honest_ranking/run.py`

Use this for:

- running the same honest ranking algorithm from a separate isolated folder
- preserving a stable launcher and frozen snapshot outside `scripts/`

## Single Command Pipeline

If you want the final strict training dataset in one command, use:

```bash
rtk python3 scripts/training_pipeline.py
```

This will:

- parse all PDFs under `data/raw/`
- rebuild processed bundles
- create the reference-filtered merged CSV
- refresh the filtered college reference JSON
- create the final strict training-ready CSV

If the bundles are already built and you only want to rebuild the final outputs:

```bash
rtk python3 scripts/training_pipeline.py --skip-batch
```

Compatibility command:

```bash
rtk python3 scripts/build_training_dataset.py --skip-batch
```

Open the TypeScript repo TUI from the repo root:

```bash
node tui/ranking_tui.ts
```

Or:

```bash
npm run tui
```

Separate honest ranking launcher:

```bash
rtk python3 algorithms/honest_ranking/run.py --skip-scrape
```

## 1. Parse One PDF

```bash
rtk python3 scripts/tnea_pdf_parser.py parse 'data/raw/2025/2025-3/Round3-gen-allotments.pdf'
```

Optional flags:

- `--max-pages 3` to test only a few pages
- `--with-audit-files` to also write `audit/` outputs
- `--copy-source` to copy the source PDF into the bundle

Example:

```bash
rtk python3 scripts/tnea_pdf_parser.py parse \
  'data/raw/2024/2024-3/2024-3.pdf' \
  --with-audit-files
```

Output goes to:

- `data/processed/bundles/<year>__<round>__<pdf_stem>/`

## 2. Parse All PDFs

```bash
rtk python3 scripts/tnea_pdf_parser.py batch
```

This scans:

- `data/raw/`

and writes:

- per-PDF bundle outputs into `data/processed/bundles/`
- batch manifest into `data/processed/reports/batch_manifest.csv`
- merged files into `data/processed/merged/`

## 3. Merge All Parsed Records

```bash
rtk python3 scripts/tnea_pdf_parser.py merge
```

Output:

- `data/processed/merged/merged_records_all_years_rounds.csv`

This merged file includes:

- `YEAR`
- `ROUND`
- the standardized allotment columns

## 4. Merge With Rank Cleanup And Community Normalization

```bash
rtk python3 scripts/tnea_pdf_parser.py merge --clean
```

This does:

- removes rows with non-numeric `RANK`
- converts `MBCDNC` -> `MBC`
- converts `MBCV` -> `MBC`
- converts `SCA` -> `SC`

Output:

- `data/processed/merged/merged_records_all_years_rounds_cleaned.csv`

## 5. Merge Using The College Reference JSON

Reference file:

- `/home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json`

Command:

```bash
rtk python3 scripts/tnea_pdf_parser.py merge --clean \
  --retain-only-college-codes-from-json /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json
```

Output:

- `data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv`

This keeps only rows whose `COLLEGE CODE` exists in the reference JSON.

## 6. Filter The College Reference JSON

This creates a cleaned college reference JSON that keeps only:

- colleges present in allotment data
- non-architecture-only institutions

Command:

```bash
rtk python3 scripts/filter_college_reference.py \
  /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json \
  data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv
```

Outputs:

- `/home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output_present_non_architecture.json`
- `/home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/removed_architecture_or_absent_colleges.csv`

## 7. Remove Architecture-Only Colleges From Allotment Data

Command:

```bash
rtk python3 scripts/filter_allotment_reference.py \
  /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json \
  data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv
```

Outputs:

- `data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only_non_architecture.csv`
- default removed-row report if not overridden

This removes rows from architecture-only colleges.

## 8. Create The Final Training-Ready Dataset

This is the strict version. It removes:

- dirty rank rows
- old community labels
- colleges not in the reference JSON
- architecture-only colleges
- architecture/design branch rows inside mixed colleges

Command:

```bash
rtk python3 scripts/filter_allotment_reference.py \
  /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json \
  data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv \
  --drop-architecture-branches \
  --output-csv data/processed/merged/merged_records_all_years_rounds_training_ready.csv \
  --removed-report data/processed/reports/merged_records_all_years_rounds_training_ready_removed_rows.csv
```

Final outputs:

- `data/processed/merged/merged_records_all_years_rounds_training_ready.csv`
- `data/processed/reports/merged_records_all_years_rounds_training_ready_removed_rows.csv`

## Current Important Files

### Final strict training dataset

- `data/processed/merged/merged_records_all_years_rounds_training_ready.csv`

## 9. Generate The College Rankings

This ranking uses the final strict training dataset plus the filtered
non-architecture college reference JSON.

Command:

```bash
rtk python3 scripts/college_ranking.py
```

Cached-only mode:

```bash
rtk python3 scripts/college_ranking.py --skip-scrape
```

Outputs:

- `data/rankings/college_rankings.json`
- `data/rankings/college_rankings.csv`

Interactive viewer and repo control surface from the repo root:

```bash
node tui/ranking_tui.ts
```

The canonical score uses:

- `selectivity` from round-1 ranks
- `academic_quality` from admitted marks
- `branch_strength` from branch-wise peer comparison
- `institutional_quality` from NBA ratio, placement record, and autonomy
- `web_reputation` from live or cached college website scraping
- `trend` from 2020-2025 movement

Small-sample colleges are shrunk toward neutral so tiny admission counts do not
artificially jump to the top. Seat-matrix signals are not used.

See:

- `RANKING_ALGORITHM.md`

### Final training removal report

- `data/processed/reports/merged_records_all_years_rounds_training_ready_removed_rows.csv`

### Reference-filtered merged dataset

- `data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv`

### Non-architecture college reference JSON

- `/home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output_present_non_architecture.json`

## Recommended Order

If you want to regenerate everything from scratch, use this order:

1. `rtk python3 scripts/tnea_pdf_parser.py batch`
2. `rtk python3 scripts/tnea_pdf_parser.py merge --clean --retain-only-college-codes-from-json /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json`
3. `rtk python3 scripts/filter_college_reference.py /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv`
4. `rtk python3 scripts/filter_allotment_reference.py /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv --drop-architecture-branches --output-csv data/processed/merged/merged_records_all_years_rounds_training_ready.csv --removed-report data/processed/reports/merged_records_all_years_rounds_training_ready_removed_rows.csv`

Or just run:

1. `rtk python3 scripts/training_pipeline.py`

## Notes For Training

For ML training, do not use these fields as model inputs:

- `NAME OF THE CANDIDATE`
- `APPLICATION NUMBER`
- `S NO`

Better input fields:

- `YEAR`
- `ROUND`
- `RANK`
- `AGGREGATE MARK`
- `COMMUNITY`

Typical target choices:

- `COLLEGE CODE`
- `BRANCH CODE`
- combined `COLLEGE CODE` + `BRANCH CODE`
