import json
from pathlib import Path

import pandas as pd

from backend.config import FINGERPRINT_PATH, REFERENCE_FINGERPRINT_PATH


def _load_json_reference(path: Path):
    with path.open('r', encoding='utf-8') as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError('reference_fingerprints.json must contain a list of fingerprints')

    normalized = []
    for row in data:
        normalized.append({
            'location': str(row['location']),
            'sequence_number': int(row.get('sequence_number', -1)),
            'signals': {str(k).upper().strip(): float(v) for k, v in row['signals'].items()},
        })
    return normalized


def _build_reference_from_csv(path: Path):
    df = pd.read_csv(path)
    if 'Location' not in df.columns:
        raise ValueError("fingerprint_reference.csv must contain 'Location' column")

    feature_columns = [c for c in df.columns if c != 'Location']
    reference = []
    for idx, row in df.iterrows():
        signals = {
            str(mac).upper().strip(): float(row[mac])
            for mac in feature_columns
            if pd.notna(row[mac]) and float(row[mac]) > -100
        }
        reference.append({
            'location': str(row['Location']),
            'sequence_number': int(idx),
            'signals': signals,
        })
    return reference


ref_json_path = Path(REFERENCE_FINGERPRINT_PATH)
ref_csv_path = Path(FINGERPRINT_PATH)

if ref_json_path.exists():
    reference_fingerprints = _load_json_reference(ref_json_path)
elif ref_csv_path.exists():
    reference_fingerprints = _build_reference_from_csv(ref_csv_path)
else:
    raise FileNotFoundError(
        f'No reference fingerprint file found at {ref_json_path} or {ref_csv_path}'
    )

print(f'Loaded {len(reference_fingerprints)} reference fingerprints')
