"""Payment endpoints — Razorpay order creation and verification."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/ping")
async def payments_ping() -> dict:
    return {"module": "payments", "status": "ok"}
