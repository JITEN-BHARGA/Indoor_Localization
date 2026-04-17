from backend.ml_predictor import predict_with_ml
from backend.similarity_matcher import predict_with_knn_similarity
from backend.config import LOW_CONFIDENCE_THRESHOLD


def hybrid_predict(payload: dict):
    ml_result = predict_with_ml(payload)
    knn_result = predict_with_knn_similarity(payload, k=3)

    if ml_result["confidence"] >= LOW_CONFIDENCE_THRESHOLD:
        final_prediction = ml_result["predicted_location"]
        final_method = "ml_model"
    else:
        final_prediction = knn_result["predicted_location"]
        final_method = "knn_similarity"

    return {
        "object_id": payload["object_id"],
        "final_prediction": final_prediction,
        "final_method": final_method,
        "ml_result": ml_result,
        "knn_result": knn_result
    }