from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

from app.routers import (
    auth,
    onboarding,
    recommendations,
    choices,
    explore,
    payments,
    profile,
    config,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup
    print("Counsly backend starting...")
    yield
    # Shutdown
    print("Counsly backend shutting down...")


app = FastAPI(
    title="Counsly API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(choices.router, prefix="/api/choices", tags=["choices"])
app.include_router(explore.router, prefix="/api/explore", tags=["explore"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(config.router, prefix="/api/config", tags=["config"])


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0"}
