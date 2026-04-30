-- ============================================================
-- 004_rls_policies.sql
-- Defense-in-depth RLS policies for Counsly launch tables.
--
-- The app backend uses the Supabase service role / server DB connection and
-- keeps all user authorization in API queries. These policies prevent direct
-- anon/authenticated clients from reading private tables while preserving
-- public reference-data reads and service-role maintenance.
-- ============================================================

BEGIN;

-- Public reference/readiness data that may be exposed directly.
DROP POLICY IF EXISTS reference_select_all ON colleges;
CREATE POLICY reference_select_all ON colleges FOR SELECT USING (true);

DROP POLICY IF EXISTS reference_select_all ON branches;
CREATE POLICY reference_select_all ON branches FOR SELECT USING (true);

DROP POLICY IF EXISTS reference_select_all ON college_branches;
CREATE POLICY reference_select_all ON college_branches FOR SELECT USING (true);

DROP POLICY IF EXISTS reference_select_all ON community_seats;
CREATE POLICY reference_select_all ON community_seats FOR SELECT USING (true);

DROP POLICY IF EXISTS reference_select_all ON rank_lookup;
CREATE POLICY reference_select_all ON rank_lookup FOR SELECT USING (true);

DROP POLICY IF EXISTS reference_select_all ON tfc_locations;
CREATE POLICY reference_select_all ON tfc_locations FOR SELECT USING (true);

DROP POLICY IF EXISTS readiness_select_all ON app_config;
CREATE POLICY readiness_select_all ON app_config FOR SELECT USING (true);

DROP POLICY IF EXISTS readiness_select_all ON data_freshness;
CREATE POLICY readiness_select_all ON data_freshness FOR SELECT USING (true);

DROP POLICY IF EXISTS reference_select_all ON seat_matrix_current;
CREATE POLICY reference_select_all ON seat_matrix_current FOR SELECT USING (true);

DROP POLICY IF EXISTS reference_select_all ON seat_matrix_round_tables;
CREATE POLICY reference_select_all ON seat_matrix_round_tables FOR SELECT USING (true);

DROP POLICY IF EXISTS reference_select_all ON round_dates;
CREATE POLICY reference_select_all ON round_dates FOR SELECT USING (true);

-- Service-role write/read access for server-owned private and ops tables.
DROP POLICY IF EXISTS service_role_all ON auth_identities;
CREATE POLICY service_role_all ON auth_identities FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON app_users;
CREATE POLICY service_role_all ON app_users FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON workspaces;
CREATE POLICY service_role_all ON workspaces FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON student_profiles;
CREATE POLICY service_role_all ON student_profiles FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON onboarding_state;
CREATE POLICY service_role_all ON onboarding_state FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON user_sessions;
CREATE POLICY service_role_all ON user_sessions FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON payment_orders;
CREATE POLICY service_role_all ON payment_orders FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON subscriptions;
CREATE POLICY service_role_all ON subscriptions FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON payment_audit_log;
CREATE POLICY service_role_all ON payment_audit_log FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON user_college_preferences;
CREATE POLICY service_role_all ON user_college_preferences FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON shortlist_snapshots;
CREATE POLICY service_role_all ON shortlist_snapshots FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON shortlist_snapshot_items;
CREATE POLICY service_role_all ON shortlist_snapshot_items FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON college_compare_history;
CREATE POLICY service_role_all ON college_compare_history FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON college_compare_history_items;
CREATE POLICY service_role_all ON college_compare_history_items FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON user_activity_log;
CREATE POLICY service_role_all ON user_activity_log FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON ingestion_audit_log;
CREATE POLICY service_role_all ON ingestion_audit_log FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS reference_select_all ON cutoff_data;
DROP POLICY IF EXISTS service_role_all ON cutoff_data;
CREATE POLICY service_role_all ON cutoff_data FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON roll_number_claims;
CREATE POLICY service_role_all ON roll_number_claims FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON user_saved_filters;
CREATE POLICY service_role_all ON user_saved_filters FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON chat_threads;
CREATE POLICY service_role_all ON chat_threads FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON chat_messages;
CREATE POLICY service_role_all ON chat_messages FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON chat_usage_counters;
CREATE POLICY service_role_all ON chat_usage_counters FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Server-side data loaders keep write ownership for operational tables.
DROP POLICY IF EXISTS service_role_all ON app_config;
CREATE POLICY service_role_all ON app_config FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON data_freshness;
CREATE POLICY service_role_all ON data_freshness FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON seat_matrix_current;
CREATE POLICY service_role_all ON seat_matrix_current FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON seat_matrix_round_tables;
CREATE POLICY service_role_all ON seat_matrix_round_tables FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS reference_select_all ON tnea_roll_numbers;
DROP POLICY IF EXISTS service_role_all ON tnea_roll_numbers;
CREATE POLICY service_role_all ON tnea_roll_numbers FOR ALL TO service_role USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS service_role_all ON round_dates;
CREATE POLICY service_role_all ON round_dates FOR ALL TO service_role USING (true) WITH CHECK (true);

COMMIT;
