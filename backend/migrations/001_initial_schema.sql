-- ============================================================
-- 001_initial_schema.sql
-- Counsly P0 tables — Supabase PostgreSQL
-- Generated: 2026-04-24
-- Reference: docs/11-database-schema.md
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- Identity & Access
-- ============================================================

-- auth_identities: External identity bridge for direct Google OAuth
CREATE TABLE auth_identities (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id    UUID NOT NULL,
    provider        TEXT NOT NULL DEFAULT 'google',
    google_id       TEXT NOT NULL,
    email           TEXT NOT NULL,
    email_verified  BOOLEAN NOT NULL DEFAULT FALSE,
    display_name    TEXT,
    avatar_url      TEXT,
    last_login_at   TIMESTAMPTZ,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_auth_identities_auth_user_id   UNIQUE (auth_user_id),
    CONSTRAINT uq_auth_identities_google_id      UNIQUE (google_id),
    CONSTRAINT uq_auth_identities_email          UNIQUE (email)
);

-- enable RLS
ALTER TABLE auth_identities ENABLE ROW LEVEL SECURITY;

CREATE INDEX idx_auth_identities_auth_user_id ON auth_identities (auth_user_id);
CREATE INDEX idx_auth_identities_google_id    ON auth_identities (google_id);

-- app_users: Internal app principal row
CREATE TABLE app_users (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_identity_id    UUID NOT NULL,
    auth_user_id        UUID NOT NULL,
    role                TEXT NOT NULL DEFAULT 'student',
    status              TEXT NOT NULL DEFAULT 'active',
    current_season_year INT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_app_users_auth_identity_id   UNIQUE (auth_identity_id),
    CONSTRAINT uq_app_users_auth_user_id       UNIQUE (auth_user_id)
);

ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;

-- workspaces: Personal Data Environment boundary
CREATE TABLE workspaces (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_user_id     UUID NOT NULL,
    workspace_kind  TEXT NOT NULL DEFAULT 'personal',
    display_name    TEXT,
    season_year     INT,
    archived_at     TIMESTAMPTZ,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_workspaces_app_user_id UNIQUE (app_user_id)
);

ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;

CREATE INDEX idx_workspaces_app_user_id ON workspaces (app_user_id);

-- student_profiles: Onboarding + canonical student facts
CREATE TABLE student_profiles (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id            UUID NOT NULL,

    full_name               TEXT,
    board                   TEXT,
    district                TEXT,
    home_district           TEXT,
    community_quota         TEXT,  -- OC, BC, BCM, MBC, SC, SCA, ST

    maths_mark              INT,
    physics_mark            INT,
    chemistry_mark          INT,
    cutoff_mark             INT,
    expected_cutoff_mark    INT,

    official_rank           INT,
    official_community_rank INT,
    roll_number             TEXT,
    roll_number_verified_at TIMESTAMPTZ,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_student_profiles_workspace_id UNIQUE (workspace_id),

    CONSTRAINT chk_student_profiles_community
        CHECK (community_quota IN ('OC','BC','BCM','MBC','SC','SCA','ST'))
);

ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;

CREATE INDEX idx_student_profiles_workspace_id ON student_profiles (workspace_id);

-- onboarding_state: Resume-exact-step state machine
CREATE TABLE onboarding_state (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID NOT NULL,

    current_step        INT NOT NULL DEFAULT 1,
    is_complete         BOOLEAN NOT NULL DEFAULT FALSE,
    eligible            BOOLEAN,
    eligibility_reason  TEXT,
    last_route          TEXT,
    entered_phase       TEXT,
    completed_at        TIMESTAMPTZ,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_onboarding_state_workspace_id UNIQUE (workspace_id)
);

ALTER TABLE onboarding_state ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Reference Data
-- ============================================================

