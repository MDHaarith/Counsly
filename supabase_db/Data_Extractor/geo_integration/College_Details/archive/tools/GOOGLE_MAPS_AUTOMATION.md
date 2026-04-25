# Google Maps coordinate automation

This folder now contains a browser-only coordinate extractor.

## Run

```bash
cd /home/mdhaarith/Desktop/Data_Extractor/processed/College_Details
./run_google_maps_coords.sh
```

Or directly:

```bash
/home/mdhaarith/.openclaw/workspace/venv/bin/python google_maps_coords.py college_names_only.json --headless --delay-seconds 0.75
```

## Outputs

- `college_names_only_with_coordinates.json`
- `college_names_only_coords_lines.txt`
- `college_names_only_failed.txt`
- `college_names_only_run.log`

## Validator

Validate the extracted coordinates:

```bash
cd /home/mdhaarith/Desktop/Data_Extractor/processed/College_Details
/home/mdhaarith/.openclaw/workspace/venv/bin/python validate_google_maps_coords.py college_names_only_with_coordinates.json
```

Optional: also write a URL-corrected JSON using canonical place coordinates embedded in the Google Maps URL:

```bash
/home/mdhaarith/.openclaw/workspace/venv/bin/python validate_google_maps_coords.py college_names_only_with_coordinates.json --autofix-url-place
```

Validator outputs:

- `college_names_only_with_coordinates_validation_report.json`
- `college_names_only_with_coordinates_validation_summary.txt`
- `college_names_only_with_coordinates_suspect_coordinates.json`
- `college_names_only_with_coordinates_url_fixed.json` (only with `--autofix-url-place`)

## Plain line format

Each successful line is written as:

```text
College Name,12.345678,78.901234,
```

If a college cannot be resolved, the lines file uses:

```text
College Name,NOT_FOUND,NOT_FOUND,
```
