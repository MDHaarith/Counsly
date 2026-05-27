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

queries = [
    "Olakkur, Tamil Nadu",
    "Koyilvenni, Tamil Nadu",
    "Tiruchirappalli Junction",
    "Trichy Fort",
    "Tuticorin Melur",
    "Kuzhithurai",
    "Aloor, Tamil Nadu",
    "Thoppur, Tamil Nadu"
]

for q in queries:
    print(f"Query: {q}")
    res = test_geocode(q)
    if res:
        for idx, item in enumerate(res):
            print(f"  [{idx}] {item.get('display_name')} @ ({item.get('lat')}, {item.get('lon')}) class={item.get('class')} type={item.get('type')}")
    else:
        print("  No results found")
    print("-" * 50)