-- colleges: Canonical college master
CREATE TABLE colleges (
    college_code          TEXT PRIMARY KEY,
    college_name          TEXT NOT NULL,
    address               TEXT,
    district              TEXT,
    taluk                 TEXT,
    pincode               TEXT,
    phone_fax             TEXT,
    email                 TEXT,
    website               TEXT,
    autonomous_status     TEXT,
    minority_status       TEXT,
    placement_record      TEXT,
    hostel_boys           BOOLEAN,
    hostel_girls          BOOLEAN,
    transport_facilities  BOOLEAN,
    min_transport_charges INT,
    max_transport_charges INT,
    latitude              NUMERIC(10, 7),
    longitude             NUMERIC(10, 7),
    maps_url              TEXT,
    is_architecture       BOOLEAN NOT NULL DEFAULT FALSE,
    raw_payload           JSONB,

    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE colleges ENABLE ROW LEVEL SECURITY;

-- branches: Canonical branch master
CREATE TABLE branches (
    branch_code      TEXT PRIMARY KEY,
    branch_name      TEXT NOT NULL,
    is_architecture  BOOLEAN NOT NULL DEFAULT FALSE,
    keep             BOOLEAN NOT NULL DEFAULT TRUE,
    removal_reasons  JSONB,

    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE branches ENABLE ROW LEVEL SECURITY;

-- college_branches: College-to-branch mapping
CREATE TABLE college_branches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    college_code    TEXT NOT NULL REFERENCES colleges (college_code),
    branch_code     TEXT NOT NULL REFERENCES branches (branch_code),
    branch_name     TEXT,
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    source_file     TEXT,
    extraction_date DATE,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_college_branches UNIQUE (college_code, branch_code)
);

ALTER TABLE college_branches ENABLE ROW LEVEL SECURITY;

-- community_seats: Per-college per-branch seat totals
CREATE TABLE community_seats (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    college_code    TEXT NOT NULL REFERENCES colleges (college_code),
    branch_code     TEXT NOT NULL REFERENCES branches (branch_code),

    oc              INT NOT NULL DEFAULT 0,
    bc              INT NOT NULL DEFAULT 0,
    bcm             INT NOT NULL DEFAULT 0,
    mbc             INT NOT NULL DEFAULT 0,
    sc              INT NOT NULL DEFAULT 0,
    sca             INT NOT NULL DEFAULT 0,
    st              INT NOT NULL DEFAULT 0,
    total           INT NOT NULL DEFAULT 0,

    source_file     TEXT,
    extraction_date DATE,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_community_seats UNIQUE (college_code, branch_code)
);

ALTER TABLE community_seats ENABLE ROW LEVEL SECURITY;

-- cutoff_data: Historical allotment rows for recommendations and analytics
CREATE TABLE cutoff_data (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_year         INT NOT NULL,
    round_number        INT NOT NULL,
    aggregate_mark      INT NOT NULL,
    general_rank        INT,
    community_quota     TEXT NOT NULL,
    source_community_raw TEXT,
    college_code        TEXT NOT NULL,
    branch_code         TEXT NOT NULL,
    allotted_category   TEXT,
    application_number  TEXT,
    source_file         TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_cutoff_community
        CHECK (community_quota IN ('OC','BC','BCM','MBC','SC','SCA','ST'))
);

ALTER TABLE cutoff_data ENABLE ROW LEVEL SECURITY;

CREATE INDEX idx_cutoff_data_season_round_community_college_branch
    ON cutoff_data (season_year, round_number, community_quota, college_code, branch_code);

-- rank_lookup: Pre-computed historical rank band lookup
-- PK is aggregate_mark (INT), NOT composite subject marks
CREATE TABLE rank_lookup (
    aggregate_mark   INT PRIMARY KEY,
    rank_min         INT NOT NULL,
    rank_max         INT NOT NULL,
    confidence_label TEXT,  -- e.g. 'high', 'medium', 'low'
    sample_size      INT,
    source_years     JSONB,
    method_version   TEXT,
    is_abstain       BOOLEAN NOT NULL DEFAULT FALSE
);

ALTER TABLE rank_lookup ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Subscriptions & Payments
-- ============================================================

-- subscriptions: Paid entitlement for a season
CREATE TABLE subscriptions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id            UUID NOT NULL REFERENCES workspaces (id),
    season_year             INT NOT NULL,

    plan_code               TEXT NOT NULL,
    status                  TEXT NOT NULL DEFAULT 'pending',
    amount_paise            INT NOT NULL,
    starts_at               TIMESTAMPTZ,
    ends_at                 TIMESTAMPTZ,
    activated_at            TIMESTAMPTZ,
    source_payment_order_id UUID REFERENCES payment_orders (id),

    created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_subscriptions_workspace_season UNIQUE (workspace_id, season_year),

    CONSTRAINT chk_subscription_status
        CHECK (status IN ('pending','active','expired','payment_failed','cancelled'))
);

ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- payment_orders: Razorpay order/payment linkage
CREATE TABLE payment_orders (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id        UUID NOT NULL REFERENCES workspaces (id),
    season_year         INT NOT NULL,

    razorpay_order_id   TEXT NOT NULL,
    razorpay_payment_id TEXT,
    razorpay_signature  TEXT,
    amount_paise        INT NOT NULL,
    currency            TEXT NOT NULL DEFAULT 'INR',
    status              TEXT NOT NULL DEFAULT 'created',
    verified_at         TIMESTAMPTZ,
    failure_reason      TEXT,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_payment_orders_razorpay_order_id  UNIQUE (razorpay_order_id),
    CONSTRAINT uq_payment_orders_razorpay_payment_id UNIQUE (razorpay_payment_id),

    CONSTRAINT chk_payment_status
        CHECK (status IN ('created','authorized','captured','refunded','failed'))
);

