"""Generate offline SQL for branches."""

from seed_utils import build_seed_sql, first_value


def main() -> None:
    build_seed_sql(
        "Generate SQL for branches.",
        "branches",
        [
            ("branch_code", lambda row: first_value(row, "branch_code", "code", "Branch Code")),
            ("branch_name", lambda row: first_value(row, "branch_name", "name", "Branch Name")),
            ("is_architecture", lambda row: first_value(row, "is_architecture", default=False)),
            ("keep", lambda row: first_value(row, "keep", default=True)),
            ("removal_reasons", lambda row: first_value(row, "removal_reasons")),
        ],
        "(branch_code)",
        "branches",
    )


if __name__ == "__main__":
    main()
