"""Service for handling student onboarding, marks validation, and rank bands."""

from decimal import Decimal
from typing import Any
from psycopg import AsyncConnection
from app.db import queries

DISCLAIMER = "These bands are based on historical TNEA allotment data and are not a guarantee."

def calculate_aggregate_mark(maths: int, physics: int, chemistry: int) -> Decimal:
    """Calculate the TNEA aggregate mark (cutoff)."""
    return Decimal(maths) + (Decimal(physics) / Decimal(2)) + (Decimal(chemistry) / Decimal(2))

async def save_student_marks(conn: AsyncConnection, workspace_id: str, maths: int, physics: int, chemistry: int) -> dict[str, Any]:
    """Validate marks and eligibility, then delegate to queries layer."""
    return await queries.save_marks(conn, workspace_id, maths, physics, chemistry)

async def save_student_details(conn: AsyncConnection, workspace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Validate profile details completeness and delegate to queries layer."""
    return await queries.save_details(conn, workspace_id, payload)

async def get_rank_band(conn: AsyncConnection, maths: int, physics: int, chemistry: int) -> dict[str, Any]:
    """Calculate aggregate mark and fetch the corresponding rank band."""
    aggregate_mark = calculate_aggregate_mark(maths, physics, chemistry)
    band = await queries.fetch_rank_band(conn, aggregate_mark)
    
    if not band:
        return {
            "maths_mark": maths,
            "physics_mark": physics,
            "chemistry_mark": chemistry,
            "rank_min": None,
            "rank_max": None,
            "confidence_label": None,
            "sample_size": None,
            "source_years": [],
            "is_abstain": True,
            "disclaimer": DISCLAIMER,
        }
    
    source_years = band.get("source_years") or []
    return {
        "maths_mark": maths,
        "physics_mark": physics,
        "chemistry_mark": chemistry,
        "rank_min": None if band["is_abstain"] else band["rank_min"],
        "rank_max": None if band["is_abstain"] else band["rank_max"],
        "confidence_label": None if band["is_abstain"] else band["confidence_label"],
        "sample_size": band["sample_size"],
        "source_years": source_years if isinstance(source_years, list) else [],
        "is_abstain": band["is_abstain"],
        "disclaimer": DISCLAIMER,
    }
