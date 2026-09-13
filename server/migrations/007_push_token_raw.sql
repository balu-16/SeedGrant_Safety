-- Raw sendable token (hashes alone cannot be used for FCM delivery).
-- Nullable so pre-existing rows keep working; clients re-register to backfill.
ALTER TABLE push_tokens ADD COLUMN IF NOT EXISTS token TEXT;
CREATE INDEX IF NOT EXISTS idx_push_tokens_token ON push_tokens (token);
