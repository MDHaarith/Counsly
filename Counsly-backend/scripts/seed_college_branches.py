"""Generate offline SQL for college/branch offerings."""

from seed_utils import build_seed_sql, first_value


def main() -> None:
    build_seed_sql(
        "Generate SQL for college_branches.",
        "college_branches",
        [
            ("college_code", lambda row: first_value(row, "college_code", "college", "College Code")),
            ("branch_code", lambda row: first_value(row, "branch_code", "branch", "Branch Code")),
            ("branch_name", lambda row: first_value(row, "branch_name", "Branch Name")),
            ("active", True),
            ("source_file", None),
            ("extraction_date", None),
        ],
        "(college_code, branch_code)",
        "college_branches",
    )


if __name__ == "__main__":
    main()
