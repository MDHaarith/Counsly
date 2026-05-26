from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ClientErrorLog
from backend.schemas import ClientErrorLogRequest, ClientErrorLogResponse

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


def build_client_error_log(payload: dict) -> ClientErrorLog:
    return ClientErrorLog(
        endpoint=payload.get("endpoint"),
        error_type=payload.get("error_type"),
        kind=payload.get("kind") or "client_js_error",
        message=payload.get("message"),
        reported_at=parse_reported_at(payload.get("timestamp")),
        stack=payload.get("stack"),
        status_code=normalized_status(payload.get("status")),
        user_id_hash=payload.get("user_id_hash"),
    )


@router.post("/client-error", response_model=ClientErrorLogResponse)
def create_client_error_log(req: ClientErrorLogRequest, db: Session = Depends(get_db)):
    record = build_client_error_log(req.model_dump())
    db.add(record)
    db.commit()
    db.refresh(record)
    return ClientErrorLogResponse(accepted=True, id=record.id)
