import os
import json
import sqlite3

def sync():
    db_path = "/home/mdhaarith/Documents/Counsly/counsly.db"
    seed_colleges_path = "/home/mdhaarith/Documents/Counsly/supabase_db/seed_data/colleges/colleges.json"
    seed_geo_path = "/home/mdhaarith/Documents/Counsly/supabase_db/seed_data/colleges/college_geo.json"

    if not os.path.exists(db_path):
        print(f"Error: counsly.db not found at {db_path}")
        return

    if not os.path.exists(seed_colleges_path):
        print(f"Error: colleges.json not found at {seed_colleges_path}")
        return

    print("Connecting to SQLite database...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM colleges")
    db_colleges = cursor.fetchall()
    
    db_lookup = {str(row["code"]).strip(): dict(row) for row in db_colleges}
    print(f"Loaded {len(db_lookup)} colleges from counsly.db")

    print(f"Loading seed colleges from {seed_colleges_path}...")
    with open(seed_colleges_path, "r") as f:
        colleges_data = json.load(f)

    updated_count = 0
    new_geo_list = []

    for c in colleges_data:
        code = str(c["College_Code"]).strip()
        if code in db_lookup:
            db_c = db_lookup[code]
            
            # Map all new geocoded/distance fields into the JSON college object
            c["latitude"] = db_c.get("latitude")
            c["longitude"] = db_c.get("longitude")
            c["nearest_railway_station"] = db_c.get("nearest_railway_station")
            c["nearest_railway_distance_km"] = db_c.get("nearest_railway_distance_km")
            c["nearest_railway_station_latitude"] = db_c.get("nearest_railway_station_latitude")
            c["nearest_railway_station_longitude"] = db_c.get("nearest_railway_station_longitude")
            
            c["nearest_express_station"] = db_c.get("nearest_express_station")
            c["nearest_express_station_latitude"] = db_c.get("nearest_express_station_latitude")
            c["nearest_express_station_longitude"] = db_c.get("nearest_express_station_longitude")
            c["nearest_express_station_distance_km"] = db_c.get("nearest_express_station_distance_km")
            
            c["nearest_bus_station"] = db_c.get("nearest_bus_station")
            c["nearest_bus_station_latitude"] = db_c.get("nearest_bus_station_latitude")
            c["nearest_bus_station_longitude"] = db_c.get("nearest_bus_station_longitude")
            c["nearest_bus_station_distance_km"] = db_c.get("nearest_bus_station_distance_km")
            
            c["nearest_bus_stop"] = db_c.get("nearest_bus_stop")
            c["nearest_bus_stop_latitude"] = db_c.get("nearest_bus_stop_latitude")
            c["nearest_bus_stop_longitude"] = db_c.get("nearest_bus_stop_longitude")
            c["nearest_bus_stop_distance_km"] = db_c.get("nearest_bus_stop_distance_km")

            updated_count += 1

            # Populate college_geo.json lookup too
            if db_c.get("latitude") is not None and db_c.get("longitude") is not None:
                new_geo_list.append({
                    "original": c["College_Name"].strip(),
                    "latitude": db_c.get("latitude"),
                    "longitude": db_c.get("longitude")
                })

    print(f"Updated {updated_count} college items inside colleges.json memory buffer.")

    print(f"Saving updated seed colleges to {seed_colleges_path}...")
    with open(seed_colleges_path, "w") as f:
        json.dump(colleges_data, f, indent=2)

    print(f"Saving updated seed college geolocations to {seed_geo_path}...")
    with open(seed_geo_path, "w") as f:
        json.dump(new_geo_list, f, indent=2)

    conn.close()
    print("Geocode synchronization completed successfully!")

if __name__ == "__main__":
    sync()
