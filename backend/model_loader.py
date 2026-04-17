import joblib
import pandas as pd
from backend.config import MODEL_PATH, FINGERPRINT_PATH

loaded = joblib.load(MODEL_PATH)

if isinstance(loaded, dict):
    if "model" not in loaded:
        raise ValueError("Loaded joblib dict does not contain 'model' key")

    model = loaded["model"]

    if "feature_columns" in loaded and loaded["feature_columns"]:
        feature_columns = list(loaded["feature_columns"])
    else:
        fingerprint_df = pd.read_csv(FINGERPRINT_PATH)
        if "Location" not in fingerprint_df.columns:
            raise ValueError("fingerprint_reference.csv must contain 'Location' column")
        feature_columns = [c for c in fingerprint_df.columns if c != "Location"]
else:
    model = loaded
    fingerprint_df = pd.read_csv(FINGERPRINT_PATH)
    if "Location" not in fingerprint_df.columns:
        raise ValueError("fingerprint_reference.csv must contain 'Location' column")
    feature_columns = [c for c in fingerprint_df.columns if c != "Location"]

fingerprint_df = pd.read_csv(FINGERPRINT_PATH)
if "Location" not in fingerprint_df.columns:
    raise ValueError("fingerprint_reference.csv must contain 'Location' column")

print("Loaded model object type:", type(loaded))
if isinstance(loaded, dict):
    print("Loaded keys:", loaded.keys())
print("Actual model type:", type(model))
print("Feature count:", len(feature_columns))