import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from backend.model_loader import fingerprint_df, feature_columns

def cosine_fallback(x_vector):
    reference = fingerprint_df[feature_columns].values
    sims = cosine_similarity([x_vector], reference)[0]
    idx = int(np.argmax(sims))

    return {
        "predicted_location": str(fingerprint_df.iloc[idx]["Location"]),
        "confidence": float(sims[idx]),
        "method": "cosine_similarity"
    }