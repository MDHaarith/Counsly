-- Counsly DB Schema (v2.0)
-- Optimized for both PostgreSQL (Supabase) and standard SQL-compliant local databases (SQLite).

-- 2. Users Table
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY,
  auth_user_id UUID UNIQUE NOT NULL,
  google_id VARCHAR(100), -- Legacy migration alias
  google_email VARCHAR(200),
  name VARCHAR(100),
  subscription_active BOOLEAN DEFAULT FALSE,
  subscription_expiry DATE,
  razorpay_payment_id VARCHAR(100),
  welcome_message_sent BOOLEAN DEFAULT FALSE,
  roll_number VARCHAR(20),
  roll_number_verified BOOLEAN DEFAULT FALSE,
  device_fingerprint_hash VARCHAR(64),
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  last_login TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. Workspaces Table (Strictly Private Personal Data Environment)
CREATE TABLE IF NOT EXISTS workspaces (
  id UUID PRIMARY KEY,
  user_id UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(120) NOT NULL,
  slug VARCHAR(80) UNIQUE,
  onboarding_step VARCHAR(40) DEFAULT 'marks',
  onboarding_completed BOOLEAN DEFAULT FALSE,
  onboarding_completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. Workspace Settings Table
CREATE TABLE IF NOT EXISTS workspace_settings (
  id UUID PRIMARY KEY,
  workspace_id UUID UNIQUE NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  default_district VARCHAR(100),
  preferred_branch_defaults TEXT, -- Stored as comma-separated list of codes (JSON or CSV list)
  phase_preferences TEXT, -- JSON structure
  saved_filters TEXT, -- JSON structure
  compact_view BOOLEAN DEFAULT FALSE,
  mobile_density VARCHAR(20) DEFAULT 'default',
  theme_mode VARCHAR(20) DEFAULT 'mild',
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 5. Workspace Activity Timeline
CREATE TABLE IF NOT EXISTS workspace_activity (
  id BIGSERIAL PRIMARY KEY,
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  event_type VARCHAR(80) NOT NULL, -- e.g., 'onboarding_completed', 'snapshot_saved', 'pdf_exported'
  entity_type VARCHAR(80),
  entity_id VARCHAR(100),
  summary TEXT NOT NULL,
  metadata TEXT, -- JSON string
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 6. Shortlist Snapshots Table
CREATE TABLE IF NOT EXISTS shortlist_snapshots (
  id UUID PRIMARY KEY,
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  title VARCHAR(120) NOT NULL,
  source_group VARCHAR(40) DEFAULT 'primary',
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 7. Shortlist Snapshot Items
CREATE TABLE IF NOT EXISTS shortlist_snapshot_items (
  id BIGSERIAL PRIMARY KEY,
  snapshot_id UUID NOT NULL REFERENCES shortlist_snapshots(id) ON DELETE CASCADE,
  priority SMALLINT NOT NULL CHECK (priority BETWEEN 1 AND 300),
  college_code VARCHAR(10) NOT NULL,
  branch_code VARCHAR(10) NOT NULL,
  category VARCHAR(20) CHECK (category IN ('Safe', 'Moderate', 'Ambitious')),
  notes TEXT
);

-- 8. User College Preferences (Canonical Choice Filing Surface)
CREATE TABLE IF NOT EXISTS user_college_preferences (
  id BIGSERIAL PRIMARY KEY,
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  preference_group VARCHAR(40) DEFAULT 'primary',
  priority SMALLINT NOT NULL CHECK (priority BETWEEN 1 AND 300),
  college_code VARCHAR(10) NOT NULL,
  branch_code VARCHAR(10),
  category VARCHAR(20) CHECK (category IN ('Safe', 'Moderate', 'Ambitious')),
  category_override BOOLEAN DEFAULT FALSE,
  notes TEXT,
  added_from VARCHAR(20) DEFAULT 'manual',
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (workspace_id, preference_group, priority)
);

-- 9. TFC Locations Table
CREATE TABLE IF NOT EXISTS tfc_locations (
  tfc_id BIGSERIAL PRIMARY KEY,
   centre_name VARCHAR(200) NOT NULL,
  district VARCHAR(100) NOT NULL,
  address TEXT,
  phone VARCHAR(50),
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  google_maps_url TEXT
);

-- 11. Colleges Master Table
CREATE TABLE IF NOT EXISTS colleges (
  code VARCHAR(10) PRIMARY KEY,
  name VARCHAR(250) NOT NULL,
  district VARCHAR(100) NOT NULL,
  type VARCHAR(80) NOT NULL, -- e.g., 'Govt', 'Aided', 'Self-Finance'
  address TEXT,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  hostel_available BOOLEAN DEFAULT FALSE,
  transport_available BOOLEAN DEFAULT FALSE,
  website TEXT,
  is_autonomous BOOLEAN DEFAULT FALSE,
  nba_accredited BOOLEAN DEFAULT FALSE,
  coordinates_approximate BOOLEAN DEFAULT FALSE,
  nearest_railway_station VARCHAR(150),
  nearest_railway_distance_km DOUBLE PRECISION,
  fee_structure_annual INTEGER,
  placement_rate_pct DOUBLE PRECISION,
  avg_package_lpa DOUBLE PRECISION,
  details_raw TEXT -- Store complex nested raw data as JSON
);

-- 12. Branches Master Table
CREATE TABLE IF NOT EXISTS branches (
  code VARCHAR(10) PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  duration_years SMALLINT DEFAULT 4
);

-- 13. College-Branch Mapping
CREATE TABLE IF NOT EXISTS college_branches (
  id BIGSERIAL PRIMARY KEY,
  college_code VARCHAR(10) NOT NULL REFERENCES colleges(code) ON DELETE CASCADE,
  branch_code VARCHAR(10) NOT NULL REFERENCES branches(code) ON DELETE CASCADE,
  approved_intake INTEGER,
  year_starting INTEGER,
  nba_accredited BOOLEAN DEFAULT FALSE,
  UNIQUE (college_code, branch_code)
);

-- 14. Seat Matrix per Community
CREATE TABLE IF NOT EXISTS community_seats (
  id BIGSERIAL PRIMARY KEY,
  college_code VARCHAR(10) NOT NULL REFERENCES colleges(code) ON DELETE CASCADE,
  branch_code VARCHAR(10) NOT NULL REFERENCES branches(code) ON DELETE CASCADE,
  oc INTEGER DEFAULT 0,
  bc INTEGER DEFAULT 0,
  bcm INTEGER DEFAULT 0,
  mbc INTEGER DEFAULT 0,
  sc INTEGER DEFAULT 0,
  sca INTEGER DEFAULT 0,
  st INTEGER DEFAULT 0,
  total INTEGER DEFAULT 0,
  UNIQUE (college_code, branch_code)
);

-- 15. Historical and Active Cutoff Data Table
CREATE TABLE IF NOT EXISTS cutoff_data (
  id BIGSERIAL PRIMARY KEY,
  college_code VARCHAR(10) NOT NULL REFERENCES colleges(code) ON DELETE CASCADE,
  branch_code VARCHAR(10) NOT NULL REFERENCES branches(code) ON DELETE CASCADE,
  community VARCHAR(10) NOT NULL, -- e.g. OC, BC, BCM, MBC, SC, SCA, ST
  year SMALLINT NOT NULL,
  round_number SMALLINT NOT NULL,
  cutoff_mark DOUBLE PRECISION NOT NULL,
  cutoff_rank INTEGER,
  seats_allotted INTEGER DEFAULT 0
);

-- 16. Official TNEA Roll Numbers List (Interstitials verification)
CREATE TABLE IF NOT EXISTS tnea_roll_numbers (
  roll_number VARCHAR(30) PRIMARY KEY,
  student_name VARCHAR(150) NOT NULL,
  community VARCHAR(10) NOT NULL,
  district VARCHAR(100) NOT NULL,
  total_marks DOUBLE PRECISION NOT NULL,
  official_rank INTEGER NOT NULL,
  random_number VARCHAR(30),
  board VARCHAR(30)
);

-- 17. Counselling Round Dates Table
CREATE TABLE IF NOT EXISTS round_dates (
  round_number SMALLINT PRIMARY KEY,
  choice_start TIMESTAMPTZ,
  choice_end TIMESTAMPTZ,
  allotment TIMESTAMPTZ,
  confirm_start TIMESTAMPTZ,
  confirm_end TIMESTAMPTZ,
  reporting_end TIMESTAMPTZ
);

-- 18. Ingestion Audit Log
CREATE TABLE IF NOT EXISTS ingestion_audit_log (
  id BIGSERIAL PRIMARY KEY,
  dataset VARCHAR(80) NOT NULL,
  source TEXT,
  rows_inserted INTEGER DEFAULT 0,
  rows_updated INTEGER DEFAULT 0,
  rows_rejected INTEGER DEFAULT 0,
  started_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ,
  status VARCHAR(20) NOT NULL, -- 'running' | 'success' | 'failed'
  error_message TEXT
);

-- 20. Data Freshness Tracking
CREATE TABLE IF NOT EXISTS data_freshness (
  dataset_key VARCHAR(80) PRIMARY KEY,
  last_refreshed TIMESTAMPTZ NOT NULL,
  row_count INTEGER,
  notes TEXT
);

-- 20. Admin Manual Update Log
CREATE TABLE IF NOT EXISTS admin_update_log (
  id BIGSERIAL PRIMARY KEY,
  dataset VARCHAR(80) NOT NULL,
  source_url TEXT,
  rows_inserted INTEGER DEFAULT 0,
  rows_updated INTEGER DEFAULT 0,
  rows_rejected INTEGER DEFAULT 0,
  status VARCHAR(40) DEFAULT 'needs_review',
  summary TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 21. Scraping Automation Jobs
CREATE TABLE IF NOT EXISTS scraping_jobs (
  id BIGSERIAL PRIMARY KEY,
  dataset VARCHAR(80) NOT NULL,
  source_url TEXT,
  job_type VARCHAR(40) DEFAULT 'real_time_scraping',
  status VARCHAR(40) NOT NULL,
  row_count INTEGER DEFAULT 0,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 22. AI Guidance Audit Log
CREATE TABLE IF NOT EXISTS ai_guidance_log (
  id BIGSERIAL PRIMARY KEY,
  workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
  feature VARCHAR(40) NOT NULL,
  ai_available BOOLEAN DEFAULT FALSE,
  prompt_context TEXT,
  response_text TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 23. Payment Audit Log
CREATE TABLE IF NOT EXISTS payment_audit_log (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  event_type VARCHAR(40) NOT NULL, -- 'order_created', 'payment_attempted', 'verified', 'failed'
  razorpay_order VARCHAR(100),
  razorpay_payment VARCHAR(100),
  amount_paise INTEGER,
  error_message TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 23. Compare History
CREATE TABLE IF NOT EXISTS college_compare_history (
  id BIGSERIAL PRIMARY KEY,
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  session_name VARCHAR(120),
  college_codes TEXT NOT NULL, -- Comma-separated list of codes
  branch_codes TEXT, -- Comma-separated list of codes
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  saved BOOLEAN DEFAULT FALSE
);

-- 24. Rounds Checklist Tracker Progress
CREATE TABLE IF NOT EXISTS round_checklist_progress (
  id BIGSERIAL PRIMARY KEY,
  workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  round_number SMALLINT NOT NULL,
  step_1_completed BOOLEAN DEFAULT FALSE, -- e.g., 'View Current Seat'
  step_2_completed BOOLEAN DEFAULT FALSE, -- e.g., 'Review official consequence guide'
  step_3_completed BOOLEAN DEFAULT FALSE, -- e.g., 'Read Consequence Guide'
  step_4_completed BOOLEAN DEFAULT FALSE, -- e.g., 'Confirm Decision'
  updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (workspace_id, round_number)
);

-- 25. Device Fingerprints Abuse Layer
CREATE TABLE IF NOT EXISTS device_fingerprints (
  id BIGSERIAL PRIMARY KEY,
  fingerprint_hash VARCHAR(64) UNIQUE NOT NULL,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 26. Subscriptions Ledger Table
CREATE TABLE IF NOT EXISTS subscriptions (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
  expires_at TIMESTAMPTZ
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_user_prefs_workspace ON user_college_preferences(workspace_id);
CREATE INDEX IF NOT EXISTS idx_cutoff_coll_branch ON cutoff_data(college_code, branch_code);
CREATE INDEX IF NOT EXISTS idx_cutoff_community ON cutoff_data(community);
