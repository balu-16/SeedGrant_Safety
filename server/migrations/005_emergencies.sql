CREATE TABLE IF NOT EXISTS emergencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protected_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    device_id UUID NULL REFERENCES devices(id) ON DELETE SET NULL,
    trigger_type TEXT NOT NULL
        CHECK (trigger_type IN ('TAG_BUTTON', 'TAG_VOICE', 'APP_BUTTON', 'APP_VOICE', 'FALL_DETECTION')),
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'acknowledged', 'resolved', 'cancelled')),
    latitude DOUBLE PRECISION NULL CHECK (latitude IS NULL OR (latitude >= -90 AND latitude <= 90)),
    longitude DOUBLE PRECISION NULL CHECK (longitude IS NULL OR (longitude >= -180 AND longitude <= 180)),
    note TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL
);
CREATE INDEX IF NOT EXISTS idx_emergencies_user_time ON emergencies (protected_user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_emergencies_status ON emergencies (status);

CREATE TABLE IF NOT EXISTS emergency_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    emergency_id UUID NOT NULL REFERENCES emergencies(id) ON DELETE CASCADE,
    actor_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    from_status TEXT NULL,
    to_status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_emergency_events_emergency ON emergency_events (emergency_id, created_at);
