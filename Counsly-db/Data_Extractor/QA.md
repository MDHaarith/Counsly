# QA Workflow

This repo is intentionally extractor-first and PDF-family-specific, so QA should focus on correctness, cleanliness, and inspectability rather than generic parser elegance.

## Quick checks

Run shared tests:

```bash
python3 -m pytest -q
```

Run high-level output validation:

```bash
python3 validate_outputs.py
```

Generate QA summaries:

```bash
python3 qa/run_all_reports.py
```

Reports are written to:

- `qa/reports/allotement_summary.json`
- `qa/reports/allotement_summary.md`
- `qa/reports/college_info_summary.json`
- `qa/reports/college_info_summary.md`
- `qa/reports/grl_summary.json`
- `qa/reports/grl_summary.md`
- `qa/reports/geo_summary.json`
- `qa/reports/geo_summary.md`

## What these reports currently check

### Allotement
- training row counts
- year distribution
- round distribution
- community distribution
- unique college and branch counts
- invalid community rows
- non-numeric rank rows
- ranking score bound checks
- missing district coverage in ranking output

### College info
- raw vs filtered college counts
- key field missingness
- district distribution
- autonomy distribution
- course coverage
- NBA-accredited course coverage

### General Rank List
- year distribution
- community distribution
- blank community-rank rows
- blank aggregate-mark rows

### Geo integration
- legacy geolocation snapshot presence
- active geolocation snapshot presence
- clean-output record counts
- coordinate coverage counts
- unresolved snapshot presence
- emphasis on raw accuracy coverage, not UI/runtime polish

## Recommended use

After major extraction or cleanup changes:
1. run tests
2. run `validate_outputs.py`
3. run `qa/run_all_reports.py`
4. inspect the markdown summaries in `qa/reports/`

This gives a fast sanity pass before trusting downstream analysis.
