# TNEA Data Preparation Summary

## Goal

Build a reliable end-to-end pipeline to:

- parse all TNEA allotment PDFs
- standardize all years and rounds into one common CSV format
- remove dirty rows
- align college filtering with the external college reference JSON
- remove architecture colleges and architecture/design branches
- produce one final CSV that is safe to use for model training

## Final Status

The final strict training dataset is ready:

- `data/processed/merged/merged_records_all_years_rounds_training_ready.csv`
- data rows: `554,166`
- abnormal ranks remaining: `0`
- legacy communities remaining (`MBCDNC`, `MBCV`, `SCA`): `0`
- architecture-only college rows remaining: `0`
- architecture/design branch rows remaining (`AR`, `BA`, `BP`, `DA`, `ID`): `0`

The removal report for the final training file is:

- `data/processed/reports/merged_records_all_years_rounds_training_ready_removed_rows.csv`
- removed rows total: `192`
- `147` rows removed for `architecture_only_college`
- `45` rows removed for `architecture_branch`

## Standardized Output Schema

The main standardized record schema used across all years and rounds is:

- `S NO`
- `APPLICATION NUMBER`
- `NAME OF THE CANDIDATE`
- `AGGREGATE MARK`
- `RANK`
- `COMMUNITY`
- `COLLEGE CODE`
- `BRANCH CODE`
- `ALLOTTED CATEGORY`

Field standardization included:

- `AGGR MARK` -> `AGGREGATE MARK`
- `APPLN NO` -> `APPLICATION NUMBER`

All values were kept as text strings from the PDF output rather than coerced aggressively.

## Main Workflow History

### 1. Custom PDF Parser Built

A custom parser was created to read TNEA allotment PDFs across multiple layout variants from different years and rounds.

Main script:

- `scripts/tnea_pdf_parser.py`

The parser was built to:

- detect year and round
- parse rows from different PDF text layouts
- keep structured record rows
- preserve auditability through manifests and optional audit files

### 2. Clean CSV Format Enforced

The parser was then adjusted so the main `records.csv` output contains only the table data from the PDF and not extraction junk.

This made every year and round export into the same clean schema shown above.

### 3. Full Batch Parse Completed

All source PDFs under `data/raw/` were batch parsed.

Current processed bundle count:

- `21` per-PDF bundles

Example bundle:

- `data/processed/bundles/2025__round_3__Round3-gen-allotments/`

Each bundle now contains:

- `records.csv`
- `manifest.csv`
- `meta.json`
- optional `audit/`
- optional `source/`

### 4. All Years and Rounds Merged

All standardized per-PDF CSV files were merged into one combined dataset with `YEAR` and `ROUND` columns.

Merged file:

- `data/processed/merged/merged_records_all_years_rounds.csv`

Row count:

- `564,924`

### 5. Dirty Rank and Community Audit

Abnormal values were audited.

Reports:

- `data/processed/reports/abnormal_ranks.csv`
- `data/processed/reports/abnormal_communities.csv`

Findings:

- abnormal communities: none outside the expected community family
- abnormal ranks: suffix-style values like `2974A`, `12837B`, `25376C`

### 6. Cleaned Merge Created

The merged dataset was cleaned by:

- dropping rows with non-numeric `RANK`
- converting `MBCDNC` -> `MBC`
- converting `MBCV` -> `MBC`
- converting `SCA` -> `SC`

Cleaned merged file:

- `data/processed/merged/merged_records_all_years_rounds_cleaned.csv`

Row count:

- `563,666`

### 7. 2025-Only College Filter Attempt

A filtered dataset was temporarily created using only `COLLEGE CODE` values present in `2025`.

File:

- `data/processed/merged/merged_records_all_years_rounds_cleaned_2025_colleges_only.csv`

Row count:

- `549,841`

This was later superseded because the user clarified that the authoritative college set should come from the external JSON file, not only from 2025 allotment appearances.

### 8. College Reference JSON Introduced

Reference file used:

- `/home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json`

Reference size:

- `466` colleges

The merge logic was updated so merged allotment data can be filtered directly by college codes from this JSON file.

### 9. Missing Colleges Listed Separately

The colleges present in the reference JSON but absent from the allotment-linked merged data were listed separately.

Report:

- `data/processed/reports/missing_reference_colleges.csv`

Missing reference colleges:

- `33`

### 10. Filtered College Reference JSON Created

The raw college reference JSON was filtered to keep only:

- colleges that actually appear in the allotment data
- non-architecture-only institutions

Generated file:

- `/home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output_present_non_architecture.json`

Colleges kept:

- `430`

Removal report:

- `/home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/removed_architecture_or_absent_colleges.csv`

Removal breakdown:

- `3` -> `architecture_only`
- `27` -> `not_present_in_allotment|architecture_only`
- `6` -> `not_present_in_allotment`

Helper script created:

- `scripts/filter_college_reference.py`

### 11. Reference-Aligned Merged Allotment File Created

The merged allotment dataset was filtered so that only college codes present in the reference JSON remain.

File:

- `data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv`

Row count:

- `554,358`

### 12. Architecture-Only Colleges Removed From Allotment Data

The allotment merged CSV was then filtered again to remove rows belonging to architecture-only colleges from the reference data.

File:

- `data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only_non_architecture.csv`

Row count:

- `554,211`

Rows removed at this stage:

- `147`

Actual architecture-only college codes that appeared in allotment rows:

- `3`
- `1400`
- `2361`

Helper script created:

