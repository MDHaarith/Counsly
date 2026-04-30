# Honest Ranking Algorithm

This folder is the separate storage location for the current honest TNEA
college ranking algorithm.

It preserves:

- the dedicated launcher: [run.py](/home/mdhaarith/Desktop/Data_Extractor/Inputs/Allotement/algorithms/honest_ranking/run.py:1)
- the frozen algorithm specification: [algorithm_snapshot.json](/home/mdhaarith/Desktop/Data_Extractor/Inputs/Allotement/algorithms/honest_ranking/algorithm_snapshot.json:1)

The executable logic still lives in the canonical files under:

- [scripts/college_ranking.py](/home/mdhaarith/Desktop/Data_Extractor/Inputs/Allotement/scripts/college_ranking.py:1)
- [scripts/ranking](/home/mdhaarith/Desktop/Data_Extractor/Inputs/Allotement/scripts/ranking)

This folder exists so the honest algorithm has its own clean place and a stable
entrypoint without mixing it into the broader data-processing pipeline.

## Current Rules

- no seat matrix signals
- no manual prestige prior
- equal weight for `selectivity` and `academic_quality`
- web scraping kept as a capped support signal

## Current Weights

- `selectivity`: `35%`
- `academic_quality`: `35%`
- `branch_strength`: `12%`
- `institutional_quality`: `8%`
- `web_reputation`: `6%`
- `trend`: `4%`

## Run

Use cached scrape data:

```bash
rtk python3 algorithms/honest_ranking/run.py --skip-scrape
```

Run with live scraping:

```bash
rtk python3 algorithms/honest_ranking/run.py
```
