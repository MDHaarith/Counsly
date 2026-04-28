"""Payment endpoints for Razorpay order creation and verification."""

import asyncio
import hmac
import logging
from hashlib import sha256

import razorpay
from fastapi import APIRouter, Depends, Header, Request
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from app.auth.middleware import get_current_user
from app.config import settings
from app.db.connection import get_db_connection
from app.db.queries import get_session_context
from app.errors import api_error, service_unavailable
from app.models import PaymentOrderResponse, PaymentVerifyRequest, PaymentVerifyResponse

router = APIRouter()
logger = logging.getLogger("counsly.security.payments")


def verify_razorpay_payment_signature(order_id: str, payment_id: str, signature: str, secret: str) -> bool:
    signed = f"{order_id}|{payment_id}".encode()
    expected = hmac.new(secret.encode(), signed, sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def verify_razorpay_webhook_signature(body: bytes, signature: str | None, secret: str) -> bool:
    if not signature:
        return False
    expected = hmac.new(secret.encode(), body, sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _razorpay_client() -> razorpay.Client:
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise service_unavailable("Razorpay is not configured", "RAZORPAY_NOT_CONFIGURED")
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))


@router.post("/order", response_model=PaymentOrderResponse)
async def create_order(user: dict = Depends(get_current_user)) -> PaymentOrderResponse:
    client = _razorpay_client()
    async with get_db_connection() as conn:
        context = await get_session_context(conn, user["app_user_id"])
        if not context:
            raise api_error(401, "Not authenticated", "NOT_AUTHENTICATED")
        order = await asyncio.to_thread(
            client.order.create,
            {
                "amount": settings.razorpay_amount_paise,
                "currency": "INR",
                "payment_capture": 1,
                "notes": {"workspace_id": str(context["workspace_id"]), "season_year": str(settings.season_year)},
            },
        )
        async with conn.cursor() as cur:
            await cur.execute(
                """
                INSERT INTO payment_orders (workspace_id, season_year, razorpay_order_id, amount_paise, currency, status)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (razorpay_order_id) DO NOTHING
                """,
                (str(context["workspace_id"]), settings.season_year, order["id"], settings.razorpay_amount_paise, "INR", "created"),
            )
            await cur.execute(
                """
                INSERT INTO payment_audit_log (workspace_id, event_type, event_payload)
                VALUES (%s, %s, %s)
                """,
                (str(context["workspace_id"]), "order_created", Jsonb(order)),
            )
        await conn.commit()
    return PaymentOrderResponse(order_id=order["id"], amount_paise=settings.razorpay_amount_paise, currency="INR", key_id=settings.razorpay_key_id or "")


@router.post("/verify", response_model=PaymentVerifyResponse)
async def verify_payment(payload: PaymentVerifyRequest, user: dict = Depends(get_current_user)) -> PaymentVerifyResponse:
    if not settings.razorpay_key_secret:
        raise service_unavailable("Razorpay is not configured", "RAZORPAY_NOT_CONFIGURED")
    if not verify_razorpay_payment_signature(
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
        settings.razorpay_key_secret,
    ):
        logger.warning("payment_signature_invalid order_id=%s payment_id=%s", payload.razorpay_order_id, payload.razorpay_payment_id)
        raise api_error(400, "Payment signature verification failed", "PAYMENT_SIGNATURE_INVALID")

    async with get_db_connection() as conn:
        context = await get_session_context(conn, user["app_user_id"])
        if not context:
            raise api_error(401, "Not authenticated", "NOT_AUTHENTICATED")
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(
                """
                UPDATE payment_orders SET
                    razorpay_payment_id = %s,
                    razorpay_signature = %s,
                    status = %s,
                    verified_at = now(),
                    updated_at = now()
                WHERE razorpay_order_id = %s AND workspace_id = %s
                RETURNING id
                """,
                (payload.razorpay_payment_id, payload.razorpay_signature, "captured", payload.razorpay_order_id, str(context["workspace_id"])),
            )
            order = await cur.fetchone()
            if not order:
                raise api_error(404, "Payment order not found", "PAYMENT_ORDER_NOT_FOUND")
            await cur.execute(
                """
                INSERT INTO subscriptions (workspace_id, season_year, plan_code, status, amount_paise, starts_at, ends_at, activated_at, source_payment_order_id)
                VALUES (%s, %s, %s, %s, %s, now(), NULL, now(), %s)
                ON CONFLICT (workspace_id, season_year) DO UPDATE SET
                    status = %s,
                    amount_paise = EXCLUDED.amount_paise,
                    activated_at = now(),
                    source_payment_order_id = EXCLUDED.source_payment_order_id,
                    updated_at = now()
                """,
                (str(context["workspace_id"]), settings.season_year, "full_access", "active", settings.razorpay_amount_paise, order["id"], "active"),
            )
            await cur.execute(
                """
                INSERT INTO payment_audit_log (workspace_id, payment_order_id, event_type, event_payload)
                VALUES (%s, %s, %s, %s)
                """,
                (str(context["workspace_id"]), order["id"], "payment_verified", Jsonb(payload.model_dump())),
            )
        await conn.commit()
    return PaymentVerifyResponse(active=True, status="active")


