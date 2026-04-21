import joblib
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from backend.config import MODEL_PATH, FINGERPRINT_PATH

loaded = joblib.load(MODEL_PATH)

if isinstance(loaded, dict):
    if "model" not in loaded:
        raise ValueError("Loaded joblib dict does not contain 'model' key")

    model = loaded["model"]

    # FIX: Load label_encoder from bundle so we can decode predictions correctly.
    # Pipeline.classes_ returns encoded integers (0,1,2...), NOT room names.
    if "label_encoder" in loaded:
        label_encoder = loaded["label_encoder"]
    else:
        # Fallback: rebuild from fingerprint CSV if old model bundle lacks label_encoder
        fingerprint_df = pd.read_csv(FINGERPRINT_PATH)
        label_encoder = LabelEncoder()
        label_encoder.fit(fingerprint_df["Location"].unique())

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
    label_encoder = LabelEncoder()
    label_encoder.fit(fingerprint_df["Location"].unique())

fingerprint_df = pd.read_csv(FINGERPRINT_PATH)
if "Location" not in fingerprint_df.columns:
    raise ValueError("fingerprint_reference.csv must contain 'Location' column")

print("Loaded model object type:", type(loaded))
if isinstance(loaded, dict):
    print("Loaded keys:", list(loaded.keys()))
print("Actual model type:", type(model))
print("Feature count:", len(feature_columns))
print("Classes:", list(label_encoder.classes_))