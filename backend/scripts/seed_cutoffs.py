"""Generate offline SQL for historical cutoff rows."""

from seed_utils import build_seed_sql, first_value, normalize_community


def main() -> None:
    build_seed_sql(
        "Generate SQL for cutoff_data.",
        "cutoff_data",
        [
            ("season_year", lambda row: first_value(row, "season_year", "year")),
            ("round_number", lambda row: first_value(row, "round_number", "round", default=1)),
            ("aggregate_mark", lambda row: first_value(row, "aggregate_mark", "aggregate mark", "mark", "aggregate")),
            ("general_rank", lambda row: first_value(row, "general_rank", "rank")),
            ("community_quota", lambda row: normalize_community(first_value(row, "community_quota", "community"))),
            ("source_community_raw", lambda row: first_value(row, "source_community_raw", "community")),
            ("college_code", lambda row: first_value(row, "college_code", "college")),
            ("branch_code", lambda row: first_value(row, "branch_code", "branch")),
            ("allotted_category", None),
            ("application_number", lambda row: first_value(row, "application_number", "application number")),
            ("source_file", None),
        ],
        None,
        "cutoff_data",
    )


if __name__ == "__main__":
    main()
