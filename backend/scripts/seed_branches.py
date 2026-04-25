"""Generate offline SQL for branches."""

from seed_utils import build_seed_sql, first_value


def main() -> None:
    build_seed_sql(
        "Generate SQL for branches.",
        "branches",
        [
            ("branch_code", lambda row: first_value(row, "branch_code", "code", "Branch Code")),
            ("branch_name", lambda row: first_value(row, "branch_name", "name", "Branch Name")),
            ("is_architecture", False),
            ("keep", True),
            ("removal_reasons", None),
        ],
        "(branch_code)",
    )


if __name__ == "__main__":
    main()
