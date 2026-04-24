"""Recommendation endpoints — college/branch suggestions based on rank and marks."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def recommendations_ping() -> dict:
    return {"module": "recommendations", "status": "ok"}
