import numpy as np
from backend.config import LOW_CONFIDENCE_THRESHOLD
from backend.model_loader import model, feature_columns
from backend.similarity import cosine_fallback

def build_feature_vector(scan_data):
    x = np.full(len(feature_columns), -100.0, dtype=float)

    incoming = {}
    for item in scan_data:
        mac = item["mac_address"].upper().strip()
        incoming[mac] = item["rssi"]

    for i, mac in enumerate(feature_columns):
        if mac in incoming:
            x[i] = incoming[mac]

    return x

def predict_location(payload: dict):
    x = build_feature_vector(payload["scan_data"])

    probs = model.predict_proba([x])[0]
    pred_index = int(np.argmax(probs))
    pred_label = model.classes_[pred_index]
    confidence = float(probs[pred_index])

    sorted_idx = np.argsort(probs)[::-1][:3]
    top_k = [
        {"location": str(model.classes_[idx]), "score": float(probs[idx])}
        for idx in sorted_idx
    ]

    if confidence < LOW_CONFIDENCE_THRESHOLD:
        fallback = cosine_fallback(x)
        return {
            "object_id": payload["object_id"],
            "predicted_location": fallback["predicted_location"],
            "confidence": fallback["confidence"],
            "method": fallback["method"],
            "top_k": top_k,
        }

    return {
        "object_id": payload["object_id"],
        "predicted_location": str(pred_label),
        "confidence": confidence,
        "method": "ml_model",
        "top_k": top_k,
    }