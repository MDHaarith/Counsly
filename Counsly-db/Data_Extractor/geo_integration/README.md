# Geo Integration

This folder brings the older latitude/longitude college geolocation work into the `Data_Extractor` copy while preserving the original external projects unchanged.

## Included here

### 1. `College_Details/`
A copied historical geolocation workspace.

This is preserved here as a reference and legacy pipeline snapshot. It contains:
- older Python browser-automation based Google Maps extraction flows
- archived intermediate outputs
- older validation and second-pass review scripts
- historical source inputs and experiments

The original external project was not modified. This is a copied integration snapshot.

### 2. `active/v4-go/`
The newer active Go-based coordinate resolver.

This is the stronger current geolocation pipeline and should be treated as the main path for raw accuracy work. It uses:
- query normalization
- manual overrides
- place cache
- parent campus fallback
- gosom/google-maps-scraper provider flow
- candidate scoring and rejection logic

### 3. `active/v4go_intermediate/`
Copied generated outputs from the active Go pipeline.

## Why this is here

This integration makes geolocation part of the broader extractor workspace instead of leaving it disconnected.

That matters because geolocation can support:
- district cleanup and location sanity checks
- map-based downstream analysis
- future college discovery and comparison features
- joining extracted college metadata with coordinates

## Important note

This folder currently preserves the imported geolocation projects and documents them inside the extractor workspace.
It does not yet rewrite the whole geo stack to use repo-local relative references everywhere.

## Recommended usage

If you want to inspect the older historical project, start with:
- `College_Details/README.md`

If you want the newer active resolver, start with:
- `active/v4-go/README.md`

## Current trial status

A full trial on all 466 colleges was run in the integrated copy.

Current reality:
- coverage is complete because the imported place cache is very strong
- this means current output quality is heavily dependent on cache quality
- a few cache entries appear suspicious and should be disabled or corrected instead of being trusted blindly
- the next accuracy push should focus on cache hygiene, stricter acceptance rules, and provider-backed re-resolution for suspicious cases

## Canonical engineering core

Per current scope, the canonical working set is now:
- non-architecture colleges from College Info
- intersected with colleges present in Allotement
- seat matrix and pass percentage are not part of the canonical filter for this core set

Current count:
- `430` colleges

Prepared files:
- `geo_integration/core_colleges_college_info_allotement_430.json`
- `geo_integration/active/v4-go/college_names_only_core_430_allotement.json`
- `geo_integration/active/v4go_intermediate/college_names_only_core_430_allotement_clean_output.json`

Algorithmic workflow:
- `geo_integration/build_core_geo_alignment.py`
- `geo_integration/core_colleges_college_info_allotement_430_algorithmic.json`
- `geo_integration/core_colleges_college_info_allotement_430_algorithmic_summary.json`
- `geo_integration/active/v4go_intermediate/college_names_only_core_430_algorithmic_aligned.json`
- `geo_integration/active/v4go_intermediate/college_names_only_core_430_algorithmic_unresolved.json`

## Next integration target

The best next engineering step is to connect:
- `College_Info_Done/output.json`
- cleaned district signals
- resolved lat/lng outputs

into one normalized college location reference layer built for extraction accuracy, validation, and downstream ranking joins.
