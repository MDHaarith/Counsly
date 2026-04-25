from collections.abc import AsyncGenerator
from collections import defaultdict, deque
from contextlib import asynccontextmanager
import logging
from time import monotonic

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings, validate_runtime_settings
from app.db.connection import close_db_pool, get_db_connection, open_db_pool
from app.routers import auth, choices, config, explore, onboarding, payments, profile, recommendations


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    validate_runtime_settings()
    await open_db_pool()
    print("Counsly backend starting...")
    yield
    await close_db_pool()
    print("Counsly backend shutting down...")


app = FastAPI(title="Counsly API", version="0.1.0", lifespan=lifespan)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("counsly.api")
_rate_window_seconds = 60
_rate_limit = 120
_rate_buckets: dict[str, deque[float]] = defaultdict(deque)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
)


@app.middleware("http")
async def request_logging_and_rate_limit(request: Request, call_next):
    started = monotonic()
    client = request.client.host if request.client else "unknown"
    key = f"{client}:{request.url.path}"
    now = monotonic()
    bucket = _rate_buckets[key]
    while bucket and bucket[0] <= now - _rate_window_seconds:
        bucket.popleft()
    if len(bucket) >= _rate_limit:
        return JSONResponse(status_code=429, content={"error": "Too many requests", "code": "RATE_LIMITED"})
    bucket.append(now)

    response = await call_next(request)
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    logger.info(
        "request_complete method=%s path=%s status=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        int((monotonic() - started) * 1000),
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "error" in exc.detail and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": str(exc.detail), "code": "HTTP_ERROR"})


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(choices.router, prefix="/api/choices", tags=["choices"])
app.include_router(explore.router, prefix="/api/explore", tags=["explore"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(config.router, prefix="/api/config", tags=["config"])


@app.get("/")
async def frontend_root_redirect() -> RedirectResponse:
    return RedirectResponse(settings.frontend_url)


@app.get("/login")
async def frontend_login_redirect() -> RedirectResponse:
    return RedirectResponse(f"{settings.frontend_url}/login")


@app.get("/dashboard")
async def frontend_dashboard_redirect() -> RedirectResponse:
    return RedirectResponse(f"{settings.frontend_url}/dashboard")


@app.get("/health")
async def health() -> dict:
    async with get_db_connection() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT 1")
            await cur.fetchone()
    return {"status": "ok", "version": "0.1.0", "database": "ok"}
