"""Generate offline SQL for app_config defaults."""

from seed_utils import parse_args, render_insert, write_sql

DEFAULTS = [
    {"config_key": "ROLL_DATA_READY", "value_json": "false", "updated_by": "seed"},
    {"config_key": "RANK_LOOKUP_READY", "value_json": "false", "updated_by": "seed"},
]


def main() -> None:
    args = parse_args("Generate SQL for app_config defaults.")
    sql = render_insert("app_config", ["config_key", "value_json", "updated_by"], DEFAULTS, "(config_key)")
    write_sql(sql, args.out)


if __name__ == "__main__":
    main()