@router.post("/webhook")
async def razorpay_webhook(request: Request, x_razorpay_signature: str | None = Header(default=None)) -> dict[str, bool]:
    if not settings.razorpay_webhook_secret:
        raise service_unavailable("Razorpay webhook is not configured", "RAZORPAY_WEBHOOK_NOT_CONFIGURED")
    body = await request.body()
    if not verify_razorpay_webhook_signature(body, x_razorpay_signature, settings.razorpay_webhook_secret):
        logger.warning("razorpay_webhook_signature_invalid has_signature=%s", bool(x_razorpay_signature))
        raise api_error(400, "Webhook signature verification failed", "RAZORPAY_WEBHOOK_SIGNATURE_INVALID")

    payload = await request.json()
    event_type = str(payload.get("event") or "")
    payment = ((payload.get("payload") or {}).get("payment") or {}).get("entity") or {}
    order_id = payment.get("order_id")
    payment_id = payment.get("id")
    status = "captured" if event_type == "payment.captured" else payment.get("status", event_type or "received")

    async with get_db_connection() as conn:
        async with conn.cursor(row_factory=dict_row) as cur:
            payment_order = None
            if order_id:
                await cur.execute(
                    """
                    UPDATE payment_orders
                    SET razorpay_payment_id = COALESCE(razorpay_payment_id, %s),
                        status = %s,
                        verified_at = CASE WHEN %s = %s THEN COALESCE(verified_at, now()) ELSE verified_at END,
                        updated_at = now()
                    WHERE razorpay_order_id = %s
                    RETURNING id, workspace_id
                    """,
                    (payment_id, status, status, "captured", order_id),
                )
                payment_order = await cur.fetchone()
            workspace_id = payment_order["workspace_id"] if payment_order else None
            if payment_order and status == "captured":
                await cur.execute(
                    """
                    INSERT INTO subscriptions (workspace_id, season_year, plan_code, status, amount_paise, starts_at, ends_at, activated_at, source_payment_order_id)
                    VALUES (%s, %s, %s, %s, %s, now(), NULL, now(), %s)
                    ON CONFLICT (workspace_id, season_year) DO UPDATE SET
                        status = %s,
                        amount_paise = EXCLUDED.amount_paise,
                        activated_at = COALESCE(subscriptions.activated_at, now()),
                        source_payment_order_id = EXCLUDED.source_payment_order_id,
                        updated_at = now()
                    """,
                    (workspace_id, settings.season_year, "full_access", "active", settings.razorpay_amount_paise, payment_order["id"], "active"),
                )
            await cur.execute(
                """
                INSERT INTO payment_audit_log (workspace_id, payment_order_id, event_type, event_payload)
                VALUES (%s, %s, %s, %s)
                """,
                (workspace_id, payment_order["id"] if payment_order else None, f"webhook:{event_type or 'unknown'}", Jsonb(payload)),
            )
        await conn.commit()
    return {"ok": True}


@router.get("/ping")
async def payments_ping() -> dict:
    return {"module": "payments", "status": "ok"}
