from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.db import (
    get_esp_devices,
    create_scan_request,
    mark_scan_request_collecting,
    get_scan_request,
    get_prediction,
    create_esp_device,
)
from backend.mqtt_consumer import publish_scan_command, is_mqtt_ready
from backend.schemas import CreateEspDeviceBody

router = APIRouter()


class ScanRequestBody(BaseModel):
    device_id: str


@router.get("/esp-devices")
def list_esp_devices():
    return get_esp_devices()


@router.post("/scan")
def trigger_scan(body: ScanRequestBody):
    device_id = body.device_id.strip()

    devices = get_esp_devices()
    valid_ids = {d["device_id"] for d in devices}

    if device_id not in valid_ids:
        raise HTTPException(status_code=404, detail="Device not found")

    if not is_mqtt_ready():
        raise HTTPException(status_code=503, detail="MQTT not connected")

    request_id = create_scan_request(device_id)

    publish_scan_command(
        device_id=device_id,
        request_id=request_id,
        object_id=device_id
    )

    mark_scan_request_collecting(request_id)

    return {
        "request_id": request_id,
        "status": "collecting",
    }


@router.get("/scan-requests/{request_id}")
def scan_status(request_id: str):
    data = get_scan_request(request_id)
    if not data:
        raise HTTPException(404, "Not found")
    return data


@router.get("/scan-requests/{request_id}/result")
def scan_result(request_id: str):
    result = get_prediction(request_id)
    return {
        "request_id": request_id,
        "result": result,
    }

@router.post("/esp-devices")
def create_esp_device_route(body: CreateEspDeviceBody):
    create_esp_device(
        device_id=body.device_id.strip(),
        device_name=body.device_name.strip(),
        is_active=body.is_active,
    )
    return {"message": "ESP device created successfully", "device_id": body.device_id}