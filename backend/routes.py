from fastapi import APIRouter
from backend.schemas import IngestPayload
from backend.hybrid_predictor import hybrid_predict
from backend.db import save_raw_scan, save_prediction, get_latest_prediction

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/api/ingest")
def ingest(payload: IngestPayload):
    data = payload.model_dump()

    save_raw_scan(
        object_id=data["object_id"],
        device_id=data["device_id"],
        payload=data,
    )

    result = hybrid_predict(data)
    save_prediction(result)

    return result


@router.get("/latest")
def latest():
    row = get_latest_prediction()
    if not row:
        return {
            "object_id": "N/A",
            "final_prediction": "No prediction yet",
            "final_method": "none",
            "ml_result": {},
            "knn_result": {},
        }
    return row