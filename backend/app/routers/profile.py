"""Profile endpoints — student profile retrieval and updates."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def profile_ping() -> dict:
    return {"module": "profile", "status": "ok"}
