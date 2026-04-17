CREATE TABLE IF NOT EXISTS objects (
    object_id TEXT PRIMARY KEY,
    name TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS raw_scans (
    id BIGSERIAL PRIMARY KEY,
    object_id TEXT NOT NULL,
    device_id TEXT,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    object_id TEXT NOT NULL,
    predicted_location TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    method TEXT NOT NULL,
    top_k JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
