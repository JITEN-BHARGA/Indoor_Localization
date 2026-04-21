from backend.config import LOW_CONFIDENCE_THRESHOLD
from backend.ml_predictor import predict_with_ml
from backend.similarity_matcher import predict_with_knn_similarity


def hybrid_predict(payload: dict):
    ml_result = predict_with_ml(payload)
    knn_result = predict_with_knn_similarity(payload, k=3)

    ml_prediction = ml_result['predicted_location']
    knn_prediction = knn_result['predicted_location']
    ml_confidence = float(ml_result['confidence'])
    knn_confidence = float(knn_result.get('confidence', 0.0))

    if ml_confidence >= LOW_CONFIDENCE_THRESHOLD:
        final_prediction = ml_prediction
        final_method = 'ml_model'
        final_confidence = ml_confidence
    elif knn_prediction != 'Unknown':
        final_prediction = knn_prediction
        final_method = 'knn_similarity'
        final_confidence = knn_confidence
    else:
        final_prediction = ml_prediction
        final_method = 'ml_low_confidence'
        final_confidence = ml_confidence

    return {
        'object_id': payload['object_id'],
        'device_id': payload.get('device_id'),
        'final_prediction': final_prediction,
        'final_method': final_method,
        'final_confidence': final_confidence,
        'agreement': ml_prediction == knn_prediction and knn_prediction != 'Unknown',
        'ml_result': ml_result,
        'knn_result': knn_result,
    }