- `scripts/filter_allotment_reference.py`

### 13. Architecture/Design Branch Rows Also Removed

The user then requested that architecture be removed completely from allotments as well.

That required removing branch-level rows even inside mixed colleges when `BRANCH CODE` is one of:

- `AR`
- `BA`
- `BP`
- `DA`
- `ID`

This strict training export was then generated:

- `data/processed/merged/merged_records_all_years_rounds_training_ready.csv`

Row count:

- `554,166`

Extra rows removed at this stage:

- `45` rows with architecture/design branch codes

Final removal report:

- `data/processed/reports/merged_records_all_years_rounds_training_ready_removed_rows.csv`

### 14. Directory Structure Flattened

The earlier output structure had too much nesting.

It was flattened from the older style:

- `data/processed/organized_output/<year>/round_<n>/<pdf_stem>/csv/...`

to the current cleaner layout:

- `data/processed/bundles/<year>__<round>__<pdf_stem>/`
- `data/processed/merged/`
- `data/processed/reports/`

This change also updated:

- parser defaults
- merge discovery
- README paths
- bundle metadata paths

### 15. Duplicate Stale Bundle Removed

During restructuring, a stale duplicate bundle was detected:

- `2021__unknown_round__2021-2`

This duplicated the same source PDF as:

- `2021__round_2__2021-2`

The stale duplicate had worse parse quality and inflated merged row counts, so it was removed and merge discovery was updated to deduplicate by source PDF and prefer the cleaner parse.

## Current Directory Layout

```text
data/
  raw/
    2020/
    2021/
    2022/
    2023/
    2024/
    2025/
  processed/
    bundles/
      2020__round_1__2020-1/
      ...
      2025__round_3__Round3-gen-allotments/
    merged/
      merged_records_all_years_rounds.csv
      merged_records_all_years_rounds_cleaned.csv
      merged_records_all_years_rounds_cleaned_2025_colleges_only.csv
      merged_records_all_years_rounds_cleaned_reference_colleges_only.csv
      merged_records_all_years_rounds_cleaned_reference_colleges_only_non_architecture.csv
      merged_records_all_years_rounds_training_ready.csv
    reports/
      abnormal_communities.csv
      abnormal_ranks.csv
      batch_manifest.csv
      merged_records_all_years_rounds_cleaned_reference_colleges_only_removed_rows.csv
      merged_records_all_years_rounds_training_ready_removed_rows.csv
      missing_reference_colleges.csv
```

## Main Scripts

### `scripts/tnea_pdf_parser.py`

Purpose:

- parse all PDFs
- create per-PDF bundles
- merge all bundle `records.csv` files
- support cleaned merge output
- support filtering merged output by year-based college set or JSON-based college set

### `scripts/filter_college_reference.py`

Purpose:

- filter the college reference JSON to keep only colleges that are present in allotment data
- remove architecture-only colleges from the college reference JSON

### `scripts/filter_allotment_reference.py`

Purpose:

- filter merged allotment CSV using the college reference JSON
- remove architecture-only colleges
- optionally remove architecture/design branches from mixed colleges

## Final Output Files

### Final Training Dataset

- `data/processed/merged/merged_records_all_years_rounds_training_ready.csv`

### Final Training Removal Report

- `data/processed/reports/merged_records_all_years_rounds_training_ready_removed_rows.csv`

### Reference-Cleaned Allotment Dataset

- `data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv`

### Non-Architecture College Dataset

- `data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only_non_architecture.csv`

### Missing Reference Colleges Report

- `data/processed/reports/missing_reference_colleges.csv`

### Filtered College Reference JSON

- `/home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output_present_non_architecture.json`

## Reproducible Commands

### Parse All PDFs

```bash
rtk python3 scripts/tnea_pdf_parser.py batch
```

### Merge All Standardized Records

```bash
rtk python3 scripts/tnea_pdf_parser.py merge
```

### Merge With Rank Cleanup and Community Normalization

```bash
rtk python3 scripts/tnea_pdf_parser.py merge --clean
```

### Merge Using the College Reference JSON

```bash
rtk python3 scripts/tnea_pdf_parser.py merge --clean \
  --retain-only-college-codes-from-json /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json
```

### Filter the College Reference JSON

```bash
rtk python3 scripts/filter_college_reference.py \
  /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json \
  data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv
```

### Build the Final Strict Training Dataset

```bash
rtk python3 scripts/filter_allotment_reference.py \
  /home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json \
  data/processed/merged/merged_records_all_years_rounds_cleaned_reference_colleges_only.csv \
  --drop-architecture-branches \
  --output-csv data/processed/merged/merged_records_all_years_rounds_training_ready.csv \
  --removed-report data/processed/reports/merged_records_all_years_rounds_training_ready_removed_rows.csv
```

## Validation Summary

Validation on the final strict training file confirms:

- data rows: `554,166`
- non-numeric ranks remaining: `0`
- legacy community labels remaining: `0`
- architecture-only college rows remaining: `0`
- architecture/design branch rows remaining: `0`

## Recommended Next Step For Modeling

Before training a model, do not use these fields as model inputs:

- `NAME OF THE CANDIDATE`
- `APPLICATION NUMBER`
- `S NO`

Better training inputs:

- `YEAR`
- `ROUND`
- `RANK`
- `AGGREGATE MARK`
- `COMMUNITY`

Likely target fields:

- `COLLEGE CODE`
- `BRANCH CODE`
- or a combined target such as `COLLEGE_CODE__BRANCH_CODE`
