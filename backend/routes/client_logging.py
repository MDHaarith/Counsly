from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ClientErrorLog
from backend.schemas import ClientErrorLogRequest, ClientErrorLogResponse
from backend.routes.rate_limiter import rate_limit

router = APIRouter(prefix="/logging", tags=["logging"])


def parse_reported_at(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def normalized_status(value):
    status = int(value or 0)
    return status if status >= 100 else None


import re

def scrub_sensitive_data(text: str | None) -> str | None:
    if not text:
        return text
    text = re.sub(r'(eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,})', '[JWT_REDACTED]', text)
    text = re.sub(r'(Bearer\s+[a-zA-Z0-9_\-\.\/]+)', 'Bearer [TOKEN_REDACTED]', text, flags=re.IGNORECASE)
    text = re.sub(r'(Authorization\s*:\s*[^\r\n,]+)', 'Authorization: [REDACTED]', text, flags=re.IGNORECASE)
    text = re.sub(r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', '[EMAIL_REDACTED]', text)
    text = re.sub(r'(roll_number\s*=\s*[a-zA-Z0-9]+)', 'roll_number=[REDACTED]', text, flags=re.IGNORECASE)
    text = re.sub(r'(mobile\s*=\s*[0-9]+)', 'mobile=[REDACTED]', text, flags=re.IGNORECASE)
    return text

def build_client_error_log(payload: dict) -> ClientErrorLog:
    return ClientErrorLog(
        endpoint=scrub_sensitive_data(payload.get("endpoint")),
        error_type=payload.get("error_type"),
        kind=payload.get("kind") or "client_js_error",
        message=scrub_sensitive_data(payload.get("message")),
        reported_at=parse_reported_at(payload.get("timestamp")),
        stack=scrub_sensitive_data(payload.get("stack")),
        status_code=normalized_status(payload.get("status")),
        user_id_hash=payload.get("user_id_hash"),
    )


@router.post("/client-error", response_model=ClientErrorLogResponse, dependencies=[Depends(rate_limit(5, 60))])
def create_client_error_log(req: ClientErrorLogRequest, db: Session = Depends(get_db)):
    record = build_client_error_log(req.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return ClientErrorLogResponse(accepted=True, id=record.id)
