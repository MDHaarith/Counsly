import os
import re
from backend.main import app

def test_api_route_contract():
    # Locate api-routes.mjs in the workspace
    mjs_path = os.path.join(os.path.dirname(__file__), "../../frontend/lib/api-routes.mjs")
    assert os.path.exists(mjs_path), f"Frontend manifest not found at {mjs_path}"
    
    with open(mjs_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Extract all double-quoted paths starting with "/"
    endpoints = re.findall(r'"(/[a-zA-Z0-9_\-\/]+)"', content)
    assert len(endpoints) > 0, "No endpoints extracted from api-routes.mjs"
    
    # Extract all registered FastAPI paths
    registered_paths = {route.path for route in app.routes}
    
    for endpoint in endpoints:
        # 1. Check direct match
        if endpoint in registered_paths:
            continue
            
        # 2. Check if the endpoint serves as the base for a dynamic parameter route
        # e.g., /explore matches /explore/{college_code}
        # and /choices/ matches /choices/{pref_id}
        matched = False
        norm_endpoint = endpoint.rstrip("/")
        for reg_path in registered_paths:
            if reg_path.startswith(norm_endpoint):
                matched = True
                break
                
        assert matched, f"Contract drift: Frontend endpoint '{endpoint}' is not registered on the backend!"
