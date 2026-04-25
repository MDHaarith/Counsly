# Current Project State

## What we are building
A structured workspace for the Data_Extractor repo, with the current active work centered on the Allotement ranking pipeline and its shared parsing/ranking helpers.

## What good output looks like
Scripts should stay deterministic, produce clean CSV/JSON outputs under `Allotement/data/processed` and `Allotement/data/rankings`, and keep ranking logic easy to trace from input PDFs through aggregation and output generation.

## Active constraints
- Preserve archived snapshots as historical references.
- Keep script behavior compatible with existing file layouts and cached outputs.
- Prefer changes that fit the repo's script-first workflow.

## What to avoid
Avoid broad cleanup in `archive/`, changing generated cache files by accident, or introducing new abstractions unless they remove real duplication.

## Status
Initialized. Next step is to document specific workflow commands and refresh this file as the active focus changes.
