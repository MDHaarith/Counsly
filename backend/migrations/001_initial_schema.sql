-- ============================================================
-- 001_initial_schema.sql
-- Counsly P0 launch schema
-- Reference: docs/11-database-schema.md
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Identity and access
CREATE TABLE auth_identities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID NOT NULL,
    provider TEXT NOT NULL DEFAULT $$google$$,
    google_id TEXT NOT NULL,
    email TEXT NOT NULL,
    email_verified BOOLEAN NOT NULL DEFAULT false,
    display_name TEXT,
    avatar_url TEXT,
    last_login_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_auth_identities_auth_user_id UNIQUE (auth_user_id),
    CONSTRAINT uq_auth_identities_google_id UNIQUE (google_id),
    CONSTRAINT uq_auth_identities_email UNIQUE (email)
);
ALTER TABLE auth_identities ENABLE ROW LEVEL SECURITY;
CREATE INDEX idx_auth_identities_auth_user_id ON auth_identities (auth_user_id);
CREATE INDEX idx_auth_identities_google_id ON auth_identities (google_id);

CREATE TABLE app_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_identity_id UUID NOT NULL REFERENCES auth_identities (id),
    auth_user_id UUID NOT NULL,
    role TEXT NOT NULL DEFAULT $$student$$,
    status TEXT NOT NULL DEFAULT $$active$$,
    current_season_year INT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_app_users_auth_identity_id UNIQUE (auth_identity_id),
    CONSTRAINT uq_app_users_auth_user_id UNIQUE (auth_user_id)
);
ALTER TABLE app_users ENABLE ROW LEVEL SECURITY;

CREATE TABLE workspaces (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_user_id UUID NOT NULL REFERENCES app_users (id),
    workspace_kind TEXT NOT NULL DEFAULT $$personal$$,
    display_name TEXT,
    season_year INT,
    archived_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_workspaces_app_user_id UNIQUE (app_user_id)
);
ALTER TABLE workspaces ENABLE ROW LEVEL SECURITY;
CREATE INDEX idx_workspaces_app_user_id ON workspaces (app_user_id);

CREATE TABLE student_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id),
    full_name TEXT,
    board TEXT,
    district TEXT,
    home_district TEXT,
    community_quota TEXT,
    maths_mark INT,
    physics_mark INT,
    chemistry_mark INT,
    cutoff_mark INT,
    expected_cutoff_mark INT,
    official_rank INT,
    official_community_rank INT,
    roll_number TEXT,
    roll_number_verified_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_student_profiles_workspace_id UNIQUE (workspace_id),
    CONSTRAINT chk_student_profiles_community CHECK (community_quota IS NULL OR community_quota IN ($$OC$$,$$BC$$,$$BCM$$,$$MBC$$,$$SC$$,$$SCA$$,$$ST$$))
);
ALTER TABLE student_profiles ENABLE ROW LEVEL SECURITY;
CREATE INDEX idx_student_profiles_workspace_id ON student_profiles (workspace_id);

CREATE TABLE onboarding_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id),
    current_step INT NOT NULL DEFAULT 1,
    is_complete BOOLEAN NOT NULL DEFAULT false,
    eligible BOOLEAN,
    eligibility_reason TEXT,
    last_route TEXT,
    entered_phase TEXT,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_onboarding_state_workspace_id UNIQUE (workspace_id)
);
ALTER TABLE onboarding_state ENABLE ROW LEVEL SECURITY;

CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    app_user_id UUID NOT NULL REFERENCES app_users (id),
    jti TEXT NOT NULL,
    token_hash TEXT NOT NULL,
    issued_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_sessions_jti UNIQUE (jti)
);
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;
CREATE INDEX idx_user_sessions_app_user_active ON user_sessions (app_user_id, expires_at) WHERE revoked_at IS NULL;

-- Reference data
CREATE TABLE colleges (
    college_code TEXT PRIMARY KEY,
    college_name TEXT NOT NULL,
    address TEXT,
    district TEXT,
    taluk TEXT,
    pincode TEXT,
    phone_fax TEXT,
    email TEXT,
    website TEXT,
    autonomous_status TEXT,
    minority_status TEXT,
    placement_record TEXT,
    hostel_boys BOOLEAN,
    hostel_girls BOOLEAN,
    transport_facilities BOOLEAN,
    min_transport_charges INT,
    max_transport_charges INT,
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    maps_url TEXT,
    is_architecture BOOLEAN NOT NULL DEFAULT false,
    raw_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE colleges ENABLE ROW LEVEL SECURITY;

CREATE TABLE branches (
    branch_code TEXT PRIMARY KEY,
    branch_name TEXT NOT NULL,
    is_architecture BOOLEAN NOT NULL DEFAULT false,
    keep BOOLEAN NOT NULL DEFAULT true,
    removal_reasons JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE branches ENABLE ROW LEVEL SECURITY;

CREATE TABLE college_branches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    college_code TEXT NOT NULL REFERENCES colleges (college_code),
    branch_code TEXT NOT NULL REFERENCES branches (branch_code),
    branch_name TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    source_file TEXT,
    extraction_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_college_branches UNIQUE (college_code, branch_code)
);
ALTER TABLE college_branches ENABLE ROW LEVEL SECURITY;

CREATE TABLE community_seats (
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
    CONSTRAINT uq_community_seats UNIQUE (college_code, branch_code)
);
ALTER TABLE community_seats ENABLE ROW LEVEL SECURITY;

CREATE TABLE cutoff_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    season_year INT NOT NULL,
    round_number INT NOT NULL,
    aggregate_mark NUMERIC(8,4) NOT NULL,
    general_rank INT,
    community_quota TEXT NOT NULL,
    source_community_raw TEXT,
    college_code TEXT NOT NULL,
    branch_code TEXT NOT NULL,
    allotted_category TEXT,
    application_number TEXT,
    source_file TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_cutoff_community CHECK (community_quota IN ($$OC$$,$$BC$$,$$BCM$$,$$MBC$$,$$SC$$,$$SCA$$,$$ST$$))
);
ALTER TABLE cutoff_data ENABLE ROW LEVEL SECURITY;
CREATE INDEX idx_cutoff_data_season_round_community_college_branch ON cutoff_data (season_year, round_number, community_quota, college_code, branch_code);

