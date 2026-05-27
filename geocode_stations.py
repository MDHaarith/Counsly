#!/usr/bin/env python3
import sqlite3
import urllib.request
import urllib.parse
import json
import time
import sys

DB_PATH = "counsly.db"
USER_AGENT = "CounslyTransportGeocoder/1.0 (contact: support@counsly.com)"

# Tamil Nadu geographic boundary limits to avoid matching stations globally (e.g. Malaysia)
TAMIL_NADU_BOUNDS = {
    "min_lat": 8.0,
    "max_lat": 14.0,
    "min_lng": 75.0,
    "max_lng": 81.0
}

def is_within_bounds(lat, lon):
    return (TAMIL_NADU_BOUNDS["min_lat"] <= lat <= TAMIL_NADU_BOUNDS["max_lat"] and
            TAMIL_NADU_BOUNDS["min_lng"] <= lon <= TAMIL_NADU_BOUNDS["max_lng"])

def geocode_query(query):
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=1"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                print(f"  [HTTP Error] Status: {response.status}")
                return None
            data = json.loads(response.read().decode("utf-8"))
            if isinstance(data, list) and len(data) > 0:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                display_name = data[0].get("display_name", "")
                
                # Enforce Tamil Nadu bounds check
                if not is_within_bounds(lat, lon):
                    print(f"  [Bounds Rejected] Found: '{display_name}' @ ({lat}, {lon}) which is outside Tamil Nadu.")
                    return None
                    
                return lat, lon, display_name
    except Exception as e:
        print(f"  [Request Exception] {e}")
    return None

def get_candidate_queries(station_name):
    # Try different spelling modifications on the base name to catch spelling errors/variations
    names_to_try = [station_name]
    
    # 1. Handle common typo endings like PALLAVARM -> PALLAVARAM
    if station_name.upper().endswith("ARM"):
        names_to_try.append(station_name[:-3] + "ARAM")
    elif station_name.upper().endswith("RAM") and not station_name.upper().endswith("ARAM"):
        names_to_try.append(station_name[:-3] + "ARAM")
        
    # 2. Handle double consonant and double vowel variants
    for name in list(names_to_try):
        # Double consonants
        if "RR" in name.upper():
            names_to_try.append(name.upper().replace("RR", "R"))
        if "RY" in name.upper():
            names_to_try.append(name.upper().replace("RY", "RRY"))
        if "LL" in name.upper():
            names_to_try.append(name.upper().replace("LL", "L"))
        # Double vowels common in South Indian place names
        if "AA" in name.upper():
            names_to_try.append(name.upper().replace("AA", "A"))
        if "EE" in name.upper():
            names_to_try.append(name.upper().replace("EE", "E"))
        if "OO" in name.upper():
            names_to_try.append(name.upper().replace("OO", "O"))
            
    # Now build queries for each variation
    queries = []
    for name in names_to_try:
        queries.extend([
            f"{name} Railway Station, Tamil Nadu",
            f"{name} Railway Station",
            f"{name}, Tamil Nadu"
        ])
        
        # Check for "AND" splits
        if " AND " in name.upper():
            parts = [p.strip() for p in name.upper().split(" AND ")]
            for part in parts:
                if part:
                    queries.extend([
                        f"{part} Railway Station, Tamil Nadu",
                        f"{part} Railway Station"
                    ])
                    
        # Check for multi-word splits
        words = name.split()
        if len(words) > 1:
            for word in words:
                if len(word) > 3:
                    queries.extend([
                        f"{word} Railway Station, Tamil Nadu",
                        f"{word} Railway Station"
                    ])
                    
    # Deduplicate queries while preserving order
    seen = set()
    deduped_queries = []
    for q in queries:
        if q not in seen:
            seen.add(q)
            deduped_queries.append(q)
            
    return deduped_queries

def main():
    print("Connecting to database...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check schema first
    cursor.execute("PRAGMA table_info(colleges)")
    columns = [col[1] for col in cursor.fetchall()]
    if "nearest_railway_station_latitude" not in columns or "nearest_railway_station_longitude" not in columns:
        print("Error: nearest_railway_station_latitude or nearest_railway_station_longitude columns not found in database. Exiting.")
        sys.exit(1)
        
    # Get unique stations that need geocoding
    cursor.execute("""
        SELECT DISTINCT nearest_railway_station 
        FROM colleges 
        WHERE nearest_railway_station IS NOT NULL 
          AND nearest_railway_station != "" 
          AND (nearest_railway_station_latitude IS NULL OR nearest_railway_station_longitude IS NULL)
    """)
    stations = [row[0] for row in cursor.fetchall()]
    
    total = len(stations)
    print(f"Found {total} unique railway stations needing geocoding.")
    
    if total == 0:
        print("No stations need geocoding. All done!")
        conn.close()
        return

    success_count = 0
    fail_count = 0
    
    for i, station in enumerate(stations, 1):
        print(f"\n[{i}/{total}] Geocoding station: '{station}'")
        candidate_queries = get_candidate_queries(station)
        
        resolved = None
        for query in candidate_queries:
            print(f"  Trying query: '{query}'...")
            # Respect Nominatim policy: 1 second delay between requests
            time.sleep(1.0)
            result = geocode_query(query)
            if result:
                lat, lon, display_name = result
                print(f"  -> SUCCESS! Found: '{display_name}' @ ({lat}, {lon})")
                resolved = (lat, lon)
                break
            else:
                print("  -> Not found.")
                
        if resolved:
            lat, lon = resolved
            cursor.execute("""
                UPDATE colleges 
                SET nearest_railway_station_latitude = ?, 
                    nearest_railway_station_longitude = ? 
                WHERE nearest_railway_station = ?
            """, (lat, lon, station))
            conn.commit()
            success_count += 1
            print(f"  Updated database for all colleges nearest to '{station}'.")
        else:
            print(f"  -> FAILED to geocode: '{station}' after trying all variants.")
            fail_count += 1
            
    conn.close()
    print("\n========================================")
    print(f"Geocoding complete!")
    print(f"Successfully resolved: {success_count} stations.")
    print(f"Failed to resolve: {fail_count} stations.")
    print("========================================")

if __name__ == "__main__":
    main()
