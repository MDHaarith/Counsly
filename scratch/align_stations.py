import sqlite3
import json
import math
import re

# Haversine distance helper
def haversine(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 2 * math.asin(math.sqrt(a)) * 6371

# Clean name to comparable string
def clean_name(name):
    if not name:
        return ""
    # remove punctuation and convert to lowercase
    name = name.lower()
    name = re.sub(r'[^a-z0-9\s]', '', name)
    # remove common suffixes/prefixes
    suffixes = ['railway', 'station', 'junction', 'jn', 'halt', 'stop', 'siding', 'military', 'road']
    words = name.split()
    filtered_words = [w for w in words if w not in suffixes]
    return " ".join(filtered_words).strip()

def main():
    # Load OSM stations
    with open("scratch/osm_stations.json", "r") as f:
        osm_elements = json.load(f)
        
    stations = []
    for el in osm_elements:
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if lat is None or lon is None:
            continue
        tags = el.get("tags", {})
        names = []
        for key in ["name", "name:en", "alt_name", "official_name"]:
            if key in tags:
                names.append(tags[key])
        if not names:
            continue
        primary_name = names[0]
        stations.append({
            "name": primary_name,
            "all_names": names,
            "cleaned_names": [clean_name(n) for n in names],
            "lat": float(lat),
            "lon": float(lon)
        })
        
    print(f"Loaded {len(stations)} OSM stations.")
    
    # Connect to database
    conn = sqlite3.connect("counsly.db")
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT code, name, latitude, longitude, nearest_railway_station,
               nearest_railway_station_latitude, nearest_railway_station_longitude
        FROM colleges
    """)
    colleges = cursor.fetchall()
    
    updates = []
    warnings = []
    
    for code, col_name, c_lat, c_lon, db_station, db_s_lat, db_s_lon in colleges:
        if c_lat is None or c_lon is None:
            continue
            
        db_station_cleaned = clean_name(db_station)
        
        # 1. First find candidate stations by name match
        best_station = None
        best_score = 0
        min_dist = float('inf')
        
        # If the db station name is empty, we search only by distance
        if db_station_cleaned and db_station != "-":
            for st in stations:
                # Calculate simple name match score (how many words match)
                db_words = set(db_station_cleaned.split())
                for st_clean in st["cleaned_names"]:
                    st_words = set(st_clean.split())
                    common = db_words.intersection(st_words)
                    if common:
                        # Score is size of common words / max of words
                        score = len(common) / max(len(db_words), len(st_words))
                        dist = haversine(c_lat, c_lon, st["lat"], st["lon"])
                        
                        # Only accept if station is reasonably close to the college (within 55km)
                        if dist < 55.0:
                            # We prefer higher score, then closer distance
                            if score > best_score or (score == best_score and dist < min_dist):
                                best_score = score
                                best_station = st
                                min_dist = dist
                                
        # 2. If no name match found within 55km, or the db_station is empty, find the physically closest station in Tamil Nadu
        if not best_station:
            for st in stations:
                dist = haversine(c_lat, c_lon, st["lat"], st["lon"])
                if dist < min_dist:
                    min_dist = dist
                    best_station = st
            
            # If the original name was non-empty and we found a closest one, log a warning
            if db_station and db_station != "-":
                warnings.append(f"No name match for '{db_station}' at college {code} ({col_name}). Mapping to closest station '{best_station['name']}' ({min_dist:.1f} km away)")
                
        # Calculate calculated distance
        calc_dist = haversine(c_lat, c_lon, best_station["lat"], best_station["lon"])
        
        # Record the update details
        updates.append({
            "code": code,
            "station_name": best_station["name"].upper(),
            "lat": best_station["lat"],
            "lon": best_station["lon"],
            "dist": calc_dist
        })
        
    print(f"\nProcessing {len(updates)} database updates...")
    
    # Apply updates to database
    for up in updates:
        cursor.execute("""
            UPDATE colleges
            SET nearest_railway_station = ?,
                nearest_railway_station_latitude = ?,
                nearest_railway_station_longitude = ?,
                nearest_railway_distance_km = ?
            WHERE code = ?
        """, (up["station_name"], up["lat"], up["lon"], up["dist"], up["code"]))
        
    conn.commit()
    conn.close()
    
    print("\n==========================================")
    print("Alignment completed successfully!")
    print(f"Total colleges updated: {len(updates)}")
    print(f"Total warnings/fallbacks: {len(warnings)}")
    print("==========================================")
    
    # Print first 10 warnings
    for w in warnings[:15]:
        print(f"WARNING: {w}")

if __name__ == '__main__':
    main()