CREATE TABLE rank_lookup (
    aggregate_mark NUMERIC(8,4) NOT NULL,
    rank_min INT NOT NULL,
    rank_max INT NOT NULL,
    confidence_label TEXT,
    sample_size INT,
    source_years JSONB,
    method_version TEXT,
    is_abstain BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT pk_rank_lookup PRIMARY KEY (aggregate_mark),
    CONSTRAINT chk_rank_confidence CHECK (confidence_label IS NULL OR confidence_label IN ($$High$$,$$Medium$$,$$Low$$))
);
ALTER TABLE rank_lookup ENABLE ROW LEVEL SECURITY;

CREATE TABLE tfc_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    district TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    latitude NUMERIC(10, 7),
    longitude NUMERIC(10, 7),
    maps_url TEXT,
    verified_at TIMESTAMPTZ,
    source_file TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE tfc_locations ENABLE ROW LEVEL SECURITY;
CREATE INDEX idx_tfc_locations_district ON tfc_locations (district);

-- Payments and access
CREATE TABLE payment_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id),
    season_year INT NOT NULL,
    razorpay_order_id TEXT NOT NULL,
    razorpay_payment_id TEXT,
    razorpay_signature TEXT,
    amount_paise INT NOT NULL,
    currency TEXT NOT NULL DEFAULT $$INR$$,
    status TEXT NOT NULL DEFAULT $$created$$,
    verified_at TIMESTAMPTZ,
    failure_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_payment_orders_razorpay_order_id UNIQUE (razorpay_order_id),
    CONSTRAINT uq_payment_orders_razorpay_payment_id UNIQUE (razorpay_payment_id),
    CONSTRAINT chk_payment_status CHECK (status IN ($$created$$,$$authorized$$,$$captured$$,$$refunded$$,$$failed$$))
);
ALTER TABLE payment_orders ENABLE ROW LEVEL SECURITY;

CREATE TABLE subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id),
    season_year INT NOT NULL,
    plan_code TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT $$pending$$,
    amount_paise INT NOT NULL,
    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,
    activated_at TIMESTAMPTZ,
    source_payment_order_id UUID REFERENCES payment_orders (id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_subscriptions_workspace_season UNIQUE (workspace_id, season_year),
    CONSTRAINT chk_subscription_status CHECK (status IN ($$pending$$,$$active$$,$$expired$$,$$payment_failed$$,$$cancelled$$))
);
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

CREATE TABLE payment_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID REFERENCES workspaces (id),
    payment_order_id UUID REFERENCES payment_orders (id),
    event_type TEXT NOT NULL,
    event_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE payment_audit_log ENABLE ROW LEVEL SECURITY;

-- Workspace product state
CREATE TABLE user_college_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id),
    preference_group TEXT NOT NULL,
    priority INT NOT NULL DEFAULT 0,
    college_code TEXT NOT NULL,
    branch_code TEXT NOT NULL,
    system_category TEXT,
    manual_category TEXT,
    notes TEXT,
    added_from TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT uq_user_college_prefs UNIQUE (workspace_id, preference_group, college_code, branch_code),
    CONSTRAINT chk_preference_group CHECK (preference_group IN ($$wishlist$$,$$primary$$,$$pinned$$)),
    CONSTRAINT chk_system_category CHECK (system_category IS NULL OR system_category IN ($$safe$$,$$moderate$$,$$ambitious$$)),
    CONSTRAINT chk_manual_category CHECK (manual_category IS NULL OR manual_category IN ($$safe$$,$$moderate$$,$$ambitious$$))
);
ALTER TABLE user_college_preferences ENABLE ROW LEVEL SECURITY;
CREATE INDEX idx_user_college_prefs_ws_group_priority ON user_college_preferences (workspace_id, preference_group, priority);

