# TNEA PDF Parser

This project parses TNEA allotment PDFs into clean, standardized CSV outputs.

## Structure

```text
.
├── data/
│   ├── raw/          # source PDFs grouped by year and round
│   └── processed/
│       ├── bundles/  # per-PDF parsed outputs
│       ├── merged/   # merged datasets
│       └── reports/  # manifests and reports
├── scripts/
│   ├── build_training_dataset.py
│   ├── filter_allotment_reference.py
│   ├── filter_college_reference.py
│   └── tnea_pdf_parser.py
├── .gitignore
├── pyproject.toml
└── README.md
```

`scripts/tnea_pdf_parser.py` parses the allotment PDFs into flat per-PDF bundles.

`scripts/build_training_dataset.py` runs the full pipeline in one command and
produces the final strict training dataset.

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
rtk python3 scripts/build_training_dataset.py
```

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
