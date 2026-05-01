-- ============================================================
-- 002_launch_schema_gaps.sql
-- Counsly launch schema gaps from PRD/database contract
-- ============================================================

BEGIN;

-- Seat-matrix round uploads are stored in separate physical tables for 2026, for example:
-- seat_matrix_2026_r1, seat_matrix_2026_r2, seat_matrix_2026_r3.
-- seat_matrix_current is the app-facing mirror for realistic choice-filling availability.
CREATE TABLE IF NOT EXISTS seat_matrix_round_tables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_year INT NOT NULL,
    round_number INT NOT NULL,
    table_name TEXT NOT NULL,
    source_file TEXT,
    extraction_date DATE,
    rows_loaded INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_seat_matrix_round_tables UNIQUE (season_year, round_number),
    CONSTRAINT uq_seat_matrix_round_table_name UNIQUE (table_name)
);
ALTER TABLE seat_matrix_round_tables ENABLE ROW LEVEL SECURITY;

CREATE TABLE IF NOT EXISTS seat_matrix_current (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    college_code TEXT NOT NULL REFERENCES colleges (college_code),
    branch_code TEXT NOT NULL REFERENCES branches (branch_code),
    oc INT NOT NULL DEFAULT 0,
    bc INT NOT NULL DEFAULT 0,
    bcm INT NOT NULL DEFAULT 0,
    mbc INT NOT NULL DEFAULT 0,
    sc INT NOT NULL DEFAULT 0,
    sca INT NOT NULL DEFAULT 0,
    st INT NOT NULL DEFAULT 0,
    total INT NOT NULL DEFAULT 0,
    source_file TEXT,
    extraction_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_seat_matrix_current UNIQUE (college_code, branch_code)
);
ALTER TABLE seat_matrix_current ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS idx_seat_matrix_current_available
    ON seat_matrix_current (total, college_code, branch_code);

-- Official rank-list rows and roll-number verification.
CREATE TABLE IF NOT EXISTS tnea_roll_numbers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_year INT NOT NULL,
    roll_number TEXT,
    application_number TEXT NOT NULL,
    general_rank INT,
    aggregate_mark NUMERIC(8,4),
    community_quota TEXT,
    source_community_raw TEXT,
    community_rank INT,
    candidate_name TEXT,
    date_of_birth DATE,
    random_number TEXT,
    source_file TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_tnea_roll_numbers_application UNIQUE (season_year, application_number),
    CONSTRAINT uq_tnea_roll_numbers_roll UNIQUE (season_year, roll_number),
    CONSTRAINT chk_tnea_roll_numbers_community CHECK (community_quota IS NULL OR community_quota IN ($$OC$$,$$BC$$,$$BCM$$,$$MBC$$,$$SC$$,$$ST$$))
);
ALTER TABLE tnea_roll_numbers ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS idx_tnea_roll_numbers_season_rank
    ON tnea_roll_numbers (season_year, general_rank);
CREATE INDEX IF NOT EXISTS idx_tnea_roll_numbers_season_community
    ON tnea_roll_numbers (season_year, community_quota, community_rank);

CREATE TABLE IF NOT EXISTS roll_number_claims (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id),
    season_year INT NOT NULL,
    roll_number TEXT NOT NULL,
    claim_status TEXT NOT NULL DEFAULT $$claimed$$,
    verified_at TIMESTAMPTZ,
    conflict_note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_roll_number_claims UNIQUE (season_year, roll_number),
    CONSTRAINT chk_roll_number_claim_status CHECK (claim_status IN ($$claimed$$,$$verified$$,$$conflict$$,$$released$$))
);
ALTER TABLE roll_number_claims ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS idx_roll_number_claims_workspace
    ON roll_number_claims (workspace_id, season_year);

-- Legacy runtime round schedule table. Launch status now reads ROUND_1_DATE
-- through ROUND_5_DATE from environment variables; keep this table for a
-- later cleanup migration instead of dropping it here.
CREATE TABLE IF NOT EXISTS round_dates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_year INT NOT NULL,
    round_number INT NOT NULL,
    choice_fill_start_at TIMESTAMPTZ,
    choice_fill_end_at TIMESTAMPTZ,
    allotment_at TIMESTAMPTZ,
    confirm_end_at TIMESTAMPTZ,
    report_end_at TIMESTAMPTZ,
    is_active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_round_dates UNIQUE (season_year, round_number)
);
ALTER TABLE round_dates ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS idx_round_dates_season_active
    ON round_dates (season_year, is_active, round_number);

-- Saved filters for recommendations/explore/profile defaults.
CREATE TABLE IF NOT EXISTS user_saved_filters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id),
    screen_name TEXT NOT NULL,
    filter_payload JSONB NOT NULL DEFAULT $$ {} $$::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_saved_filters UNIQUE (workspace_id, screen_name)
);
ALTER TABLE user_saved_filters ENABLE ROW LEVEL SECURITY;

-- Chat persistence moved to Supabase Storage (see 007_chat_tables.sql).
-- The tables below are intentionally commented out to avoid creating
-- DB-backed message storage (150 MB database cap).
--
-- CREATE TABLE IF NOT EXISTS chat_threads ( ... );
-- CREATE TABLE IF NOT EXISTS chat_messages ( ... );
-- CREATE TABLE IF NOT EXISTS chat_usage_counters ( ... );

INSERT INTO data_freshness (dataset_name, freshness_status, notes) VALUES
    ($$seat_matrix_current$$, $$missing$$, $$Sync from latest 2026 seat-matrix round for realistic choice filling$$),
    ($$tnea_roll_numbers$$, $$missing$$, $$Load from official GRL/rank-list parser when available$$)
ON CONFLICT (dataset_name) DO NOTHING;

COMMIT;
