CREATE TABLE IF NOT EXISTS devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL DEFAULT 'Smart Safety Tag' CHECK (char_length(name) BETWEEN 1 AND 120),
    battery_pct SMALLINT NULL CHECK (battery_pct IS NULL OR (battery_pct >= 0 AND battery_pct <= 100)),
    connection_state TEXT NOT NULL DEFAULT 'offline' CHECK (connection_state IN ('offline', 'online', 'unknown')),
    last_seen_at TIMESTAMPTZ NULL,
    device_secret_hash TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_devices_owner_id ON devices (owner_id);
CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON devices (last_seen_at DESC NULLS LAST);
