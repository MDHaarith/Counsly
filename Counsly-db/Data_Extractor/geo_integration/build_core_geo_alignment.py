#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
COLLEGE_INFO_PATH = ROOT / 'College_Info_Done/output_present_non_architecture.json'
ALLOTEMENT_PATH = ROOT / 'Allotement/data/rankings/college_rankings.csv'
GEO_CLEAN_PATH = ROOT / 'geo_integration/active/v4go_intermediate/college_names_only_clean_output.json'
OUT_DIR = ROOT / 'geo_integration'
V4GO_DIR = ROOT / 'geo_integration/active/v4-go'
INTERMEDIATE_DIR = ROOT / 'geo_integration/active/v4go_intermediate'

STOPWORDS = {
    'autonomous', 'district', 'post', 'road', 'taluk', 'via', 'campus', 'college',
    'of', 'and', 'the', 'at', 'near'
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def squash_ws(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


def normalize_text(text: str) -> str:
    text = text.lower()
    text = text.replace('&', ' and ')
    text = text.replace('(', ' ').replace(')', ' ')
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    tokens = [tok for tok in text.split() if tok and tok not in STOPWORDS]
    return ' '.join(tokens)


def token_signature(text: str) -> tuple[str, ...]:
    return tuple(sorted(set(normalize_text(text).split())))


def looks_corrupted(name: str) -> bool:
    markers = [
        'government colleges',
        'government aided colleges',
        'self financing engineering colleges',
        'list of colleges',
        'list of college code and its branches',
    ]
    lowered = name.lower()
    return len(name) > 300 or any(marker in lowered for marker in markers)


def build_core430() -> list[dict[str, Any]]:
    college_info = load_json(COLLEGE_INFO_PATH)
    rankings = pd.read_csv(ALLOTEMENT_PATH)
    allotment_codes = {str(int(v)).strip() for v in rankings['college_code'].dropna().tolist()}

    rows = []
    for row in college_info:
        code = str(row.get('College_Code', '')).strip()
        if not code or code not in allotment_codes:
            continue
        name = squash_ws(str(row.get('College_Name', '')))
        rows.append({
            'College_Code': code,
            'College_Name': name,
            'District': squash_ws(str(row.get('District', ''))),
            'normalized_name': normalize_text(name),
            'token_signature': list(token_signature(name)),
            'is_corrupted_name': looks_corrupted(name),
            'raw_record': row,
        })
    return rows


def build_geo_alignment(core_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    geo_rows = load_json(GEO_CLEAN_PATH)
    exact = {squash_ws(str(row.get('original', ''))): row for row in geo_rows}
    normalized = {}
    tokenized = {}
    for row in geo_rows:
        original = squash_ws(str(row.get('original', '')))
        normalized.setdefault(normalize_text(original), []).append(row)
        tokenized.setdefault(token_signature(original), []).append(row)

    aligned = []
    unresolved = []
    for row in core_rows:
        name = row['College_Name']
        match = None
        match_method = None

        if name in exact:
            match = exact[name]
            match_method = 'exact'
        else:
            norm = row['normalized_name']
            norm_candidates = normalized.get(norm, [])
            if len(norm_candidates) == 1:
                match = norm_candidates[0]
                match_method = 'normalized'
            else:
                sig = tuple(row['token_signature'])
                sig_candidates = tokenized.get(sig, [])
                if len(sig_candidates) == 1:
                    match = sig_candidates[0]
                    match_method = 'token_signature'

        record = {
            'college_code': row['College_Code'],
            'college_name': name,
            'district': row['District'],
            'normalized_name': row['normalized_name'],
            'is_corrupted_name': row['is_corrupted_name'],
        }
        if match is not None:
            record['geo_match_method'] = match_method
            record['geo_original'] = match.get('original')
            record['latitude'] = match.get('latitude')
            record['longitude'] = match.get('longitude')
            record['source'] = match.get('source')
            record['note'] = match.get('note')
            aligned.append(record)
        else:
            unresolved.append(record)

    return aligned, unresolved


def main() -> int:
    core_rows = build_core430()
    aligned, unresolved = build_geo_alignment(core_rows)

    write_json(OUT_DIR / 'core_colleges_college_info_allotement_430_algorithmic.json', core_rows)
    write_json(V4GO_DIR / 'college_names_only_core_430_algorithmic.json', [row['College_Name'] for row in core_rows])
    write_json(INTERMEDIATE_DIR / 'college_names_only_core_430_algorithmic_aligned.json', aligned)
    write_json(INTERMEDIATE_DIR / 'college_names_only_core_430_algorithmic_unresolved.json', unresolved)

    summary = {
        'core_count': len(core_rows),
        'aligned_count': len(aligned),
        'unresolved_count': len(unresolved),
        'corrupted_core_names': [row['college_name'] for row in unresolved if row['is_corrupted_name']],
        'match_method_counts': pd.Series([row['geo_match_method'] for row in aligned]).value_counts().to_dict() if aligned else {},
    }
    write_json(OUT_DIR / 'core_colleges_college_info_allotement_430_algorithmic_summary.json', summary)
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
