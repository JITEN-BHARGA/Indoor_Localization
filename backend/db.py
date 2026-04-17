import json
from sqlalchemy import create_engine, text
from backend.config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)


def init_db():
    with engine.begin() as conn:
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS raw_scans (
            id SERIAL PRIMARY KEY,
            object_id TEXT NOT NULL,
            device_id TEXT,
            payload JSONB NOT NULL,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))

        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS predictions (
            id SERIAL PRIMARY KEY,
            object_id TEXT NOT NULL,
            final_prediction TEXT NOT NULL,
            final_method TEXT NOT NULL,
            ml_result JSONB NOT NULL,
            knn_result JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """))


def save_raw_scan(object_id: str, device_id: str, payload: dict):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO raw_scans (object_id, device_id, payload)
                VALUES (:object_id, :device_id, CAST(:payload AS JSONB))
            """),
            {
                "object_id": object_id,
                "device_id": device_id,
                "payload": json.dumps(payload),
            },
        )


def save_prediction(result: dict):
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO predictions (
                    object_id,
                    final_prediction,
                    final_method,
                    ml_result,
                    knn_result
                )
                VALUES (
                    :object_id,
                    :final_prediction,
                    :final_method,
                    CAST(:ml_result AS JSONB),
                    CAST(:knn_result AS JSONB)
                )
            """),
            {
                "object_id": result["object_id"],
                "final_prediction": result["final_prediction"],
                "final_method": result["final_method"],
                "ml_result": json.dumps(result["ml_result"]),
                "knn_result": json.dumps(result["knn_result"]),
            },
        )


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