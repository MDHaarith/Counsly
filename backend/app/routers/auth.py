"""Auth endpoints — Google OAuth, session management."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def auth_ping() -> dict:
    return {"module": "auth", "status": "ok"}
