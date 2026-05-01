"""Service for searching and exploring colleges."""

from typing import Any
from psycopg import AsyncConnection
from app.db import queries

async def search_colleges(conn: AsyncConnection, query: str | None, district: str | None, limit: int = 50) -> dict[str, Any]:
    """Search for colleges with optional filters."""
    return await queries.search_colleges(conn, query, district, limit)

async def get_college_detail(conn: AsyncConnection, college_code: str) -> dict[str, Any] | None:
    """Fetch college metadata and its available branches."""
    return await queries.fetch_college_detail(conn, college_code)
