# TNEA PDF Parser

This project parses TNEA allotment PDFs into clean, standardized CSV outputs.
It also includes a canonical college-ranking pipeline built on the cleaned
training dataset.

## Structure

```text
.
├── data/
│   ├── raw/          # source PDFs grouped by year and round
│   ├── processed/
│       ├── bundles/  # per-PDF parsed outputs
│       ├── merged/   # merged datasets
│       └── reports/  # manifests and reports
│   └── rankings/     # ranking JSON and CSV outputs
├── algorithms/
│   └── honest_ranking/   # isolated storage for the honest ranking algorithm
├── scripts/
│   ├── training_pipeline.py
│   ├── build_training_dataset.py
│   ├── college_ranking.py
│   ├── filter_allotment_reference.py
│   ├── filter_college_reference.py
│   └── tnea_pdf_parser.py
├── .gitignore
├── pyproject.toml
└── README.md
```

`scripts/tnea_pdf_parser.py` parses the allotment PDFs into flat per-PDF bundles.

`scripts/training_pipeline.py` is the canonical end-to-end pipeline and produces
the final strict training dataset.

`scripts/build_training_dataset.py` is kept as a compatibility wrapper.

`scripts/college_ranking.py` is the canonical ranking algorithm for the cleaned
non-architecture college set.

`algorithms/honest_ranking/` stores the isolated launcher and frozen snapshot
for the current honest ranking algorithm.

The main output is a clean `records.csv` with the same headers across all years and rounds:

- `S NO`
- `APPLICATION NUMBER`
- `NAME OF THE CANDIDATE`
- `AGGREGATE MARK`
- `RANK`
- `COMMUNITY`
- `COLLEGE CODE`
- `BRANCH CODE`
- `ALLOTTED CATEGORY`

Every value is written as text exactly as printed in the PDF.

## Usage

Parse one PDF:

```bash
rtk python3 scripts/tnea_pdf_parser.py parse 'data/raw/2025/2025-3/Round3-gen-allotments.pdf'
```

Parse every PDF recursively under the current folder:

```bash
rtk python3 scripts/tnea_pdf_parser.py batch
```

Run the full pipeline end-to-end in one command:

```bash
rtk python3 scripts/training_pipeline.py
```

Generate the college rankings from the final training-ready CSV with live web scraping enabled:

```bash
rtk python3 scripts/college_ranking.py
```

Reuse only cached scrape data:

```bash
rtk python3 scripts/college_ranking.py --skip-scrape
```

Run the same honest ranking algorithm from its separate storage folder:

```bash
rtk python3 algorithms/honest_ranking/run.py --skip-scrape
```

Launch the TypeScript terminal UI for the broader extractor workspace from the repo root:

```bash
cd ..
node tui/ranking_tui.ts
```

Or:

```bash
cd ..
npm run tui
```

The TUI includes:
- dashboard view across extractor outputs
- ranking explorer
- QA summaries for allotement, college info, GRL, and geo
- training pipeline manifest view
- docs browser
- quick actions for common pipeline commands

Merge all clean per-round CSVs into one file with `YEAR` and `ROUND` columns:

```bash
rtk python3 scripts/tnea_pdf_parser.py merge
```

Smoke-test just the first few pages:

```bash
rtk python3 scripts/tnea_pdf_parser.py parse 'data/raw/2024/2024-3/2024-3.pdf' --max-pages 3
```

If you also want the raw extraction/audit files:

```bash
rtk python3 scripts/tnea_pdf_parser.py parse 'data/raw/2024/2024-3/2024-3.pdf' --with-audit-files
```

## Output Layout

Outputs are written under `data/processed/bundles/<year>__<round>__<pdf_stem>/`.

Each bundle contains:

- `records.csv`
- `manifest.csv`
- `meta.json`
- `audit/records_full.csv`, `audit/pages.csv`, `audit/unparsed_lines.csv` only when `--with-audit-files` is used
- `source/<original.pdf>` only when `--copy-source` is used

The default merged file is written to:

- `data/processed/merged/merged_records_all_years_rounds.csv`

The batch manifest is written to:

- `data/processed/reports/batch_manifest.csv`

The ranking outputs are written to:

- `data/rankings/college_rankings.json`
- `data/rankings/college_rankings.csv`

Filter a college reference JSON down to colleges that are present in the allotment
data and not architecture-only institutions:

```bash
rtk python3 scripts/filter_college_reference.py \
  /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json \
  data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv
```

Filter the merged allotment CSV to remove architecture-only colleges from the
same reference JSON:

```bash
rtk python3 scripts/filter_allotment_reference.py \
  /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json \
  data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv
```

For a strict training file, also drop architecture/design branch rows inside
mixed colleges:

```bash
rtk python3 scripts/filter_allotment_reference.py \
  /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json \
  data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv \
  --drop-architecture-branches \
  --output-csv data/processed/merged/merged_records_all_years_rounds_training_ready.csv \
  --removed-report data/processed/reports/merged_records_all_years_rounds_training_ready_removed_rows.csv
```

## Ranking Algorithm

The canonical ranking score uses these dimensions:

- `selectivity` 35%: recency-weighted round-1 admitted-rank percentiles
- `academic_quality` 35%: recency-weighted aggregate-mark percentiles
- `branch_strength` 12%: branch-wise peer comparison using closing-rank percentiles
- `institutional_quality` 8%: NBA depth, placement record, and autonomy
- `web_reputation` 6%: capped score from scraped NAAC, NIRF, placement, CTC, faculty, and research signals
- `trend` 4%: selectivity improvement across 2020-2025

Small-sample colleges are shrunk toward neutral so a tiny number of admissions
cannot dominate the ranking. Seat-matrix signals are not used. The model does
not include a manual prestige prior.

The TypeScript TUI is now a broader control surface for the extractor repo.
It still includes ranking exploration, but it also covers QA summaries,
pipeline state, docs, and common command entrypoints. It does not rely on
seat-matrix data for ranking features.

See [RANKING_ALGORITHM.md](/home/mdhaarith/Desktop/Data_Extractor/Inputs/Allotement/RANKING_ALGORITHM.md:1)
for the methodology and output details.
