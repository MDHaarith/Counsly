import sqlite3
import math

def haversine(lat1, lon1, lat2, lon2):
    if None in (lat1, lon1, lat2, lon2):
        return None
    # convert decimal degrees to radians 
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    r = 6371 # Radius of earth in kilometers.
    return c * r

def check_distances():
    conn = sqlite3.connect('counsly.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT code, name, latitude, longitude, nearest_railway_station, 
               nearest_railway_station_latitude, nearest_railway_station_longitude,
               nearest_railway_distance_km
        FROM colleges
        WHERE latitude IS NOT NULL AND nearest_railway_station_latitude IS NOT NULL
    """)
    rows = cursor.fetchall()
    
    suspicious = []
    for row in rows:
        code, name, c_lat, c_lon, station, s_lat, s_lon, dist_km = row
        calc_dist = haversine(c_lat, c_lon, s_lat, s_lon)
        if calc_dist > 50.0:
            suspicious.append((code, name, c_lat, c_lon, station, s_lat, s_lon, calc_dist))
            
    print(f"Total suspicious colleges with station distance > 50km: {len(suspicious)}")
    print(f"{'Code':<6} | {'College Name':<35} | {'Station':<20} | {'Calc Dist':<10}")
    print("-" * 80)
    for code, name, c_lat, c_lon, station, s_lat, s_lon, calc_dist in suspicious:
        print(f"{code:<6} | {name[:35]:<35} | {station:<20} | {calc_dist:.2f} km")
        
    conn.close()

if __name__ == '__main__':
    check_distances()
