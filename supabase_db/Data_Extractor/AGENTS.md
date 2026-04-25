# Data_Extractor

## Identity
You are helping mdhaarith maintain a multi-pipeline data extraction repo for TNEA ranking and related PDF/JSON processing.

## This Project
This repo contains several extraction workflows: `Allotement` is the active ranking pipeline, `General_Rank_List` handles table extraction, `Seat_Matrix` parses seat matrix PDFs, `Pass_Percentage` extracts pass percentages, and `College_Info_Done` holds reusable TNEA parsing helpers.

## Rules
- Prefer small, local changes over broad refactors.
- Treat `archive/` as read-only unless explicitly asked.
- Check `CONTEXT.md` before changing scripts or data flow.

## Commands
`python Allotement/scripts/college_ranking.py --help` | `pytest` | `python Allotement/scripts/college_ranking.py --skip-scrape --verbose`

## Avoid
- Don't rewrite generated data under `data/` unless the task is about regeneration.
- Don't modify archived snapshots unless needed for a specific fix.
