-- Merge SCA into SC for the app-facing community taxonomy.
-- Raw source columns/values may still mention SCA, but runtime community_quota
-- values should be OC, BC, BCM, MBC, SC, or ST only.

UPDATE student_profiles
SET community_quota = 'SC', updated_at = now()
WHERE community_quota = 'SCA';

UPDATE cutoff_data
SET community_quota = 'SC', updated_at = now()
WHERE community_quota = 'SCA';

UPDATE tnea_roll_numbers
SET community_quota = 'SC', updated_at = now()
WHERE community_quota = 'SCA';

UPDATE community_seats
SET sc = sc + sca, sca = 0, total = oc + bc + bcm + mbc + sc + sca + st, updated_at = now()
WHERE sca > 0;

UPDATE seat_matrix_current
SET sc = sc + sca, sca = 0, total = oc + bc + bcm + mbc + sc + sca + st, updated_at = now()
WHERE sca > 0;

DO $$
DECLARE
    seat_table record;
BEGIN
    FOR seat_table IN
        SELECT table_name
        FROM seat_matrix_round_tables
        WHERE table_name ~ '^seat_matrix_2026_r[0-9]+$'
    LOOP
        EXECUTE format(
            'UPDATE %I SET sc = sc + sca, sca = 0, total = oc + bc + bcm + mbc + sc + sca + st, updated_at = now() WHERE sca > 0',
            seat_table.table_name
        );
    END LOOP;
END $$;

ALTER TABLE student_profiles DROP CONSTRAINT IF EXISTS chk_student_profiles_community;
ALTER TABLE student_profiles
    ADD CONSTRAINT chk_student_profiles_community
    CHECK (community_quota IS NULL OR community_quota IN ('OC','BC','BCM','MBC','SC','ST'));

ALTER TABLE cutoff_data DROP CONSTRAINT IF EXISTS chk_cutoff_community;
ALTER TABLE cutoff_data
    ADD CONSTRAINT chk_cutoff_community
    CHECK (community_quota IN ('OC','BC','BCM','MBC','SC','ST'));

ALTER TABLE tnea_roll_numbers DROP CONSTRAINT IF EXISTS chk_tnea_roll_numbers_community;
ALTER TABLE tnea_roll_numbers
    ADD CONSTRAINT chk_tnea_roll_numbers_community
    CHECK (community_quota IS NULL OR community_quota IN ('OC','BC','BCM','MBC','SC','ST'));
