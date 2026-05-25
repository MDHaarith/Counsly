import hashlib
import hmac
from datetime import UTC, date, datetime, time

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import PaymentAuditLog, Subscription, User, WorkspaceActivity
from backend.routes.auth import get_current_user
from backend.schemas import PaymentOrderRequest, PaymentVerificationRequest, PaymentVerificationResponse, RazorpayOrderResponse

router = APIRouter(prefix="/payments", tags=["payments"])

PAYMENT_AMOUNT_PAISE = 14900
PAYMENT_CURRENCY = "INR"


def payment_order_belongs_to_user(db: Session, user_id: str, order_id: str) -> bool:
    return db.query(PaymentAuditLog).filter(
        PaymentAuditLog.user_id == user_id,
        PaymentAuditLog.event_type == "order_created",
        PaymentAuditLog.razorpay_order == order_id,
    ).first() is not None


def payment_event_already_processed(db: Session, order_id: str, payment_id: str) -> bool:
    return db.query(PaymentAuditLog).filter(
        PaymentAuditLog.event_type.in_(["verified", "activated"]),
        PaymentAuditLog.razorpay_order == order_id,
        PaymentAuditLog.razorpay_payment == payment_id,
    ).first() is not None


def build_payment_receipt(user_id: str, source: str | None = None) -> str:
    safe_source = "".join(ch for ch in (source or "full").lower() if ch.isalnum())[:12] or "full"
    safe_user = "".join(ch for ch in user_id if ch.isalnum())[:7] or "student"
    stamp = datetime.now(UTC).strftime("%m%d%H%M%S")
    return f"counsly_{safe_source}_{safe_user}_{stamp}"[:40]


def season_expiry_date(raw: str | None = None) -> date:
    try:
        return date.fromisoformat(raw or settings.SEASON_END_DATE)
    except ValueError:
        return date(2026, 9, 30)


def verify_razorpay_signature(order_id: str, payment_id: str, signature: str, secret: str) -> bool:
    message = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def audit_payment(db: Session, user: User, event_type: str, order_id: str | None = None, payment_id: str | None = None, error: str | None = None):
    db.add(PaymentAuditLog(
        user_id=user.id,
        event_type=event_type,
        razorpay_order=order_id,
        razorpay_payment=payment_id,
        amount_paise=PAYMENT_AMOUNT_PAISE,
        error_message=error,
    ))


@router.post("/order", response_model=RazorpayOrderResponse)
async def create_payment_order(req: PaymentOrderRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    receipt = build_payment_receipt(current_user.id, req.source)

    if settings.ALLOW_MOCK_PAYMENTS:
        order = {
            "id": f"order_mock_{receipt}",
            "amount": PAYMENT_AMOUNT_PAISE,
            "currency": PAYMENT_CURRENCY,
            "receipt": receipt,
            "key_id": settings.RAZORPAY_KEY_ID,
        }
        audit_payment(db, current_user, "order_created", order["id"])
        db.commit()
        return order

    payload = {
        "amount": PAYMENT_AMOUNT_PAISE,
        "currency": PAYMENT_CURRENCY,
        "receipt": receipt,
        "payment_capture": 1,
        "notes": {"feature": req.source or "full-access", "product": "counsly"},
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://api.razorpay.com/v1/orders",
                auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
                json=payload,
            )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        audit_payment(db, current_user, "failed", receipt, error=str(exc))
        db.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Razorpay order creation failed.") from exc

    audit_payment(db, current_user, "order_created", data["id"])
    db.commit()
    return {
        "id": data["id"],
        "amount": data["amount"],
        "currency": data["currency"],
        "receipt": data.get("receipt", receipt),
        "key_id": settings.RAZORPAY_KEY_ID,
    }


@router.post("/verify", response_model=PaymentVerificationResponse)
def verify_payment(req: PaymentVerificationRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not payment_order_belongs_to_user(db, current_user.id, req.razorpay_order_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Payment order does not belong to the current user.")

    if payment_event_already_processed(db, req.razorpay_order_id, req.razorpay_payment_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment has already been processed.")

    existing_owner = db.query(User).filter(User.razorpay_payment_id == req.razorpay_payment_id).first()
    if existing_owner and existing_owner.id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Payment is already attached to another account.")

    valid = verify_razorpay_signature(
        req.razorpay_order_id,
        req.razorpay_payment_id,
        req.razorpay_signature,
        settings.RAZORPAY_KEY_SECRET,
    )
    if not valid and settings.ALLOW_MOCK_PAYMENTS:
        valid = req.razorpay_signature == "mock_signature"

    if not valid:
        audit_payment(db, current_user, "failed", req.razorpay_order_id, req.razorpay_payment_id, "Invalid Razorpay signature")
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Payment signature verification failed.")

    expiry = season_expiry_date()
    current_user.subscription_active = True
    current_user.subscription_expiry = expiry
    current_user.razorpay_payment_id = req.razorpay_payment_id
    db.add(Subscription(
        user_id=current_user.id,
        status="active",
        expires_at=datetime.combine(expiry, time.max),
    ))
    if current_user.workspace:
        db.add(WorkspaceActivity(
            workspace_id=current_user.workspace.id,
            event_type="payment_completed",
            summary="Full Access payment verified and subscription activated.",
        ))
    audit_payment(db, current_user, "verified", req.razorpay_order_id, req.razorpay_payment_id)
    audit_payment(db, current_user, "activated", req.razorpay_order_id, req.razorpay_payment_id)
    db.commit()

    return PaymentVerificationResponse(
        success=True,
        message="Payment verified. Full Access is active.",
        subscription_active=True,
        subscription_expiry=expiry,
    )
