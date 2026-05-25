from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from backend.database import get_db
from backend.models import User, WorkspaceActivity
from backend.routes.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/")
def get_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialized")

    activities = (
        db.query(WorkspaceActivity)
        .filter(WorkspaceActivity.workspace_id == ws.id)
        .order_by(WorkspaceActivity.created_at.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "id": a.id,
            "event_type": a.event_type,
            "summary": a.summary,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "read": False,
        }
        for a in activities
    ]


@router.get("/unread-count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialized")

    count = (
        db.query(WorkspaceActivity)
        .filter(WorkspaceActivity.workspace_id == ws.id)
        .count()
    )

    return {"count": count}


@router.post("/{id}/dismiss")
def dismiss_notification(
    id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not initialized")

    # No-op: WorkspaceActivity does not have a read field yet.
    # The activity is verified to belong to the current workspace.
    activity = (
        db.query(WorkspaceActivity)
        .filter(
            WorkspaceActivity.id == id,
            WorkspaceActivity.workspace_id == ws.id,
        )
        .first()
    )

    if not activity:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    return {"dismissed": True}