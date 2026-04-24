"""App config endpoints — runtime configuration for the client."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def config_ping() -> dict:
    return {"module": "config", "status": "ok"}
