# TNEA Ranking Algorithm

## Purpose

`scripts/college_ranking.py` is the canonical ranking pipeline for the cleaned
non-architecture TNEA dataset. It ranks colleges using the final strict
training CSV instead of subjective manual boosts.

## Inputs

- `data/processed/merged/merged_records_all_years_rounds_training_ready.csv`
- `/home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output_present_non_architecture.json`
- `/home/mdhaarith/Desktop/Data_Extractor/Inputs/College_Info_Done/output.json`

The raw `output.json` is still read so the loader can recover clean college
names from the PDF-derived tail-contaminated fields.

## Score Design

The final composite score is a weighted sum of six dimensions:

- `selectivity` 35%
  Recency-weighted round-1 admitted-rank percentiles across `2023`, `2024`, and `2025`.
  It uses within-year percentile scoring on median rank, upper-quartile rank,
  and lower-quartile rank.

- `academic_quality` 35%
  Recency-weighted round-1 aggregate-mark percentiles across `2023`, `2024`,
  and `2025`.

- `branch_strength` 12%
  For each `YEAR + BRANCH_CODE`, the algorithm compares colleges against direct
  branch peers using branch closing-rank percentiles, then aggregates those
  branch peer scores back to the college level.

- `institutional_quality` 8%
  Uses only capped support signals from the college reference:
  NBA-accredited branch ratio, placement percentage, and autonomy.

- `web_reputation` 6%
  Uses capped website-derived support signals:
  NAAC, NIRF, web placement %, average CTC, faculty count, and research mentions.

- `trend` 4%
  Measures improvement or decline in selectivity from `2020` through `2025`.

## Reliability Control

This algorithm explicitly avoids over-ranking tiny sample sizes.

- Year-level selectivity and academic scores are shrunk back toward neutral when
  a college has very few round-1 admissions in that year.
- Colleges missing multiple recent years are shrunk back toward neutral instead
  of being treated as fully established from one strong snapshot.
- Branch-strength scores are also shrunk when the total weighted branch sample
  size is small.

This is why single-admission colleges no longer jump near the top of the table.
Seat-matrix signals are not part of this algorithm. The model also does not
contain a manual prestige prior.

## Output Files

Running live scrape plus ranking:

```bash
rtk python3 scripts/college_ranking.py
```

Running from cache only:

```bash
rtk python3 scripts/college_ranking.py --skip-scrape
```

writes:

- `data/rankings/college_rankings.json`
- `data/rankings/college_rankings.csv`
- `data/rankings/scraped_cache/*.json`

The JSON includes:

- overall ranking
- ranking by community
- ranking by branch
- ranking by district
- per-college dimension scores

## Current Output

The latest generated ranking covers:

- `430` colleges
- `20` branch ranking views
- `6` community ranking views
- `12` district ranking views
- `426` cached scrape result files
- `161` colleges with at least one usable scraped signal

## Notes

- Web scraping is now part of the score as a capped `web_reputation` dimension.
- Hard-coded government/private tier boosts are not part of the score.
- The ranking is primarily driven by actual allotment behavior plus reference
  metadata, with scraped website evidence added as support.
