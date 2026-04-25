"""Generate offline SQL for the colleges reference table."""

from seed_utils import build_seed_sql, first_value


def main() -> None:
    build_seed_sql(
        "Generate SQL for colleges.",
        "colleges",
        [
            ("college_code", lambda row: first_value(row, "college_code", "code", "College Code")),
            ("college_name", lambda row: first_value(row, "college_name", "name", "College Name")),
            ("address", None),
            ("district", None),
            ("taluk", None),
            ("pincode", None),
            ("phone_fax", None),
            ("email", None),
            ("website", None),
            ("autonomous_status", None),
            ("minority_status", None),
            ("placement_record", None),
            ("hostel_boys", False),
            ("hostel_girls", False),
            ("transport_facilities", False),
            ("min_transport_charges", None),
            ("max_transport_charges", None),
            ("latitude", None),
            ("longitude", None),
            ("maps_url", None),
            ("is_architecture", False),
            ("raw_payload", lambda row: row),
        ],
        "(college_code)",
    )


if __name__ == "__main__":
    main()
