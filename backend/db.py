import json
import uuid
from typing import Optional
from sqlalchemy import create_engine, text
from backend.config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)


def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS objects (
            object_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS esp_devices (
            device_id TEXT PRIMARY KEY,
            device_name TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            last_seen_at TIMESTAMP NULL
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS scan_requests (
            request_id TEXT PRIMARY KEY,
            object_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP NULL
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS scan_request_devices (
            id SERIAL PRIMARY KEY,
            request_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            UNIQUE(request_id, device_id)
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS raw_scans (
            id SERIAL PRIMARY KEY,
            request_id TEXT,
            object_id TEXT NOT NULL,
            device_id TEXT NOT NULL,
            payload JSONB NOT NULL,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            request_id TEXT,
            object_id TEXT NOT NULL,
            final_prediction TEXT NOT NULL,
            final_method TEXT NOT NULL,
            ml_result JSONB NOT NULL,
            knn_result JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))


def create_object(object_id: str, name: str, description: Optional[str] = None):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO objects (object_id, name, description)
                VALUES (:object_id, :name, :description)
                ON CONFLICT (object_id)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description
            """),
            {
                "object_id": object_id,
                "name": name,
                "description": description,
            },
        )


def list_objects():
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT object_id, name, description, created_at
            FROM objects
            ORDER BY created_at DESC
        """)).fetchall()

    return [
        {
            "object_id": row[0],
            "name": row[1],
            "description": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
        }
        for row in rows
    ]


def get_object(object_id: str):
    with engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT object_id, name, description, created_at
                FROM objects
                WHERE object_id = :object_id
            """),
            {"object_id": object_id},
        ).fetchone()

    if not row:
        return None

    return {
        "object_id": row[0],
        "name": row[1],
        "description": row[2],
        "created_at": row[3].isoformat() if row[3] else None,
    }


def upsert_esp_device(device_id: str, device_name: str, is_active: bool = True):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO esp_devices (device_id, device_name, is_active, last_seen_at)
                VALUES (:device_id, :device_name, :is_active, CURRENT_TIMESTAMP)
                ON CONFLICT (device_id)
                DO UPDATE SET
                    device_name = EXCLUDED.device_name,
                    is_active = EXCLUDED.is_active,
                    last_seen_at = CURRENT_TIMESTAMP
            """),
            {
                "device_id": device_id,
                "device_name": device_name,
                "is_active": is_active,
            },
        )


def touch_esp_device(device_id: str):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE esp_devices
                SET last_seen_at = CURRENT_TIMESTAMP
                WHERE device_id = :device_id
            """),
            {"device_id": device_id},
        )


def list_esp_devices():
    with engine.begin() as conn:
        rows = conn.execute(text("""
            SELECT device_id, device_name, is_active, last_seen_at
            FROM esp_devices
            ORDER BY device_name ASC
        """)).fetchall()

    return [
        {
            "device_id": row[0],
            "device_name": row[1],
            "is_active": bool(row[2]),
            "last_seen_at": row[3].isoformat() if row[3] else None,
        }
        for row in rows
    ]


def get_esp_devices_by_ids(device_ids: list[str]):
    if not device_ids:
        return []

    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT device_id, device_name, is_active, last_seen_at
                FROM esp_devices
                WHERE device_id = ANY(:device_ids)
            """),
            {"device_ids": device_ids},
        ).fetchall()

    return [
        {
            "device_id": row[0],
            "device_name": row[1],
            "is_active": bool(row[2]),
            "last_seen_at": row[3].isoformat() if row[3] else None,
        }
        for row in rows
    ]


def create_scan_request(object_id: str, device_ids: list[str]) -> str:
    request_id = str(uuid.uuid4())

    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO scan_requests (request_id, object_id, status)
                VALUES (:request_id, :object_id, 'pending')
            """),
            {
                "request_id": request_id,
                "object_id": object_id,
            },
        )

        for device_id in device_ids:
            conn.execute(
                text("""
                    INSERT INTO scan_request_devices (request_id, device_id, status)
                    VALUES (:request_id, :device_id, 'pending')
                """),
                {
                    "request_id": request_id,
                    "device_id": device_id,
                },
            )

    return request_id


def mark_scan_request_collecting(request_id: str):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE scan_requests
                SET status = 'collecting'
                WHERE request_id = :request_id
            """),
            {"request_id": request_id},
        )


def complete_scan_request(request_id: str):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE scan_requests
                SET status = 'completed',
                    completed_at = CURRENT_TIMESTAMP
                WHERE request_id = :request_id
            """),
            {"request_id": request_id},
        )


def mark_scan_request_failed(request_id: str):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE scan_requests
                SET status = 'failed'
                WHERE request_id = :request_id
            """),
            {"request_id": request_id},
        )


