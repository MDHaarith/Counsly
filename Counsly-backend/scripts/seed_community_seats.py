"""Generate offline SQL for community seat counts."""

from seed_utils import build_seed_sql, first_value


def main() -> None:
    build_seed_sql(
        "Generate SQL for community_seats.",
        "community_seats",
        [
            ("college_code", lambda row: first_value(row, "college_code", "college", "College Code")),
            ("branch_code", lambda row: first_value(row, "branch_code", "branch", "Branch Code")),
            ("oc", lambda row: first_value(row, "oc", default=0)),
            ("bc", lambda row: first_value(row, "bc", default=0)),
            ("bcm", lambda row: first_value(row, "bcm", default=0)),
            ("mbc", lambda row: first_value(row, "mbc", default=0)),
            ("sc", lambda row: first_value(row, "sc", default=0)),
            ("sca", lambda row: first_value(row, "sca", default=0)),
            ("st", lambda row: first_value(row, "st", default=0)),
            ("total", lambda row: first_value(row, "total", default=0)),
            ("source_file", lambda row: first_value(row, "source_file")),
            ("extraction_date", lambda row: first_value(row, "extraction_date")),
        ],
        "(college_code, branch_code)",
        "community_seats",
    )


if __name__ == "__main__":
    main()
