-- Drop the unused index on the raw plaintext push token.
-- Lookups go through token_hash (registration/unregister) or user_id
-- (delivery fan-out); no query ever filters by the raw token, so the
-- index only broadened exposure of sendable credentials.
DROP INDEX IF EXISTS idx_push_tokens_token;
