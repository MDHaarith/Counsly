# Counsly — Database Schema

**Source:** Populated from Sections 3, 5, 7, 8, 10, 16, and 17  
**Last updated:** 25 April 2026

---

## Schema Rules

- Supabase PostgreSQL is the system of record for all product state.
- Student-owned product data is scoped by `workspace_id`. `auth_user_id` binds identity only; it is not the personal data ownership boundary.
- Use `uuid` primary keys by default. Keep stable natural keys only where they already exist and are truly canonical, such as `college_code`, `branch_code`, and `app_config.config_key`.
- Every mutable table must include `created_at timestamptz` and `updated_at timestamptz`.
- Every audit table is append-only. Audit rows are never updated in place.
- Preserve source-truth values in `source_*` columns when the app-facing normalized value differs from the raw source.
- App-facing community taxonomy is fixed to `OC`, `BC`, `BCM`, `MBC`, `SC`, `ST`. Raw values such as `MBCDNC`, `MBCV`, and `SCA` must be preserved, then normalized for app use; `SCA` maps to `SC`.
- `rank_lookup` is a curated derived table, not a raw-ingestion table.
- No automatic data deletion in v2.0. Archival states are explicit.

## Canonical Enums

| Domain | Allowed values | Notes |
| --- | --- | --- |
| `community_quota` | `OC`, `BC`, `BCM`, `MBC`, `SC`, `ST` | App-facing taxonomy |
| `workspace_kind` | `personal` | One PDE per user in v2.0 |
| `preference_group` | `wishlist`, `primary`, `pinned` | `primary` is the actual ordered choice list |
| `safety_category` | `safe`, `moderate`, `ambitious` | Stored in lowercase even if rendered as title case |
| `subscription_status` | `pending`, `active`, `expired`, `payment_failed`, `cancelled` | No refund flow in-app |
| `chat_role` | `system`, `assistant`, `user` | Transcript roles |
| `news_status` | `draft`, `active`, `archived` | Runtime admin controlled |
| `audit_status` | `started`, `success`, `failed`, `rejected` | Used in ingestion and admin audit logs |

## Identity And Access Tables

| Table | Purpose | PK / uniqueness | Required columns |
| --- | --- | --- | --- |
| `auth_identities` | External identity bridge for direct Google OAuth | `id uuid pk`, unique `auth_user_id`, unique `google_id`, unique `email` | `auth_user_id`, `provider`, `google_id`, `email`, `email_verified`, `display_name`, `avatar_url`, `last_login_at` |
| `app_users` | Internal app principal row | `id uuid pk`, unique `auth_identity_id`, unique `auth_user_id` | `auth_identity_id`, `auth_user_id`, `role`, `status`, `current_season_year` |
| `workspaces` | Personal Data Environment boundary | `id uuid pk`, unique `app_user_id` | `app_user_id`, `workspace_kind`, `display_name`, `season_year`, `archived_at` |
| `student_profiles` | Onboarding + canonical student facts | `id uuid pk`, unique `workspace_id` | `workspace_id`, `full_name`, `board`, `district`, `home_district`, `community_quota`, `maths_mark`, `physics_mark`, `chemistry_mark`, `cutoff_mark`, `expected_cutoff_mark`, `official_rank`, `official_community_rank`, `roll_number`, `roll_number_verified_at` |
| `onboarding_state` | Resume-exact-step state | `id uuid pk`, unique `workspace_id` | `workspace_id`, `current_step`, `is_complete`, `eligible`, `eligibility_reason`, `last_route`, `entered_phase`, `completed_at` |
| `user_sessions` | Server-side allowlist/revocation store for JWT cookies | `id uuid pk`, unique `jti` | `app_user_id`, `jti`, `token_hash`, `issued_at`, `expires_at`, `revoked_at` |
| `roll_number_claims` | One-account-per-roll enforcement | `id uuid pk`, unique `(season_year, roll_number)` | `workspace_id`, `season_year`, `roll_number`, `claim_status`, `verified_at`, `conflict_note` |

## Subscription And Payment Tables

| Table | Purpose | PK / uniqueness | Required columns |
| --- | --- | --- | --- |
| `subscriptions` | Paid entitlement for a season | `id uuid pk`, unique `(workspace_id, season_year)` | `workspace_id`, `season_year`, `plan_code`, `status`, `amount_paise`, `starts_at`, `ends_at`, `activated_at`, `source_payment_order_id` |
| `payment_orders` | Razorpay order/payment linkage | `id uuid pk`, unique `razorpay_order_id`, nullable unique `razorpay_payment_id` | `workspace_id`, `season_year`, `razorpay_order_id`, `razorpay_payment_id`, `razorpay_signature`, `amount_paise`, `currency`, `status`, `verified_at`, `failure_reason` |
| `payment_audit_log` | Append-only payment event log | `id uuid pk` | `workspace_id`, `payment_order_id`, `event_type`, `event_payload jsonb`, `created_at` |

