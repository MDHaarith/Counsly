# General Rank List Parser

This folder now includes a dataset-specific parser for the TNEA General Rank List PDFs in `GRL-2020/` through `GRL-2025/`.

The parser is tailored to the actual schema drift in these files:

- `2020`: `RANK, APPLICATION NUMBER, NAME, DOB, COMMUNITY, CUTOFF, COMMUNITY RANK`
- `2021`: `RANK, APPLICATION NUMBER, NAME, AGGREGATE MARK, DOB, COMMUNITY, COMMUNITY RANK`
- `2022` to `2024`: `RANK, APPLICATION NUMBER, NAME, DOB, AGGREGATE MARK, COMMUNITY, COMMUNITY RANK`
- `2025`: `S NO, APPLICATION NUMBER, AGGREGATE MARK, GENERAL RANK, COMMUNITY, COMMUNITY RANK`

It also handles PDF-specific edge cases that show up in the real files here:

- names wrapped onto the next line
- names glued directly to DOB or mark values
- rows with missing community rank
- the `2022` legal footnote on the last page
- the `2025` no-name / no-DOB layout

## Script

Use:

```bash
rtk python3 scripts/general_rank_list_parser.py --help
```

Single PDF-only workflow:

```bash
rtk python3 scripts/single_grl_workflow.py
```

This is the small one-shot workflow for this folder:

- read every `GRL-<year>/GRL-<year>.pdf`
- parse each PDF with the working year-aware parser
- normalize `OC` community ranks
- write per-year `records.csv` bundles
- write the compact merged CSV:
  `processed/merged/merged_general_rank_list_all_years.csv`

If you want the lower-level parser directly:

```bash
rtk python3 scripts/general_rank_list_parser.py batch
rtk python3 scripts/general_rank_list_parser.py merge
```

Image-based row-fragment concatenation and cleanup:

```bash
rtk python3 scripts/concatenate_table_rows.py input.png \
  --debug-output output/debug_rows.png \
  --clean-mask-output output/clean_rows_mask.png \
  --stacked-rows-output output/training_rows.png \
  --rows-json-output output/rows.json
```

This utility is for the exact case where a valid row should span the full table width
like your first example, and short partial fragments like your second example should be
removed. The most important tuning flag is:

```bash
--min-row-width-ratio 0.60
```

Increase it to remove more short fragments. Lower it if valid rows are being dropped.

If you want the final training data to contain only the valid full rows, use:

```bash
--stacked-rows-output output/training_rows.png
```

That file is a vertical concatenation of only the kept rows.

Parse one PDF:

```bash
rtk python3 scripts/general_rank_list_parser.py parse GRL-2024/GRL-2024.pdf
```

Parse every PDF in this folder:

```bash
rtk python3 scripts/general_rank_list_parser.py batch
```

Merge all parsed bundles into one CSV:

```bash
rtk python3 scripts/general_rank_list_parser.py merge
```

Write audit files for a single PDF:

```bash
rtk python3 scripts/general_rank_list_parser.py parse GRL-2022/GRL-2022.pdf --with-audit-files
```

## Outputs

Outputs are written under `processed/`:

- `processed/bundles/<year>__<pdf_stem>/records.csv`
- `processed/bundles/<year>__<pdf_stem>/meta.json`
- `processed/bundles/<year>__<pdf_stem>/audit/...` only when `--with-audit-files` is used
- `processed/reports/batch_manifest.csv`
- `processed/merged/merged_general_rank_list_all_years.csv`

The standardized CSV columns are:

- `S NO`
- `GENERAL RANK`
- `APPLICATION NUMBER`
- `NAME OF THE CANDIDATE`
- `DATE OF BIRTH`
- `AGGREGATE MARK`
- `COMMUNITY`
- `COMMUNITY RANK`
