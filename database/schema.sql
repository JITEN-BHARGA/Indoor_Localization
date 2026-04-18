CREATE TABLE IF NOT EXISTS objects (
    object_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS esp_devices (
    device_id TEXT PRIMARY KEY,
    device_name TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    last_seen_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS scan_requests (
    request_id TEXT PRIMARY KEY,
    object_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS scan_request_devices (
    id BIGSERIAL PRIMARY KEY,
    request_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    UNIQUE(request_id, device_id)
);

CREATE TABLE IF NOT EXISTS raw_scans (
    id BIGSERIAL PRIMARY KEY,
    request_id TEXT,
    object_id TEXT NOT NULL,
    device_id TEXT NOT NULL,
    payload JSONB NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS predictions (
    id BIGSERIAL PRIMARY KEY,
    request_id TEXT,
    object_id TEXT NOT NULL,
    final_prediction TEXT NOT NULL,
    final_method TEXT NOT NULL,
    ml_result JSONB NOT NULL,
    knn_result JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);