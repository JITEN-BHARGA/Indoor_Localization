from typing import List
from pydantic import BaseModel


class ScanItem(BaseModel):
    mac_address: str
    rssi: int


class IngestPayload(BaseModel):
    object_id: str
    device_id: str
    scan_data: List[ScanItem]