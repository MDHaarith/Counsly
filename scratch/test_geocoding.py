import urllib.request
import urllib.parse
import json
import time

USER_AGENT = "CounslyTransportGeocoder/1.0 (contact: support@counsly.com)"

def test_geocode(query):
    url = f"https://nominatim.openstreetmap.org/search?q={urllib.parse.quote(query)}&format=json&limit=3"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        time.sleep(1.0) # respect Nominatim 1s rate limit
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return data
    except Exception as e:
        print(f"Error: {e}")
    return None

# Let's test a few queries to see what they return
queries = [
    "Olakkur Railway Station, Tamil Nadu",
    "Koyilvenni Railway Station, Tamil Nadu",
    "Trichy Railway Station, Tamil Nadu",
    "Tuticorin Melur Railway Station, Tamil Nadu",
    "Kuzhithurai Railway Station, Tamil Nadu",
    "Aloor Railway Station, Kanyakumari, Tamil Nadu",
    "Arni Road Railway Station, Tamil Nadu"
]

for q in queries:
    print(f"Query: {q}")
    res = test_geocode(q)
    if res:
        for idx, item in enumerate(res):
            print(f"  [{idx}] {item.get('display_name')} @ ({item.get('lat')}, {item.get('lon')})")
    else:
        print("  No results found")
    print("-" * 50)
