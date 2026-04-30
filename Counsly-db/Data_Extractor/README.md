# Data_Extractor

Dataset-specific PDF extractors for TNEA and related education documents.

This repo is intentionally built around tailored parsers for known PDF families, not universal parsers. The main quality bar is extraction correctness, clean outputs, and easy reruns when a source layout changes.

## Main folders

- `Allotement/` - active allotment extraction, cleaning, training data, and ranking pipeline
- `General_Rank_List/` - year-aware general rank list parser
- `College_Info_Done/` - college metadata extraction from the TNEA information PDF
- `Seat_Matrix/` - seat-matrix extractor with text and OCR modes
- `Pass_Percentage/` - pass-percentage PDF extractor
- `geo_integration/` - integrated college latitude/longitude work focused on raw coordinate resolution accuracy, historical pipelines, and active resolver logic
- `tnea_lib/` - shared low-level PDF raw-stream helpers
- `tests/` - shared tests for common extraction helpers

## Working style

These extractors are intentionally PDF-family-specific.

That means:
- parser logic may be tuned to one document family
- layout assumptions are acceptable when they improve accuracy
- auditability and validation matter more than generic abstraction

## Recommended priorities

1. keep outputs reproducible
2. keep failures inspectable
3. add validation checks around generated data
4. reduce environment-specific path assumptions where possible
5. add tests for shared helpers and fragile parsing rules

## Quick checks

Run the shared tests:

```bash
python3 -m pytest -q
```

Launch the repo-wide TypeScript TUI:

```bash
npm run tui
```

Most mature workflow:

```bash
cd Allotement
python3 scripts/training_pipeline.py --skip-batch
```

## Notes

Generated outputs and cache folders are intentionally ignored at the repo root where appropriate so the working tree stays readable while iterating on parsers.
