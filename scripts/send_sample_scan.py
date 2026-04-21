import json
import os
from datetime import datetime, timezone
import httpx

API_BASE = os.getenv('API_BASE', 'http://127.0.0.1:8000')
API_TOKEN = os.getenv('API_TOKEN', '')

payload = {
    'object_id': 'bag_01',
    'device_id': 'esp32_01',
    'timestamp': datetime.now(timezone.utc).isoformat(),
    'scan_data': [
        {'mac_address': 'AA:BB:CC:DD:EE:01', 'rssi': -65},
        {'mac_address': 'AA:BB:CC:DD:EE:02', 'rssi': -74},
        {'mac_address': 'AA:BB:CC:DD:EE:03', 'rssi': -82},
    ],
}

headers = {'Content-Type': 'application/json'}
if API_TOKEN:
    headers['x-api-token'] = API_TOKEN

resp = httpx.post(f'{API_BASE}/api/ingest', json=payload, headers=headers, timeout=30.0)
print(resp.status_code)
print(resp.text)
