CREATE TABLE IF NOT EXISTS guardians (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    protected_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    guardian_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
    guardian_email CITEXT NOT NULL,
    guardian_name TEXT NOT NULL DEFAULT '',
    relation TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'accepted', 'rejected', 'removed')),
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_guardian_protected_email UNIQUE (protected_user_id, guardian_email),
    CONSTRAINT chk_guardian_not_self CHECK (guardian_user_id IS NULL OR guardian_user_id <> protected_user_id)
);
CREATE INDEX IF NOT EXISTS idx_guardians_protected ON guardians (protected_user_id, status);
CREATE INDEX IF NOT EXISTS idx_guardians_user ON guardians (guardian_user_id);
CREATE INDEX IF NOT EXISTS idx_guardians_email ON guardians (guardian_email);
