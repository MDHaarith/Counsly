import time
from fastapi import Request, HTTPException, status
from collections import defaultdict
from typing import Dict, List

# Simple in-memory sliding window rate limiter
# Key: (ip, path) -> list of timestamps of requests
_request_history: Dict[tuple, List[float]] = defaultdict(list)
_last_cleanup = 0.0
CLEANUP_INTERVAL = 300.0  # 5 minutes

def rate_limit(requests: int, window_seconds: int):
    async def dependency(request: Request):
        global _last_cleanup
        # Resolve client IP address (supporting reverse proxy headers like X-Forwarded-For)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
            
        path = request.url.path
        key = (ip, path)
        
        now = time.time()
        
        # Periodic global cleanup of all expired keys to prevent memory leaks
        if now - _last_cleanup > CLEANUP_INTERVAL:
            _last_cleanup = now
            for k in list(_request_history.keys()):
                timestamps_k = _request_history[k]
                while timestamps_k and timestamps_k[0] < now - 600.0:
                    timestamps_k.pop(0)
                if not timestamps_k:
                    _request_history.pop(k, None)

        # Clean up old timestamps outside the window
        timestamps = _request_history[key]
        while timestamps and timestamps[0] < now - window_seconds:
            timestamps.pop(0)
            
        if len(timestamps) >= requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )
            
        timestamps.append(now)
    return dependency

