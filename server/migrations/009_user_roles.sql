-- Admin portal: role-based access + account suspension.
-- Existing users stay 'user'; admins are promoted via ADMIN_EMAILS bootstrap or CLI.

ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'user';
ALTER TABLE users ADD COLUMN IF NOT EXISTS disabled_at TIMESTAMPTZ NULL;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'users_role_check'
    ) THEN
        ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('user', 'admin'));
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_users_role ON users (role);
