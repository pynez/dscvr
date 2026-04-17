-- DSCVR Supabase Schema
-- Run this in the Supabase SQL editor or via CLI:
--   supabase db push  (if using supabase CLI)
--   or paste into: Project > SQL Editor > New query

-- ─── Users ───────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          UUID        PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── Interactions ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS interactions (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    track_id          VARCHAR     NOT NULL,   -- row_index as string
    interaction_type  VARCHAR     NOT NULL,   -- 'heart' | 'skip' | 'complete'
    feature           VARCHAR,                -- 'recommend'|'soundtrack'|etc. for attribution
    timestamp         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT interactions_type_check
        CHECK (interaction_type IN ('heart', 'skip', 'complete'))
);

CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_track_id ON interactions(track_id);

-- ─── Taste Profile ────────────────────────────────────────────────────────────
-- Materialized per-user tag scores; updated incrementally on each interaction.
CREATE TABLE IF NOT EXISTS taste_profile (
    user_id     UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    tag         VARCHAR     NOT NULL,
    score       FLOAT       NOT NULL DEFAULT 0,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user_id, tag)
);

CREATE INDEX IF NOT EXISTS idx_taste_profile_user_id ON taste_profile(user_id);