## Workspace Product Tables

| Table | Purpose | PK / uniqueness | Required columns |
| --- | --- | --- | --- |
| `user_college_preferences` | Canonical preference store from FR-44 | `id uuid pk`, unique `(workspace_id, preference_group, college_code, branch_code)` | `workspace_id`, `preference_group`, `priority`, `college_code`, `branch_code`, `system_category`, `manual_category`, `notes`, `added_from`, `active` |
| `shortlist_snapshots` | Snapshot header rows | `id uuid pk` | `workspace_id`, `title`, `item_count`, `created_by`, `created_at` |
| `shortlist_snapshot_items` | Immutable rows captured per snapshot | `id uuid pk` | `snapshot_id`, `priority`, `college_code`, `branch_code`, `category`, `notes` |
| `college_compare_history` | Saved compare session metadata | `id uuid pk` | `workspace_id`, `title`, `created_from`, `created_at` |
| `college_compare_history_items` | Colleges/branches inside one compare session | `id uuid pk` | `compare_history_id`, `sort_order`, `college_code`, `branch_code` |
| `user_saved_filters` | Persisted recommendation/explore filters | `id uuid pk`, unique `(workspace_id, screen_name)` | `workspace_id`, `screen_name`, `filter_payload jsonb` |
| `user_activity_log` | Timeline/events inside a workspace | `id uuid pk` | `workspace_id`, `event_type`, `entity_type`, `entity_id`, `event_payload jsonb`, `created_at` |
| `chat_threads` | Per-workspace chat containers | `id uuid pk` | `workspace_id`, `title`, `archived`, `last_message_at` |
| `chat_messages` | Stored chat transcript | `id uuid pk` | `thread_id`, `role`, `content`, `token_estimate`, `grounding_payload jsonb`, `source_count`, `created_at` |
| `chat_usage_counters` | Free/paid usage meter per season | `id uuid pk`, unique `(workspace_id, season_year)` | `workspace_id`, `season_year`, `free_messages_used`, `paid_messages_used`, `welcome_message_sent`, `fingerprint_hash`, `last_message_at` |

## Reference Data Tables

| Table | Purpose | PK / uniqueness | Required columns |
| --- | --- | --- | --- |
| `colleges` | Canonical college master | natural PK `college_code` | `college_code`, `college_name`, `address`, `district`, `taluk`, `pincode`, `phone_fax`, `email`, `website`, `autonomous_status`, `minority_status`, `placement_record`, `hostel_boys`, `hostel_girls`, `transport_facilities`, `min_transport_charges`, `max_transport_charges`, `latitude`, `longitude`, `maps_url`, `is_architecture`, `raw_payload jsonb` |
| `branches` | Canonical branch master | natural PK `branch_code` | `branch_code`, `branch_name`, `is_architecture`, `keep`, `removal_reasons jsonb` |
| `college_branches` | College-to-branch mapping | `id uuid pk`, unique `(college_code, branch_code)` | `college_code`, `branch_code`, `branch_name`, `active`, `source_file`, `extraction_date` |
| `community_seats` | Historical quota-seat seed table retained from the original schema | `id uuid pk`, unique `(college_code, branch_code)` | `college_code`, `branch_code`, `oc`, `bc`, `bcm`, `mbc`, `sc`, `sca`, `st`, `total`, `source_file`, `extraction_date` |
| `seat_matrix_current` | Current 2026 choice-filling availability mirror. App hides college-branch rows with `total = 0`. | `id uuid pk`, unique `(college_code, branch_code)` | `college_code`, `branch_code`, `oc`, `bc`, `bcm`, `mbc`, `sc`, `sca`, `st`, `total`, `source_file`, `extraction_date` |
| `seat_matrix_round_tables` | Metadata registry for physical 2026 per-round seat-matrix tables | `id uuid pk`, unique `(season_year, round_number)`, unique `table_name` | `season_year`, `round_number`, `table_name`, `source_file`, `extraction_date`, `rows_loaded` |
| `seat_matrix_2026_rN` | Physical per-round 2026 seat-matrix table created by ingestion, e.g. `seat_matrix_2026_r1` | `id uuid pk`, unique `(college_code, branch_code)` | `college_code`, `branch_code`, `oc`, `bc`, `bcm`, `mbc`, `sc`, `sca`, `st`, `total`, `source_file`, `extraction_date` |
| `cutoff_data` | Historical allotment rows for recommendations and analytics | `id uuid pk` | `season_year`, `round_number`, `aggregate_mark`, `general_rank`, `community_quota`, `source_community_raw`, `college_code`, `branch_code`, `allotted_category`, `application_number`, `source_file` |
| `rank_lookup` | Pre-computed historical rank band lookup | PK `(aggregate_mark)` | `aggregate_mark`, `rank_min`, `rank_max`, `confidence_label`, `sample_size`, `source_years jsonb`, `method_version`, `is_abstain` |
| `tnea_roll_numbers` | Official rank-list rows and claim lookup | `id uuid pk`, unique `(season_year, application_number)`, nullable unique `(season_year, roll_number)` | `season_year`, `roll_number`, `application_number`, `general_rank`, `aggregate_mark`, `community_quota`, `source_community_raw`, `community_rank`, `candidate_name`, `date_of_birth`, `random_number`, `source_file` |
| `tfc_locations` | Facilitation centre master | `id uuid pk` | `name`, `district`, `address`, `phone`, `latitude`, `longitude`, `maps_url`, `verified_at`, `source_file` |