def mark_device_response_received(request_id: str, device_id: str):
    with engine.begin() as conn:
        conn.execute(
            text("""
                UPDATE scan_request_devices
                SET status = 'received'
                WHERE request_id = :request_id AND device_id = :device_id
            """),
            {
                "request_id": request_id,
                "device_id": device_id,
            },
        )


def save_raw_scan(request_id: Optional[str], object_id: str, device_id: str, payload: dict):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO raw_scans (request_id, object_id, device_id, payload)
                VALUES (:request_id, :object_id, :device_id, CAST(:payload AS JSONB))
            """),
            {
                "request_id": request_id,
                "object_id": object_id,
                "device_id": device_id,
                "payload": json.dumps(payload),
            },
        )


def get_raw_scans_for_request(request_id: str):
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT payload
                FROM raw_scans
                WHERE request_id = :request_id
                ORDER BY received_at ASC
            """),
            {"request_id": request_id},
        ).fetchall()

    return [row[0] for row in rows]


def save_prediction(result: dict, request_id: Optional[str] = None):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO predictions (
                    request_id,
                    object_id,
                    final_prediction,
                    final_method,
                    ml_result,
                    knn_result
                )
                VALUES (
                    :request_id,
                    :object_id,
                    :final_prediction,
                    :final_method,
                    CAST(:ml_result AS JSONB),
                    CAST(:knn_result AS JSONB)
                )
            """),
            {
                "request_id": request_id,
                "object_id": result["object_id"],
                "final_prediction": result["final_prediction"],
                "final_method": result["final_method"],
                "ml_result": json.dumps(result["ml_result"]),
                "knn_result": json.dumps(result["knn_result"]),
            },
        )


def get_prediction_by_request(request_id: str):
    with engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT object_id, final_prediction, final_method, ml_result, knn_result, created_at
                FROM predictions
                WHERE request_id = :request_id
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"request_id": request_id},
        ).fetchone()

    if not row:
        return None

    return {
        "object_id": row[0],
        "final_prediction": row[1],
        "final_method": row[2],
        "ml_result": row[3],
        "knn_result": row[4],
        "created_at": row[5].isoformat() if row[5] else None,
    }


def get_latest_prediction():
    with engine.begin() as conn:
        row = conn.execute(text("""
            SELECT object_id, final_prediction, final_method, ml_result, knn_result, created_at
            FROM predictions
            ORDER BY created_at DESC
            LIMIT 1
        """)).fetchone()

    if not row:
        return None

    return {
        "object_id": row[0],
        "final_prediction": row[1],
        "final_method": row[2],
        "ml_result": row[3],
        "knn_result": row[4],
        "created_at": row[5].isoformat() if row[5] else None,
    }


def get_latest_prediction_for_object(object_id: str):
    with engine.begin() as conn:
        row = conn.execute(
            text("""
                SELECT object_id, final_prediction, final_method, ml_result, knn_result, created_at
                FROM predictions
                WHERE object_id = :object_id
                ORDER BY created_at DESC
                LIMIT 1
            """),
            {"object_id": object_id},
        ).fetchone()

    if not row:
        return None

    return {
        "object_id": row[0],
        "final_prediction": row[1],
        "final_method": row[2],
        "ml_result": row[3],
        "knn_result": row[4],
        "created_at": row[5].isoformat() if row[5] else None,
    }


def get_scan_request_status(request_id: str):
    with engine.begin() as conn:
        req = conn.execute(
            text("""
                SELECT request_id, object_id, status, requested_at, completed_at
                FROM scan_requests
                WHERE request_id = :request_id
            """),
            {"request_id": request_id},
        ).fetchone()

        if not req:
            return None

        device_rows = conn.execute(
            text("""
                SELECT device_id, status
                FROM scan_request_devices
                WHERE request_id = :request_id
                ORDER BY device_id ASC
            """),
            {"request_id": request_id},
        ).fetchall()

    device_statuses = [
        {"device_id": row[0], "status": row[1]}
        for row in device_rows
    ]

    received_count = sum(1 for item in device_statuses if item["status"] == "received")

    return {
        "request_id": req[0],
        "object_id": req[1],
        "status": req[2],
        "requested_at": req[3].isoformat() if req[3] else None,
        "completed_at": req[4].isoformat() if req[4] else None,
        "expected_device_count": len(device_statuses),
        "received_device_count": received_count,
        "device_statuses": device_statuses,
    }