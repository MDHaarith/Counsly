from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import User, WorkspaceActivity, WorkspaceSettings
from backend.routes.auth import get_current_user
from backend.schemas import WorkspaceSettingsResponse, WorkspaceSettingsUpdate

router = APIRouter(prefix="/workspace", tags=["workspace"])


def split_branch_defaults(branches: str | None) -> list[str]:
    return [branch.strip() for branch in (branches or "").split(",") if branch.strip()]


def _settings_for_user(current_user: User, db: Session) -> WorkspaceSettings:
    ws = current_user.workspace
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace environment not initialized")
    if ws.settings:
        return ws.settings

    settings = WorkspaceSettings(workspace_id=ws.id)
    db.add(settings)
    db.flush()
    return settings


def _response(settings: WorkspaceSettings) -> WorkspaceSettingsResponse:
    return WorkspaceSettingsResponse(
        default_district=settings.default_district,
        preferred_branches=split_branch_defaults(settings.preferred_branch_defaults),
        compact_view=settings.compact_view,
        mobile_density=settings.mobile_density or "default",
        theme_mode=settings.theme_mode or "mild",
        saved_filters=settings.saved_filters,
        phase_preferences=settings.phase_preferences,
    )


@router.get("/settings", response_model=WorkspaceSettingsResponse)
def get_workspace_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    settings = _settings_for_user(current_user, db)
    db.commit()
    return _response(settings)


@router.put("/settings", response_model=WorkspaceSettingsResponse)
def update_workspace_settings(
    req: WorkspaceSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = _settings_for_user(current_user, db)
    settings.default_district = req.default_district
    settings.preferred_branch_defaults = ",".join(req.preferred_branches)
    settings.compact_view = req.compact_view
    settings.mobile_density = req.mobile_density
    settings.theme_mode = req.theme_mode
    db.add(WorkspaceActivity(
        workspace_id=settings.workspace_id,
        event_type="workspace_settings_saved",
        summary="Updated workspace district, branch defaults, and display density.",
    ))
    db.commit()
    db.refresh(settings)
    return _response(settings)
