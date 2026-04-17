import json
from backend.config import REFERENCE_FINGERPRINT_PATH

with open(REFERENCE_FINGERPRINT_PATH, "r", encoding="utf-8") as f:
    reference_fingerprints = json.load(f)

print(f"Loaded {len(reference_fingerprints)} reference fingerprints")