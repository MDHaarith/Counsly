-- Predicted closing ranks from ML model (replaces historical MAX(rank) in recommendations)
CREATE TABLE IF NOT EXISTS predicted_closing_ranks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    season_year int NOT NULL,
    round_number int NOT NULL DEFAULT 1,
    community_quota text NOT NULL CHECK (community_quota IN ('OC','BC','BCM','MBC','SC','SCA','ST')),
    college_code text NOT NULL,
    branch_code text NOT NULL,
    predicted_closing_rank int NOT NULL,
    prediction_lower int,
    prediction_upper int,
    confidence_label text NOT NULL DEFAULT 'Medium' CHECK (confidence_label IN ('High','Medium','Low')),
    model_version text NOT NULL,
    predicted_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (season_year, round_number, community_quota, college_code, branch_code)
);

CREATE INDEX IF NOT EXISTS idx_pcr_lookup ON predicted_closing_ranks (season_year, round_number, community_quota);

-- Predicted rank bands from ML model (replaces rank_lookup table for ML predictions)
CREATE TABLE IF NOT EXISTS predicted_rank_bands (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_mark numeric(8,4) NOT NULL,
    community_quota text NOT NULL CHECK (community_quota IN ('OC','BC','BCM','MBC','SC','SCA','ST')),
    predicted_rank_min int NOT NULL,
    predicted_rank_max int NOT NULL,
    predicted_total_students int NOT NULL,
    confidence_label text NOT NULL DEFAULT 'Medium' CHECK (confidence_label IN ('High','Medium','Low')),
    model_version text NOT NULL,
    predicted_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (aggregate_mark, community_quota)
);

CREATE INDEX IF NOT EXISTS idx_prb_lookup ON predicted_rank_bands (aggregate_mark, community_quota);
