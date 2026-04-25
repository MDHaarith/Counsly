"""Explore endpoints for college search and overview details."""

from fastapi import APIRouter, Depends, Query

from app.auth.middleware import get_current_user
from app.db.connection import get_db_connection
from app.db.queries import fetch_college_detail, search_colleges
from app.errors import api_error
from app.models import CollegeDetailResponse, ExploreEnvelope

router = APIRouter()


@router.get("/ping")
async def explore_ping() -> dict:
    return {"module": "explore", "status": "ok"}


@router.get("", response_model=ExploreEnvelope)
async def get_explore(
    q: str | None = Query(default=None, max_length=80),
    district: str | None = Query(default=None, max_length=80),
    user: dict = Depends(get_current_user),
) -> ExploreEnvelope:
    async with get_db_connection() as conn:
        payload = await search_colleges(conn, q, district)
    return ExploreEnvelope(**payload)


@router.get("/{college_code}", response_model=CollegeDetailResponse)
async def get_college_detail(college_code: str, user: dict = Depends(get_current_user)) -> CollegeDetailResponse:
    async with get_db_connection() as conn:
        payload = await fetch_college_detail(conn, college_code)
    if not payload:
        raise api_error(404, "College not found", "COLLEGE_NOT_FOUND")
    return CollegeDetailResponse(**payload)
