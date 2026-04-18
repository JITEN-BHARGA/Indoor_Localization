from fastapi import APIRouter, HTTPException
from backend.schemas import (
    IngestPayload,
    ObjectCreate,
    EspDeviceCreate,
    TriggerScanRequest,
)
from backend.hybrid_predictor import hybrid_predict
from backend.db import (
    create_object,
    list_objects,
    get_object,
    upsert_esp_device,
    list_esp_devices,
    get_esp_devices_by_ids,
    create_scan_request,
    mark_scan_request_collecting,
    save_raw_scan,
    save_prediction,
    get_latest_prediction,
    get_latest_prediction_for_object,
    get_scan_request_status,
    get_prediction_by_request,
)
from backend.mqtt_consumer import publish_scan_command, is_mqtt_ready

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/objects")
def create_object_route(payload: ObjectCreate):
    create_object(
        object_id=payload.object_id,
        name=payload.name,
        description=payload.description,
    )
    return {"message": "Object saved successfully"}


@router.get("/objects")
def list_objects_route():
    return list_objects()


@router.get("/objects/{object_id}")
def get_object_route(object_id: str):
    obj = get_object(object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    return obj


@router.get("/objects/{object_id}/latest")
def get_object_latest_route(object_id: str):
    row = get_latest_prediction_for_object(object_id)
    if not row:
        return {
            "object_id": object_id,
            "final_prediction": "No prediction yet",
            "final_method": "none",
            "ml_result": {},
            "knn_result": {},
        }
    return row


@router.post("/esp-devices")
def create_esp_device_route(payload: EspDeviceCreate):
    upsert_esp_device(
        device_id=payload.device_id,
        device_name=payload.device_name,
        is_active=payload.is_active,
    )
    return {"message": "ESP device saved successfully"}


@router.get("/esp-devices")
def list_esp_devices_route():
    return list_esp_devices()


@router.post("/scan")
def trigger_scan_route(payload: TriggerScanRequest):
    obj = get_object(payload.object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")

    if not payload.device_ids:
        raise HTTPException(status_code=400, detail="At least one ESP device must be selected")

    devices = get_esp_devices_by_ids(payload.device_ids)
    if len(devices) != len(payload.device_ids):
        raise HTTPException(status_code=400, detail="One or more selected ESP devices do not exist")

    inactive = [d["device_id"] for d in devices if not d["is_active"]]
    if inactive:
        raise HTTPException(status_code=400, detail=f"Inactive ESP devices selected: {inactive}")

    if not is_mqtt_ready():
        raise HTTPException(
            status_code=503,
            detail="Backend MQTT broker se connected nahi hai"
        )

    request_id = create_scan_request(
        object_id=payload.object_id,
        device_ids=payload.device_ids,
    )

    for device_id in payload.device_ids:
        publish_scan_command(
            device_id=device_id,
            request_id=request_id,
            object_id=payload.object_id,
        )

    mark_scan_request_collecting(request_id)

    return {
        "request_id": request_id,
        "object_id": payload.object_id,
        "status": "collecting",
    }


@router.get("/scan-requests/{request_id}")
def get_scan_request_route(request_id: str):
    row = get_scan_request_status(request_id)
    if not row:
        raise HTTPException(status_code=404, detail="Scan request not found")
    return row


@router.get("/scan-requests/{request_id}/result")
def get_scan_result_route(request_id: str):
    row = get_prediction_by_request(request_id)
    if not row:
        return {
            "request_id": request_id,
            "status": "pending",
            "result": None,
        }
    return {
        "request_id": request_id,
        "status": "completed",
        "result": row,
    }


# Legacy direct ingest route - useful for testing without MQTT
@router.post("/api/ingest")
def ingest(payload: IngestPayload):
    data = payload.model_dump()

    save_raw_scan(
        request_id=data.get("request_id"),
        object_id=data["object_id"],
        device_id=data["device_id"],
        payload=data,
    )

    result = hybrid_predict(data)
    save_prediction(result, request_id=data.get("request_id"))

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