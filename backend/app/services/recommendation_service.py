"""Service for calculating recommendations and safety bands."""

from typing import Any
from psycopg import AsyncConnection
from app.db import queries

def compute_safety(student_rank: int | None, cutoff_rank: int | None) -> str | None:
    """Compute the safety category based on student rank vs historical cutoff."""
    if student_rank is None or cutoff_rank is None:
        return None
    if student_rank <= cutoff_rank - 500:
        return "safe"
    if student_rank <= cutoff_rank + 200:
        return "moderate"
    return "ambitious"

async def get_student_recommendations(conn: AsyncConnection, workspace_id: str, paid: bool) -> dict[str, Any]:
    """Fetch raw recommendation data and apply safety logic."""
    data = await queries.fetch_recommendations(conn, workspace_id, paid)
    
    # Logic for post-processing items (e.g., adding derived safety labels if not already in queries)
    # is currently handled within queries.fetch_recommendations for efficiency.
    return data
