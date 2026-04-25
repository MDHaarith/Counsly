"""Generate offline SQL for TFC locations."""

from seed_utils import build_seed_sql, first_value


def main() -> None:
    build_seed_sql(
        "Generate SQL for tfc_locations.",
        "tfc_locations",
        [
            ("name", lambda row: first_value(row, "name", "centre_name")),
            ("district", lambda row: first_value(row, "district")),
            ("address", lambda row: first_value(row, "address", "full_address")),
            ("phone", lambda row: first_value(row, "phone")),
            ("latitude", lambda row: first_value(row, "latitude")),
            ("longitude", lambda row: first_value(row, "longitude")),
            ("maps_url", lambda row: first_value(row, "maps_url", "google_maps_url")),
            ("verified_at", None),
            ("source_file", lambda row: first_value(row, "source_file", default="supabase_db/seed_data/tfc_locations")),
        ],
        None,
        "tfc_locations",
    )


if __name__ == "__main__":
    main()
