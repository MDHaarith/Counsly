"""Generate offline SQL for the colleges reference table."""

from pathlib import Path
from typing import Any

from seed_utils import first_value, load_rows, normalize_key, parse_args, render_freshness_update, render_insert, write_sql


DEFAULT_GEO = Path(__file__).resolve().parents[2] / "supabase_db" / "seed_data" / "colleges" / "college_geo.json"


def truthy(value: Any) -> bool | None:
    if value in (None, ""):
        return None
    return str(value).strip().lower() in {"yes", "true", "1", "permanent", "rental", "available"}


def geo_key(value: Any) -> str:
    return normalize_key(str(value or ""))


def geo_index(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    rows = load_rows(path)
    return {geo_key(first_value(row, "original")): row for row in rows if first_value(row, "original")}


def project_college(row: dict[str, Any], geo_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    name = first_value(row, "college_name", "College_Name", "name")
    geo = geo_rows.get(geo_key(name), {})
    return {
        "college_code": str(first_value(row, "college_code", "College_Code", "code")),
        "college_name": name,
        "address": first_value(row, "address", "Address"),
        "district": first_value(row, "district", "District"),
        "taluk": first_value(row, "taluk", "Taluk"),
        "pincode": first_value(row, "pincode", "Pincode"),
        "phone_fax": first_value(row, "phone_fax", "Phone_Fax"),
        "email": first_value(row, "email", "email_id", "Email-ID"),
        "website": first_value(row, "website", "Website"),
        "autonomous_status": first_value(row, "autonomous_status", "Autonomous_Status"),
        "minority_status": first_value(row, "minority_status", "Minority_Status"),
        "placement_record": first_value(row, "placement_record", "Placement_Record"),
        "hostel_boys": truthy(first_value(row, "hostel_boys", "Hostel_Boys_Permanent_or_Rental")),
        "hostel_girls": truthy(first_value(row, "hostel_girls", "Hostel_Girls_Permanent_or_Rental")),
        "transport_facilities": truthy(first_value(row, "transport_facilities", "Transport_Facilities")),
        "min_transport_charges": first_value(row, "min_transport_charges", "Min_Transport_Charges"),
        "max_transport_charges": first_value(row, "max_transport_charges", "Max_Transport_Charges"),
        "latitude": first_value(geo, "latitude"),
        "longitude": first_value(geo, "longitude"),
        "maps_url": first_value(geo, "maps_url"),
        "is_architecture": False,
        "raw_payload": row,
    }


def main() -> None:
    args = parse_args("Generate SQL for colleges.")
    if not args.source:
        raise SystemExit("source JSON path is required")
    geo_rows = geo_index(DEFAULT_GEO)
    rows = [project_college(row, geo_rows) for row in load_rows(args.source, args.limit)]
    sql = render_insert("colleges", list(rows[0].keys()) if rows else [], rows, "(college_code)")
    sql += "\n" + render_freshness_update("colleges", str(args.source), len(rows))
    write_sql(sql, args.out)


if __name__ == "__main__":
    main()
