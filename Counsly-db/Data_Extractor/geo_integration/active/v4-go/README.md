# v4-go

Current active college coordinate extractor. Uses gosom/google-maps-scraper plus local scoring, filtering, and fallback logic to maximize raw resolution accuracy instead of flattening nearby duplicates.

## How it works (current state)
- **Input**: JSON list (e.g., `college_names_only.json`). For each item, we pull `query|title|name|college|institution` plus location hints (`city,district,state,country,address,location,pincode`).
- **Normalize**: Apply abbreviation/alias/stopword cleanup from `config/query_normalization.json` and join location parts.
- **Resolve one college at a time**: Build several query variants for each college instead of flattening one global gosom run.
- **Attach reference metadata**: Load `/home/mdhaarith/Desktop/Projects/Data_Extractor/College_Info/output.json` when available and match each input college to the extracted TNEA record.
- **Scrape**: Shells out to `gosom/google-maps-scraper` Docker image with `-json`, collecting one candidate cluster per college.
- **Score candidates**: Rank results using multiple signals:
  - normalized title overlap
  - exact normalized-name match bonus
  - city/district/taluk/pincode and locality overlap
  - reference address, district, taluk, pincode, and website-host matches from `College_Info/output.json`
  - institution-type penalties (`engineering` vs `polytechnic`, `architecture`, `women`, `nursing`, `arts and science`, etc.)
  - Tamil Nadu / India bounds checks
- **Fallbacks**: Reuse exact hits from `config/manual_overrides.json` and `config/place_cache.json`, then try `config/parent_campuses.json` for sub-campus cases.
- **Output**: Writes `*_clean_output.json` and `*_clean_output_unresolved.json` to `../archive/v4go_intermediate/`. Unresolved records include the top candidate summaries and match reasons when available.

## Prerequisites
- Go toolchain.
- Docker access (able to run `docker run gosom/google-maps-scraper`). If Docker requires root, run with appropriate permissions or add the user to the docker group.

## Usage (once Go is installed and Docker works)
```bash
cd /home/mdhaarith/Desktop/Projects/Data_Extractor/v4-go
# Run directly
go run ./cmd/runner \
  --input ./college_names_only.json \
  --provider=gosom \
  --reference /home/mdhaarith/Desktop/Projects/Data_Extractor/College_Info/output.json \
  --extra="--depth 3" \
  --timeout=600

# Or build
go build -o ./bin/runner ./cmd/runner
./bin/runner --input ./college_names_only.json --provider=gosom
```

Flags:
- `--input`: path to input JSON.
- `--provider`: currently `gosom` only.
- `--config-dir`: defaults to `./config`.
- `--out-dir`: defaults to `../archive/v4go_intermediate` under the project root.
- `--reference`: defaults to `College_Info/output.json` when that file is discoverable; used for extra address/pincode/website signals.
- `--extra`: comma-separated extra args passed to gosom (e.g., `--depth 5,--proxies http://user:pass@host:port`).
- `--timeout`: per-item seconds before killing the provider run.
- `--min-score`: minimum score required to accept a candidate.
- `--min-margin`: minimum score gap over the next-best candidate.
- `--max-variants`: maximum query variants to try per college.

Outputs:
- `../archive/v4go_intermediate/<basename>_clean_output.json`
- `../archive/v4go_intermediate/<basename>_clean_output_unresolved.json`

## Accuracy priorities
- maximize correct college matching over convenience
- reject sibling or wrong-type institutions aggressively
- use district, locality, pincode, and reference metadata as ranking signals
- preserve unresolved cases instead of forcing weak matches
- treat imported cache hits as provisional unless they survive review or re-resolution

## Known gaps / TODO
- Add a second-pass reviewer equivalent to the Python browser flow for stubborn unresolved colleges.
- Add a review path for suspicious cache entries so stale cache data does not masquerade as algorithmic success.
- Tune default timeouts/concurrency for large full-dataset runs.
- Expand tests with archived raw gosom fixtures.

## If Docker permission denied
You may see: `permission denied while trying to connect to the Docker daemon socket`. Fix by granting docker access (e.g., add user to `docker` group and re-login) or run with sudo (if permitted). Without Docker access, the gosom provider cannot run.
