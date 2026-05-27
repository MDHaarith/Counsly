import urllib.request
import urllib.parse
import json
import time

def fetch_overpass_stations():
    # Overpass API URL
    url = "https://overpass-api.de/api/interpreter"
    
    # Query to fetch all railway stations and halts in Tamil Nadu area
    query = """
    [out:json][timeout:60];
    area["ISO3166-2"="IN-TN"]->.searchArea;
    (
      nwr["railway"="station"](area.searchArea);
      nwr["railway"="halt"](area.searchArea);
    );
    out center;
    """
    
    headers = {
        "User-Agent": "CounslyTransportGeocoder/1.0 (contact: support@counsly.com)",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers)
    
    print("Sending request to Overpass API...")
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            if response.status == 200:
                res_data = json.loads(response.read().decode("utf-8"))
                elements = res_data.get("elements", [])
                print(f"Success! Found {len(elements)} railway stations/halts in Tamil Nadu.")
                
                # Print the first 10 for inspection
                for el in elements[:10]:
                    tags = el.get("tags", {})
                    name = tags.get("name", tags.get("name:en", "Unnamed"))
                    lat = el.get("lat") or el.get("center", {}).get("lat")
                    lon = el.get("lon") or el.get("center", {}).get("lon")
                    print(f"  - {name} @ ({lat}, {lon})")
                    
                # Save to a file
                with open("scratch/osm_stations.json", "w") as f:
                    json.dump(elements, f, indent=2)
                print("Saved all stations to scratch/osm_stations.json")
            else:
                print(f"Error: HTTP Status {response.status}")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == '__main__':
    fetch_overpass_stations()
