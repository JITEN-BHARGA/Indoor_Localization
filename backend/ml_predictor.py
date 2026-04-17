import numpy as np
from backend.model_loader import model, feature_columns


def get_model_classes():
    if hasattr(model, "classes_"):
        return model.classes_

    if hasattr(model, "named_steps"):
        last_step = list(model.named_steps.values())[-1]
        if hasattr(last_step, "classes_"):
            return last_step.classes_

    raise AttributeError("Could not find classes_ on loaded model")


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


def predict_with_ml(payload: dict):
    x = build_feature_vector(payload["scan_data"])
    probs = model.predict_proba([x])[0]
    classes = get_model_classes()

    pred_index = int(np.argmax(probs))
    pred_label = str(classes[pred_index])
    confidence = float(probs[pred_index])

    sorted_idx = np.argsort(probs)[::-1][:3]
    top_k = [
        {"location": str(classes[idx]), "score": float(probs[idx])}
        for idx in sorted_idx
    ]

    return {
        "predicted_location": pred_label,
        "confidence": confidence,
        "top_k": top_k
    }