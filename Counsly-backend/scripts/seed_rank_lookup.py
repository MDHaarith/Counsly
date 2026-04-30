"""Generate offline SQL for aggregate-mark rank lookup rows."""

from seed_utils import build_seed_sql, first_value


def main() -> None:
    build_seed_sql(
        "Generate SQL for rank_lookup.",
        "rank_lookup",
        [
            ("aggregate_mark", lambda row: first_value(row, "aggregate_mark", "mark", "cutoff_mark")),
            ("rank_min", None),
            ("rank_max", None),
            ("confidence_label", None),
            ("sample_size", None),
            ("source_years", None),
            ("method_version", "offline-v1"),
            ("is_abstain", False),
        ],
        "(aggregate_mark)",
        "rank_lookup",
    )


if __name__ == "__main__":
    main()
