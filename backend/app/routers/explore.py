"""Explore endpoints for searching and viewing college details."""

from fastapi import APIRouter, Depends, Query

from app.auth.middleware import get_current_user
from app.db.connection import get_db_connection
from app.errors import api_error
from app.models import CollegeDetailResponse, ExploreEnvelope
from app.services import explore_service

router = APIRouter()


@router.get("", response_model=ExploreEnvelope)
async def get_explore(q: str | None = None, district: str | None = None, user: dict = Depends(get_current_user)) -> ExploreEnvelope:
    async with get_db_connection() as conn:
        # In explore, we don't strictly enforce workspace_id for searching, 
        # but user context is provided by get_current_user dependency.
        payload = await explore_service.search_colleges(conn, q, district)
    return ExploreEnvelope(**payload)


@router.get("/{college_code}", response_model=CollegeDetailResponse)
async def get_college_detail(college_code: str, user: dict = Depends(get_current_user)) -> CollegeDetailResponse:
    async with get_db_connection() as conn:
        detail = await explore_service.get_college_detail(conn, college_code)
        if not detail:
            raise api_error(404, "College not found", "COLLEGE_NOT_FOUND")
    return CollegeDetailResponse(**detail)


@router.get("/compare")
async def compare_colleges(
    codes: str = Query(..., max_length=200),
    user: dict = Depends(get_current_user),
):
    college_codes = [c.strip() for c in codes.split(",") if c.strip()][:3]
    async with get_db_connection() as conn:
        results = []
        for code in college_codes:
            data = await explore_service.get_college_detail(conn, code)
            if data:
                results.append(data)
    return {"colleges": results}


@router.get("/ping")
async def explore_ping() -> dict:
    return {"module": "explore", "status": "ok"}
