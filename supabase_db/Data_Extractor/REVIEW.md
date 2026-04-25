# Data_Extractor Review

## Framing

This repository is best understood as a collection of tailored PDF extractors for known TNEA-related document families. It is not trying to be a universal PDF parsing framework.

That framing changes what good engineering looks like here.

The main goals are:
- accurate extraction for known source PDFs
- clean, inspectable outputs
- manageable updates when document layouts shift
- enough structure that downstream analysis remains trustworthy

## What is strong

### 1. `Allotement/` is the most mature pipeline
It has the clearest end-to-end workflow:
- parse raw PDFs
- build bundle outputs
- merge cleaned records
- filter reference data
- produce training-ready outputs
- generate rankings

### 2. Auditability is present
The active parsers support structured outputs and optional audit artifacts, which is exactly what a tailored extractor repo should have.

### 3. Shared low-level extraction exists
`tnea_lib/raw_stream.py` centralizes raw stream decoding and already has tests. That is a good foundation for the PDF families that rely on custom encoded streams.

### 4. Downstream value exists
Even though this repo is extractor-first, `Allotement/` already creates clean datasets and ranking outputs, which makes the extracted data more useful than one-off JSON dumps.

## Main weaknesses

### 1. Repo hygiene is inconsistent
Generated outputs, caches, and local artifacts were not consistently ignored at the repo root.

### 2. Validation is still lighter than it should be
Because the parsers are intentionally tailored, correctness checks matter even more. The current repo would benefit from more validation scripts and coverage checks around generated outputs.

### 3. Some key paths are still too environment-specific
Absolute paths are acceptable for local work, but they make reruns and maintenance harder than necessary.

### 4. Maturity varies by extractor
`Allotement/` is structured. Some other folders are more utility-like and would benefit from simple validation and usage notes.

## Current recommendations

### High priority
1. keep the active `Allotement/` workflow as the canonical pipeline
2. add lightweight validation scripts for major generated datasets
3. reduce path hardcoding where it is easy and low-risk
4. keep repo noise out of git status

### Medium priority
1. add tests for shared helper logic
2. add focused parser regression tests for known tricky formats
3. add dataset summaries or manifests for non-Allotement outputs

### Low priority
1. broader refactors for elegance
2. over-generalizing parsers
3. building abstractions that do not improve extraction accuracy or maintenance

## Immediate improvements made in this copy

- added a root `.gitignore`
- added a root `README.md`
- documented this review in `REVIEW.md`
- next recommended step: add validation scripts for generated outputs
