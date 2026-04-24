"""Choice-filling endpoints — preference list management."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def choices_ping() -> dict:
    return {"module": "choices", "status": "ok"}
