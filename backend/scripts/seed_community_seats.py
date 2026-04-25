"""Generate offline SQL for community seat counts."""

from seed_utils import build_seed_sql, first_value


def main() -> None:
    build_seed_sql(
        "Generate SQL for community_seats.",
        "community_seats",
        [
            ("college_code", lambda row: first_value(row, "college_code", "college", "College Code")),
            ("branch_code", lambda row: first_value(row, "branch_code", "branch", "Branch Code")),
            ("oc", 0),
            ("bc", 0),
            ("bcm", 0),
            ("mbc", 0),
            ("sc", 0),
            ("sca", 0),
            ("st", 0),
            ("total", 0),
            ("source_file", None),
            ("extraction_date", None),
        ],
        "(college_code, branch_code)",
    )


if __name__ == "__main__":
    main()
