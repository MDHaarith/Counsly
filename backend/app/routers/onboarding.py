"""Onboarding endpoints — marks entry, step progression, eligibility."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def onboarding_ping() -> dict:
    return {"module": "onboarding", "status": "ok"}