CREATE TABLE shortlist_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id),
    title TEXT NOT NULL,
    item_count INT NOT NULL DEFAULT 0,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE shortlist_snapshots ENABLE ROW LEVEL SECURITY;

CREATE TABLE shortlist_snapshot_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id UUID NOT NULL REFERENCES shortlist_snapshots (id),
    priority INT NOT NULL,
    college_code TEXT NOT NULL,
    branch_code TEXT NOT NULL,
    category TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE shortlist_snapshot_items ENABLE ROW LEVEL SECURITY;

CREATE TABLE college_compare_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id),
    title TEXT NOT NULL,
    created_from TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE college_compare_history ENABLE ROW LEVEL SECURITY;

CREATE TABLE college_compare_history_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    compare_history_id UUID NOT NULL REFERENCES college_compare_history (id),
    sort_order INT NOT NULL,
    college_code TEXT NOT NULL,
    branch_code TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE college_compare_history_items ENABLE ROW LEVEL SECURITY;

CREATE TABLE user_activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id UUID NOT NULL REFERENCES workspaces (id),
    event_type TEXT NOT NULL,
    entity_type TEXT,
    entity_id TEXT,
    event_payload JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE user_activity_log ENABLE ROW LEVEL SECURITY;
CREATE INDEX idx_user_activity_log_workspace_created ON user_activity_log (workspace_id, created_at DESC);

-- Runtime and audit
CREATE TABLE app_config (
    config_key TEXT PRIMARY KEY,
    value_type TEXT NOT NULL DEFAULT $$string$$,
    value_json JSONB,
    updated_by TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE app_config ENABLE ROW LEVEL SECURITY;

CREATE TABLE news_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    summary TEXT,
    source_url TEXT,
    published_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT $$draft$$,
    sort_order INT NOT NULL DEFAULT 0,
    created_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_news_status CHECK (status IN ($$draft$$,$$active$$,$$archived$$))
);
ALTER TABLE news_items ENABLE ROW LEVEL SECURITY;
CREATE INDEX idx_news_items_status_published ON news_items (status, published_at DESC);

CREATE TABLE ingestion_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_name TEXT NOT NULL,
    run_type TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at TIMESTAMPTZ,
    source_reference TEXT,
    rows_seen INT,
    rows_loaded INT,
    report_path TEXT,
    error_message TEXT,
    CONSTRAINT chk_ingestion_status CHECK (status IN ($$started$$,$$success$$,$$failed$$,$$rejected$$))
);
ALTER TABLE ingestion_audit_log ENABLE ROW LEVEL SECURITY;

CREATE TABLE data_freshness (
    dataset_name TEXT PRIMARY KEY,
    last_success_at TIMESTAMPTZ,
    last_source_at TIMESTAMPTZ,
    freshness_status TEXT NOT NULL DEFAULT $$missing$$,
    source_reference TEXT,
    notes TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_data_freshness_status CHECK (freshness_status IN ($$missing$$,$$seeded_unverified$$,$$verified$$,$$stale$$,$$disabled$$))
);
ALTER TABLE data_freshness ENABLE ROW LEVEL SECURITY;

CREATE TABLE admin_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_identifier TEXT NOT NULL,
    command TEXT NOT NULL,
    target_key TEXT,
    previous_value JSONB,
    new_value JSONB,
    success BOOLEAN NOT NULL DEFAULT false,
    validation_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE admin_audit_log ENABLE ROW LEVEL SECURITY;

INSERT INTO app_config (config_key, value_type, value_json) VALUES
    ($$TNEA_PHASE$$, $$integer$$, $$0$$),
    ($$TOTAL_ROUNDS$$, $$integer$$, $$0$$),
    ($$RANK_RELEASED$$, $$boolean$$, $$false$$),
    ($$ROLL_DATA_READY$$, $$boolean$$, $$false$$),
    ($$RANK_LOOKUP_READY$$, $$boolean$$, $$false$$),
    ($$FREE_CHAT_LIMIT$$, $$integer$$, $$3$$),
    ($$SEASON_END_DATE$$, $$string$$, $$null$$),
    ($$BROADCAST_ACTIVE$$, $$boolean$$, $$false$$),
    ($$BROADCAST_MESSAGE$$, $$string$$, $$null$$)
ON CONFLICT (config_key) DO NOTHING;

INSERT INTO data_freshness (dataset_name, freshness_status, notes) VALUES
    ($$colleges$$, $$missing$$, $$Seed from local extractor before launch$$),
    ($$branches$$, $$missing$$, $$Seed from local extractor before launch$$),
    ($$college_branches$$, $$missing$$, $$Seed from local extractor before launch$$),
    ($$community_seats$$, $$missing$$, $$Seed from local extractor before launch$$),
    ($$cutoff_data$$, $$missing$$, $$Seed from local extractor before launch$$),
    ($$rank_lookup$$, $$missing$$, $$Build from GRL 2020 to 2025 before launch$$),
    ($$tfc_locations$$, $$missing$$, $$Seed from local extractor before launch$$)
ON CONFLICT (dataset_name) DO NOTHING;
