from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.config import settings
from backend.database import get_db
from backend.models import AdminUpdateLog
from backend.schemas import AdminUpdateRequest, AdminUpdateResponse, OperationalStatusResponse
from backend.routes.auth import get_current_user
from backend.routes.scraping import default_scraping_jobs

router = APIRouter(prefix="/admin", tags=["admin"])


def build_admin_update_summary(dataset: str, source_url: str | None, rows_inserted: int, rows_updated: int, rows_rejected: int) -> dict:
    status = "needs_review" if rows_rejected else "applied"
    return {
        "dataset": dataset,
        "source_url": source_url,
        "rows_inserted": rows_inserted,
        "rows_updated": rows_updated,
        "rows_rejected": rows_rejected,
        "status": status,
        "summary": (
            f"Manual update for {dataset}: {rows_inserted} inserted, {rows_updated} updated, "
            f"{rows_rejected} rejected from {source_url or 'operator upload'}."
        ),
    }


@router.get("/status", response_model=OperationalStatusResponse)
def get_operational_status(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    updates = db.query(AdminUpdateLog).order_by(AdminUpdateLog.created_at.desc()).limit(8).all()
    admin_updates = [
        AdminUpdateResponse(
            dataset=item.dataset,
            source_url=item.source_url,
            rows_inserted=item.rows_inserted,
            rows_updated=item.rows_updated,
            rows_rejected=item.rows_rejected,
            status=item.status,
            summary=item.summary,
        )
        for item in updates
    ]
    if not admin_updates:
        admin_updates = [
            AdminUpdateResponse(**build_admin_update_summary("cutoff_data", None, 0, 0, 0)),
            AdminUpdateResponse(**build_admin_update_summary("seat_matrix", None, 0, 0, 0)),
        ]

    return OperationalStatusResponse(
        admin_updates=admin_updates,
        scraping_jobs=default_scraping_jobs(),
        ai={"configured": settings.AI_PROVIDER_CONFIGURED},
    )


@router.post("/updates", response_model=AdminUpdateResponse)
def create_admin_update(req: AdminUpdateRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    summary = build_admin_update_summary(
        dataset=req.dataset,
        source_url=req.source_url,
        rows_inserted=req.rows_inserted,
        rows_updated=req.rows_updated,
        rows_rejected=req.rows_rejected,
    )
    record = AdminUpdateLog(**summary)
    db.add(record)
    db.commit()
    return AdminUpdateResponse(**summary)
