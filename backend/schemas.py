from typing import List, Optional
from pydantic import BaseModel, Field


class ScanItem(BaseModel):
    mac_address: str
    rssi: int


class IngestPayload(BaseModel):
    object_id: str
    device_id: str
    scan_data: List[ScanItem]
    request_id: Optional[str] = None


class ObjectCreate(BaseModel):
    object_id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    description: Optional[str] = None


class ObjectResponse(BaseModel):
    object_id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[str] = None


class EspDeviceCreate(BaseModel):
    device_id: str = Field(..., min_length=1)
    device_name: str = Field(..., min_length=1)
    is_active: bool = True


class EspDeviceResponse(BaseModel):
    device_id: str
    device_name: str
    is_active: bool
    last_seen_at: Optional[str] = None


class TriggerScanRequest(BaseModel):
    object_id: str
    device_ids: List[str]


class ScanRequestResponse(BaseModel):
    request_id: str
    object_id: str
    status: str
    requested_at: Optional[str] = None
    completed_at: Optional[str] = None
    expected_device_count: int = 0
    received_device_count: int = 0
    device_statuses: List[dict] = []