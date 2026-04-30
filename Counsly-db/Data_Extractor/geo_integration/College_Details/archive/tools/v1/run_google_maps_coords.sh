#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [[ -d "$SCRIPT_DIR/../../archive" || "$SCRIPT_DIR" == *"/College_Details/archive/tools" ]]; then
  ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
else
  ROOT_DIR="/home/mdhaarith/Desktop/Data_Extractor/processed/College_Details"
fi
ARCHIVE_DIR="$ROOT_DIR/archive"
SOURCE_DIR="$ARCHIVE_DIR/source"
INTERMEDIATE_DIR="$ARCHIVE_DIR/intermediate"

mkdir -p "$INTERMEDIATE_DIR"

VENV_PY="/home/mdhaarith/.openclaw/workspace/venv/bin/python"
GEOCODER="$SCRIPT_DIR/google_maps_coords.py"
VALIDATOR="$SCRIPT_DIR/validate_google_maps_coords.py"
REVIEWER="$SCRIPT_DIR/final_review_google_maps_coords.py"

INPUT_ARG="${1:-college_names_only.json}"
shift || true
EXTRA_ARGS=("$@")

resolve_input() {
  local candidate="$1"
  if [[ -f "$candidate" ]]; then
    realpath "$candidate"
    return 0
  fi
  if [[ -f "$SOURCE_DIR/$candidate" ]]; then
    realpath "$SOURCE_DIR/$candidate"
    return 0
  fi
  if [[ -f "$ROOT_DIR/$candidate" ]]; then
    realpath "$ROOT_DIR/$candidate"
    return 0
  fi
  return 1
}

if ! INPUT="$(resolve_input "$INPUT_ARG")"; then
  echo "Input not found: $INPUT_ARG" >&2
  exit 1
fi

if [[ "${INPUT##*.}" != "json" ]]; then
  echo "This full pipeline currently expects a JSON input file." >&2
  exit 1
fi

BASE_NAME="$(basename "${INPUT%.*}")"
GEOCODED_JSON="$INTERMEDIATE_DIR/${BASE_NAME}_with_coordinates.json"
GEOCODED_LINES="$INTERMEDIATE_DIR/${BASE_NAME}_coords_lines.txt"
GEOCODED_FAILED="$INTERMEDIATE_DIR/${BASE_NAME}_failed.txt"
FINAL_JSON="$INTERMEDIATE_DIR/${BASE_NAME}_with_coordinates_final_cleaned.json"
FINAL_UNRESOLVED="$INTERMEDIATE_DIR/${BASE_NAME}_with_coordinates_final_unresolved.json"
FINAL_VALIDATION_TARGET="$INTERMEDIATE_DIR/${BASE_NAME}_with_coordinates_final_cleaned.json"

export PYTHONUNBUFFERED=1

echo "==> Extracting coordinates from Google Maps"
"$VENV_PY" "$GEOCODER" "$INPUT" \
  --headless \
  --delay-seconds 0.75 \
  --output "$GEOCODED_JSON" \
  --line-output "$GEOCODED_LINES" \
  --failed-output "$GEOCODED_FAILED" \
  "${EXTRA_ARGS[@]}"

echo
echo "==> Validating raw extraction"
"$VENV_PY" "$VALIDATOR" "$GEOCODED_JSON" --autofix-url-place

echo
echo "==> Running second-pass reviewer"
"$VENV_PY" "$REVIEWER" "$GEOCODED_JSON" --headless

echo
echo "==> Validating final cleaned output"
"$VENV_PY" "$VALIDATOR" "$FINAL_VALIDATION_TARGET"

TARGET_CLEAN_JSON="$ROOT_DIR/${BASE_NAME}_clean_output.json"
TARGET_UNRESOLVED_JSON="$ROOT_DIR/${BASE_NAME}_clean_output_unresolved.json"

echo
echo "==> Refreshing clean outputs"
cp -f "$FINAL_JSON" "$TARGET_CLEAN_JSON"
cp -f "$FINAL_UNRESOLVED" "$TARGET_UNRESOLVED_JSON"

if [[ "$BASE_NAME" == "college_names_only" ]]; then
  cp -f "$FINAL_JSON" "$ROOT_DIR/clean_output.json"
  cp -f "$FINAL_UNRESOLVED" "$ROOT_DIR/clean_output_unresolved.json"
fi

echo
echo "Done."
echo "Clean output:      $TARGET_CLEAN_JSON"
echo "Unresolved output: $TARGET_UNRESOLVED_JSON"
echo "Intermediate dir:  $INTERMEDIATE_DIR"
