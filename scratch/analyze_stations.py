import sqlite3

def analyze():
    conn = sqlite3.connect('counsly.db')
    cursor = conn.cursor()
    
    # Let's list all unique stations, count of colleges, and current coordinates
    cursor.execute("""
        SELECT nearest_railway_station, COUNT(*), nearest_railway_station_latitude, nearest_railway_station_longitude
        FROM colleges
        WHERE nearest_railway_station IS NOT NULL AND nearest_railway_station != ""
        GROUP BY nearest_railway_station
        ORDER BY COUNT(*) DESC
    """)
    rows = cursor.fetchall()
    
    print(f"Total unique railway stations in use: {len(rows)}")
    print(f"{'Station Name':<40} | {'Colleges':<8} | {'Latitude':<12} | {'Longitude':<12}")
    print("-" * 80)
    for row in rows[:50]:
        station, count, lat, lon = row
        lat_str = f"{lat:.6f}" if lat is not None else "None"
        lon_str = f"{lon:.6f}" if lon is not None else "None"
        print(f"{station:<40} | {count:<8} | {lat_str:<12} | {lon_str:<12}")
        
    conn.close()

if __name__ == '__main__':
    analyze()
