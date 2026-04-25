# Working Snapshot Archive

Date:

- `2026-04-14`

Purpose:

- preserve the current working code and documentation snapshot before further cleanup or refactoring

Included files:

- `README.md`
- `HOW_TO_USE.md`
- `DATA_PREP_SUMMARY.md`
- `pyproject.toml`
- `scripts/tnea_pdf_parser.py`
- `scripts/filter_college_reference.py`
- `scripts/filter_allotment_reference.py`
- `scripts/build_training_dataset.py`

Verified state at archive time:

- single-command pipeline works with `rtk python3 scripts/build_training_dataset.py --skip-batch`
- final strict training dataset path:
  `data/processed/merged/merged_records_all_years_rounds_training_ready.csv`
- final strict training row count: `554,166`
- removed rows report path:
  `data/processed/reports/merged_records_all_years_rounds_training_ready_removed_rows.csv`

Archive outputs:

- folder archive:
  `archive/working_snapshot_2026-04-14/`
- compressed archive:
  `archive/working_snapshot_2026-04-14.tar.gz`
