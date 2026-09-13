CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id UUID NULL REFERENCES devices(id) ON DELETE SET NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude >= -90 AND latitude <= 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude >= -180 AND longitude <= 180),
    accuracy_m DOUBLE PRECISION NULL CHECK (accuracy_m IS NULL OR accuracy_m > 0),
    source TEXT NOT NULL DEFAULT 'phone_gps'
        CHECK (source IN ('phone_gps', 'manual', 'tag_ble', 'fused', 'mock')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_locations_user_time ON locations (user_id, recorded_at DESC);
CREATE INDEX IF NOT EXISTS idx_locations_device_time ON locations (device_id, recorded_at DESC);
