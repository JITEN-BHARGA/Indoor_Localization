import json
import os
import uuid

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ValueError('DATABASE_URL not found in environment')

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
)


def get_esp_devices():
    with engine.connect() as conn:
        result = conn.execute(text('SELECT * FROM esp_devices ORDER BY device_id'))
        return [dict(row._mapping) for row in result]


def create_scan_request(device_id: str, object_id: str | None = None):
    request_id = str(uuid.uuid4())
    object_id = object_id or device_id

    with engine.begin() as conn:
        conn.execute(
            text('''
                INSERT INTO scan_requests (request_id, object_id, device_id, status)
                VALUES (:request_id, :object_id, :device_id, 'pending')
            '''),
            {
                'request_id': request_id,
                'object_id': object_id,
                'device_id': device_id,
            },
        )

    return request_id


def mark_scan_request_collecting(request_id: str):
    with engine.begin() as conn:
        conn.execute(
            text('''
                UPDATE scan_requests
                SET status = 'collecting'
                WHERE request_id = :request_id
            '''),
            {'request_id': request_id},
        )


def complete_scan_request(request_id: str):
    with engine.begin() as conn:
        conn.execute(
            text('''
                UPDATE scan_requests
                SET status = 'completed', completed_at = NOW()
                WHERE request_id = :request_id
            '''),
            {'request_id': request_id},
        )


def get_scan_request(request_id: str):
    with engine.connect() as conn:
        result = conn.execute(
            text('SELECT * FROM scan_requests WHERE request_id = :id'),
            {'id': request_id},
        ).fetchone()
        return dict(result._mapping) if result else None


def save_raw_scan(request_id: str | None, object_id: str, device_id: str, payload: dict):
    with engine.begin() as conn:
        conn.execute(
            text('''
                INSERT INTO raw_scans (request_id, object_id, device_id, payload)
                VALUES (:request_id, :object_id, :device_id, CAST(:payload AS JSONB))
            '''),
            {
                'request_id': request_id,
                'object_id': object_id,
                'device_id': device_id,
                'payload': json.dumps(payload),
            },
        )


def save_prediction(result: dict, request_id: str | None, device_id: str):
    with engine.begin() as conn:
        conn.execute(
            text('''
                INSERT INTO predictions (
                    request_id,
                    object_id,
                    device_id,
                    final_prediction,
                    final_method,
                    final_confidence,
                    agreement,
                    ml_result,
                    knn_result
                )
                VALUES (
                    :request_id,
                    :object_id,
                    :device_id,
                    :final_prediction,
                    :final_method,
                    :final_confidence,
                    :agreement,
                    CAST(:ml_result AS JSONB),
                    CAST(:knn_result AS JSONB)
                )
            '''),
            {
                'request_id': request_id,
                'object_id': result['object_id'],
                'device_id': device_id,
                'final_prediction': result['final_prediction'],
                'final_method': result['final_method'],
                'final_confidence': float(result.get('final_confidence', 0.0)),
                'agreement': bool(result.get('agreement', False)),
                'ml_result': json.dumps(result['ml_result']),
                'knn_result': json.dumps(result['knn_result']),
            },
        )


def get_prediction(request_id: str):
    with engine.connect() as conn:
        result = conn.execute(
            text('''
                SELECT * FROM predictions
                WHERE request_id = :id
                ORDER BY created_at DESC
                LIMIT 1
            '''),
            {'id': request_id},
        ).fetchone()
        return dict(result._mapping) if result else None


def create_esp_device(device_id: str, device_name: str, is_active: bool = True):
    with engine.begin() as conn:
        conn.execute(
            text('''
                INSERT INTO esp_devices (device_id, device_name, is_active)
                VALUES (:device_id, :device_name, :is_active)
                ON CONFLICT (device_id)
                DO UPDATE SET
                    device_name = EXCLUDED.device_name,
                    is_active = EXCLUDED.is_active
            '''),
            {
                'device_id': device_id,
                'device_name': device_name,
                'is_active': is_active,
            },
        )
