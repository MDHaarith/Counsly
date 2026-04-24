"""Explore endpoints — college search, filters, comparison."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def explore_ping() -> dict:
    return {"module": "explore", "status": "ok"}
