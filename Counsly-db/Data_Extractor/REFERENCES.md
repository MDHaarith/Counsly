# References

## About Data_Extractor
Multi-pipeline repository for extracting and transforming TNEA-related PDFs and metadata into rankings, CSVs, JSON bundles, and helper datasets.

## Relevant links
- Local active code: `Allotement/scripts/college_ranking.py`
- Ranking helpers: `Allotement/scripts/ranking/`
- PDF extraction helpers: `College_Info_Done/tnea_lib/`

## Key decisions already made
- `Allotement/` is the primary active pipeline.
- `archive/` contains historical snapshots and should not be treated as the working copy.
- Outputs live in `Allotement/data/processed` and `Allotement/data/rankings`.

## Notes
- This repo mixes code and generated data.
- Keep names aligned with existing folder conventions: `allotment`, `college_info`, `ranking`, `bundle`, `cache`.
