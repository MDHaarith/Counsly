# Clean Algorithm Snapshot

Date:

- `2026-04-14`

Purpose:

- preserve the current working state after introducing the canonical single-entry pipeline

Canonical entry script:

- `scripts/training_pipeline.py`

Compatibility wrapper:

- `scripts/build_training_dataset.py`

Verified command:

```bash
rtk python3 scripts/training_pipeline.py --skip-batch
```

Verified outputs:

- final training CSV:
  `data/processed/merged/merged_records_all_years_rounds_training_ready.csv`
- final training removed-rows report:
  `data/processed/reports/merged_records_all_years_rounds_training_ready_removed_rows.csv`
- pipeline manifest:
  `data/processed/reports/training_pipeline_manifest.json`

Verified counts:

- training rows: `554,166`
- removed rows: `192`
- bad ranks remaining: `0`
- legacy community labels remaining: `0`
- architecture branch rows remaining: `0`

Archive outputs:

- folder archive:
  `archive/clean_algorithm_snapshot_2026-04-14/`
- compressed archive:
  `archive/clean_algorithm_snapshot_2026-04-14.tar.gz`