## Runtime And Audit Tables

| Table | Purpose | PK / uniqueness | Required columns |
| --- | --- | --- | --- |
| `app_config` | Runtime key-value store | natural PK `config_key` | `config_key`, `value_type`, `value_json`, `updated_by`, `updated_at` |
| `round_dates` | Counselling round schedule | `id uuid pk`, unique `(season_year, round_number)` | `season_year`, `round_number`, `choice_fill_start_at`, `choice_fill_end_at`, `allotment_at`, `confirm_end_at`, `report_end_at`, `is_active` |
| `news_items` | Runtime-managed news strip and links | `id uuid pk` | `title`, `summary`, `source_url`, `published_at`, `status`, `sort_order`, `created_by` |
| `admin_audit_log` | Telegram/admin write log | `id uuid pk` | `admin_identifier`, `command`, `target_key`, `previous_value jsonb`, `new_value jsonb`, `success`, `validation_error`, `created_at` |
| `ingestion_audit_log` | Ingestion lifecycle tracking | `id uuid pk` | `dataset_name`, `run_type`, `status`, `started_at`, `finished_at`, `source_reference`, `rows_seen`, `rows_loaded`, `report_path`, `error_message` |
| `data_freshness` | Last-known freshness per dataset | natural PK `dataset_name` | `dataset_name`, `last_success_at`, `last_source_at`, `freshness_status`, `source_reference`, `notes` |

## Required `app_config` Keys

- `TNEA_PHASE`
- `TOTAL_ROUNDS`
- `RANK_RELEASED`
- `ROLL_DATA_READY`
- `FREE_CHAT_LIMIT`
- `SEASON_END_DATE`
- `BROADCAST_ACTIVE`
- `BROADCAST_MESSAGE`

## Normalization Rules

- Keep raw source community values in `source_community_raw`.
- Normalize `MBCDNC` and `MBCV` into app-facing `MBC`, but do not overwrite raw-ingestion truth.
- Keep raw `sca` seat columns for traceability, but merge those seats into app-facing `SC` guidance and do not expose `SCA` as a separate student quota.
- Normalize geo columns to `latitude` and `longitude` in final tables even if source files differ.
- `college_code` and `branch_code` remain the only accepted natural foreign keys across reference tables.

## Minimum Indexes And Constraints

- `auth_identities(auth_user_id)`
- `auth_identities(google_id)`
- `workspaces(app_user_id)`
- `student_profiles(workspace_id)`
- `user_college_preferences(workspace_id, preference_group, priority)`
- `cutoff_data(season_year, round_number, community_quota, college_code, branch_code)`
- `rank_lookup(aggregate_mark)`
- `tnea_roll_numbers(season_year, roll_number)`
- `tnea_roll_numbers(season_year, application_number)`
- `news_items(status, published_at desc)`
- `round_dates(season_year, round_number)`

## Ownership And Access Rules

- Reference tables are read-only to the app client and writable only through backend/admin ingestion paths.
- Workspace tables are scoped by `workspace_id`; any direct client access must enforce that boundary with RLS.
- Payment, admin, and ingestion audit tables are backend/admin only.
- Chat grounding payloads, roll-number verification fields, and payment signatures must never be exposed to the client unfiltered.
- `workspace_id` is the canonical product boundary. `auth_user_id` remains an identity binding key only.

## Launch Migration And Seed Order

Apply migrations `001_initial_schema.sql`, `002_launch_schema_gaps.sql`, and `003_decimal_aggregate_marks.sql` together for launch. `003` is safe after an older `001/002` deployment and preserves decimal `aggregate_mark` values as `numeric(8,4)` in `cutoff_data`, `rank_lookup`, and `tnea_roll_numbers`.

Seed/load order:

1. `seed_colleges.py` for `colleges`; it maps extractor keys such as `College_Code` and merges `college_geo.json`.
2. `seed_branches.py`, `seed_college_branches.py`, and `seed_community_seats.py` for reference availability.
3. `load_cutoffs.py` for the 554K-row historical cutoff CSV.
4. `build_rank_lookup.py` from GRL CSV, then `load_rank_lookup.py` for rank bands.
5. `seed_tfc_locations.py` for facilitation centres.

Seed scripts update `data_freshness` to `verified` when they produce/load successful outputs, which is required for feature gates to open.
