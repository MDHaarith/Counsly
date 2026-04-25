from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from app.config import settings, validate_runtime_settings
from app.db.connection import close_db_pool, open_db_pool
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    return {"status": "ok", "version": "0.1.0"}
