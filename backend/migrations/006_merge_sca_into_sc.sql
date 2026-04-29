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

DELETE FROM predicted_closing_ranks p
USING predicted_closing_ranks existing
WHERE p.community_quota = 'SCA'
  AND existing.community_quota = 'SC'
  AND existing.season_year = p.season_year
  AND existing.round_number = p.round_number
  AND existing.college_code = p.college_code
  AND existing.branch_code = p.branch_code;

UPDATE predicted_closing_ranks
SET community_quota = 'SC', predicted_at = now()
WHERE community_quota = 'SCA';

DELETE FROM predicted_rank_bands p
USING predicted_rank_bands existing
WHERE p.community_quota = 'SCA'
  AND existing.community_quota = 'SC'
  AND existing.aggregate_mark = p.aggregate_mark;

UPDATE predicted_rank_bands
SET community_quota = 'SC', predicted_at = now()
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

ALTER TABLE predicted_closing_ranks DROP CONSTRAINT IF EXISTS predicted_closing_ranks_community_quota_check;
ALTER TABLE predicted_closing_ranks
    ADD CONSTRAINT predicted_closing_ranks_community_quota_check
    CHECK (community_quota IN ('OC','BC','BCM','MBC','SC','ST'));

ALTER TABLE predicted_rank_bands DROP CONSTRAINT IF EXISTS predicted_rank_bands_community_quota_check;
ALTER TABLE predicted_rank_bands
    ADD CONSTRAINT predicted_rank_bands_community_quota_check
    CHECK (community_quota IN ('OC','BC','BCM','MBC','SC','ST'));