ALTER TABLE payment_orders ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- Workspace Product Tables
-- ============================================================

-- user_college_preferences: Canonical preference store (FR-44)
CREATE TABLE user_college_preferences (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id     UUID NOT NULL REFERENCES workspaces (id),
    preference_group TEXT NOT NULL,
    priority         INT NOT NULL DEFAULT 0,
    college_code     TEXT NOT NULL,
    branch_code      TEXT NOT NULL,
    system_category  TEXT,  -- safe / moderate / ambitious
    manual_category  TEXT,
    notes            TEXT,
    added_from       TEXT,
    active           BOOLEAN NOT NULL DEFAULT TRUE,

    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_user_college_prefs UNIQUE (workspace_id, preference_group, college_code, branch_code),

    CONSTRAINT chk_preference_group
        CHECK (preference_group IN ('wishlist','primary','pinned')),

    CONSTRAINT chk_safety_category
        CHECK (system_category IS NULL OR system_category IN ('safe','moderate','ambitious'))
);

ALTER TABLE user_college_preferences ENABLE ROW LEVEL SECURITY;

CREATE INDEX idx_user_college_prefs_ws_group_priority
    ON user_college_preferences (workspace_id, preference_group, priority);

-- user_activity_log: Timeline/events inside a workspace
CREATE TABLE user_activity_log (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id  UUID NOT NULL REFERENCES workspaces (id),
    event_type    TEXT NOT NULL,
    entity_type   TEXT,
    entity_id     TEXT,
    event_payload JSONB,

    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    -- append-only: no updated_at column
);

ALTER TABLE user_activity_log ENABLE ROW LEVEL SECURITY;

CREATE INDEX idx_user_activity_log_workspace_created
    ON user_activity_log (workspace_id, created_at DESC);

-- ============================================================
-- Runtime Configuration & News
-- ============================================================

-- app_config: Runtime key-value store
CREATE TABLE app_config (
    config_key  TEXT PRIMARY KEY,
    value_type  TEXT NOT NULL DEFAULT 'string',  -- string / integer / boolean / json
    value_json  JSONB,
    updated_by  TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE app_config ENABLE ROW LEVEL SECURITY;

-- news_items: Runtime-managed news strip and links
CREATE TABLE news_items (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title       TEXT NOT NULL,
    summary     TEXT,
    source_url  TEXT,
    published_at TIMESTAMPTZ,
    status      TEXT NOT NULL DEFAULT 'draft',
    sort_order  INT NOT NULL DEFAULT 0,
    created_by  TEXT,

    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_news_status
        CHECK (status IN ('draft','active','archived'))
);

ALTER TABLE news_items ENABLE ROW LEVEL SECURITY;

CREATE INDEX idx_news_items_status_published
    ON news_items (status, published_at DESC);

-- ============================================================
-- Seed app_config defaults
-- ============================================================

INSERT INTO app_config (config_key, value_type, value_json) VALUES
    ('TNEA_PHASE',       'integer', '"0"'),
    ('TOTAL_ROUNDS',     'integer', '"0"'),
    ('RANK_RELEASED',    'boolean', '"false"'),
    ('ROLL_DATA_READY',  'boolean', '"false"'),
    ('FREE_CHAT_LIMIT',  'integer', '"5"'),
    ('SEASON_END_DATE',  'string',  'null'),
    ('BROADCAST_ACTIVE', 'boolean', '"false"'),
    ('BROADCAST_MESSAGE','string',  'null')
ON CONFLICT (config_key) DO NOTHING;
