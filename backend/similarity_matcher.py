from collections import defaultdict
from typing import Dict, List
from backend.config import MIN_COMMON_MACS
from backend.reference_loader import reference_fingerprints


def normalize_live_scan(scan_data: List[dict]) -> Dict[str, float]:
    signals = {}
    for item in scan_data:
        mac = item["mac_address"].strip().upper()
        rssi = float(item["rssi"])
        signals[mac] = rssi
    return signals


def compare_with_sequence(live_signals: Dict[str, float], ref_signals: Dict[str, float]):
    common_macs = set(live_signals.keys()) & set(ref_signals.keys())

    if len(common_macs) < MIN_COMMON_MACS:
        return None

    diffs = []
    for mac in common_macs:
        diffs.append(abs(live_signals[mac] - ref_signals[mac]))

    avg_diff = sum(diffs) / len(diffs)
    similarity_score = 1.0 / (1.0 + avg_diff)

    return {
        "similarity_score": similarity_score,
        "common_mac_count": len(common_macs),
        "avg_rssi_difference": avg_diff,
        "matched_macs": sorted(list(common_macs)),
    }


def predict_with_knn_similarity(payload: dict, k: int = 3):
    live_signals = normalize_live_scan(payload["scan_data"])

    all_matches = []

    for ref in reference_fingerprints:
        result = compare_with_sequence(live_signals, ref["signals"])
        if result is None:
            continue

        all_matches.append({
            "location": ref["location"],
            "sequence_number": ref["sequence_number"],
            "similarity_score": result["similarity_score"],
            "common_mac_count": result["common_mac_count"],
            "avg_rssi_difference": result["avg_rssi_difference"],
            "matched_macs": result["matched_macs"],
        })

    if not all_matches:
        return {
            "predicted_location": "Unknown",
            "k": k,
            "top_matches": [],
            "weighted_scores": {}
        }

    all_matches = sorted(all_matches, key=lambda x: x["similarity_score"], reverse=True)
    top_k = all_matches[:k]

    weighted_scores = defaultdict(float)
    for item in top_k:
        weighted_scores[item["location"]] += item["similarity_score"]

    predicted_location = max(weighted_scores, key=weighted_scores.get)

    return {
        "predicted_location": predicted_location,
        "k": k,
        "top_matches": top_k,
        "weighted_scores": dict(weighted_scores)
    }