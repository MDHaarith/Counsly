-- ============================================================
-- 003_decimal_aggregate_marks.sql
-- Preserve decimal aggregate marks from historical TNEA data.
-- Safe to run after 001/002 if they were applied before this fix.
-- ============================================================

BEGIN;

ALTER TABLE IF EXISTS cutoff_data
    ALTER COLUMN aggregate_mark TYPE NUMERIC(8,4)
    USING aggregate_mark::NUMERIC(8,4);

ALTER TABLE IF EXISTS rank_lookup
    ALTER COLUMN aggregate_mark TYPE NUMERIC(8,4)
    USING aggregate_mark::NUMERIC(8,4);

ALTER TABLE IF EXISTS tnea_roll_numbers
    ALTER COLUMN aggregate_mark TYPE NUMERIC(8,4)
    USING aggregate_mark::NUMERIC(8,4);

COMMIT;
