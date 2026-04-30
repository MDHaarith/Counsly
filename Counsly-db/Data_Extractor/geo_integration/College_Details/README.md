# College_Details

Current active implementation was moved to the project root:

- [v4-go](/home/mdhaarith/Desktop/Projects/Data_Extractor/v4-go)
- [v4-ui](/home/mdhaarith/Desktop/Projects/Data_Extractor/v4-ui)
- [archive/v4go_intermediate](/home/mdhaarith/Desktop/Projects/Data_Extractor/archive/v4go_intermediate)

## What it does

This project resolves Tamil Nadu college coordinates from Google Maps search results. The active pipeline:

- generates multiple query variants per college
- runs `gosom/google-maps-scraper`
- scores returned candidates to reject wrong sibling institutions
- reuses manual overrides and cached hits
- falls back to parent-campus coordinates for sub-campus cases
- writes clean and unresolved outputs under `/home/mdhaarith/Desktop/Projects/Data_Extractor/archive/v4go_intermediate/`

## Active layout

- `/home/mdhaarith/Desktop/Projects/Data_Extractor/v4-go/` — active Go extractor and local config
- `/home/mdhaarith/Desktop/Projects/Data_Extractor/v4-go/config/` — normalization rules, manual overrides, parent-campus mappings, place cache
- `/home/mdhaarith/Desktop/Projects/Data_Extractor/v4-ui/` — minimal UI that triggers `v4-go`
- `/home/mdhaarith/Desktop/Projects/Data_Extractor/archive/v4go_intermediate/` — current generated outputs
- `archive/` — preserved historical outputs and experiments

## Common commands

Run the active pipeline:

```bash
cd /home/mdhaarith/Desktop/Projects/Data_Extractor/v4-go
go run ./cmd/runner --input ./college_names_only.json --provider=gosom --timeout=600
```

Run tests:

```bash
cd /home/mdhaarith/Desktop/Projects/Data_Extractor/v4-go
go test ./...
```

Run the UI:

```bash
cd /home/mdhaarith/Desktop/Projects/Data_Extractor/v4-ui
npm run dev
```
