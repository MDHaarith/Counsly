"""Choice-filing endpoints for the primary ordered preference list."""

from fastapi import APIRouter, Depends

from app.auth.middleware import get_current_user
from app.db.connection import get_db_connection
from app.db.queries import add_choice, get_session_context, list_choices, move_choice, remove_choice, update_choice
from app.errors import api_error
from app.models import ChoiceCreateRequest, ChoiceMoveRequest, ChoiceUpdateRequest, ChoicesEnvelope

router = APIRouter()


async def _choice_context(conn, app_user_id: str):
    context = await get_session_context(conn, app_user_id)
    if not context:
        raise api_error(401, "Not authenticated", "NOT_AUTHENTICATED")
    return str(context["workspace_id"]), bool(context["paid"])


@router.get("/ping")
async def choices_ping() -> dict:
    return {"module": "choices", "status": "ok"}


@router.get("", response_model=ChoicesEnvelope)
async def get_choices(user: dict = Depends(get_current_user)) -> ChoicesEnvelope:
    async with get_db_connection() as conn:
        workspace_id, paid = await _choice_context(conn, user["app_user_id"])
        payload = await list_choices(conn, workspace_id, paid)
    return ChoicesEnvelope(**payload)


@router.post("", response_model=ChoicesEnvelope)
async def post_choice(payload: ChoiceCreateRequest, user: dict = Depends(get_current_user)) -> ChoicesEnvelope:
    async with get_db_connection() as conn:
        workspace_id, paid = await _choice_context(conn, user["app_user_id"])
        try:
            result = await add_choice(conn, workspace_id, paid, payload.model_dump())
        except ValueError as exc:
            if str(exc) == "choice unavailable":
                raise api_error(409, "This college and branch has no available seats in the active seat matrix", "CHOICE_UNAVAILABLE") from exc
            if str(exc) == "ineligible":
                raise api_error(403, "Choice filing is locked because the entered cutoff is below the eligibility threshold", "INELIGIBLE") from exc
            raise api_error(403, "Choice limit reached for your plan", "PLAN_LIMIT") from exc
    return ChoicesEnvelope(**result)


@router.patch("/{choice_id}", response_model=ChoicesEnvelope)
async def patch_choice(choice_id: str, payload: ChoiceUpdateRequest, user: dict = Depends(get_current_user)) -> ChoicesEnvelope:
    async with get_db_connection() as conn:
        workspace_id, paid = await _choice_context(conn, user["app_user_id"])
        result = await update_choice(conn, workspace_id, paid, choice_id, payload.model_dump())
    return ChoicesEnvelope(**result)


@router.post("/{choice_id}/move", response_model=ChoicesEnvelope)
async def post_move(choice_id: str, payload: ChoiceMoveRequest, user: dict = Depends(get_current_user)) -> ChoicesEnvelope:
    async with get_db_connection() as conn:
        workspace_id, paid = await _choice_context(conn, user["app_user_id"])
        result = await move_choice(conn, workspace_id, paid, choice_id, payload.priority)
    return ChoicesEnvelope(**result)


@router.delete("/{choice_id}", response_model=ChoicesEnvelope)
async def delete_choice(choice_id: str, user: dict = Depends(get_current_user)) -> ChoicesEnvelope:
    async with get_db_connection() as conn:
        workspace_id, paid = await _choice_context(conn, user["app_user_id"])
        result = await remove_choice(conn, workspace_id, paid, choice_id)
    return ChoicesEnvelope(**result)
