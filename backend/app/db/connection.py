"""Database connection management."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from psycopg import AsyncConnection
from psycopg.rows import dict_row

from app.config import settings
from app.errors import service_unavailable


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """Yield a PostgreSQL connection for one request or script operation."""
    if not settings.database_url:
        raise service_unavailable("DATABASE_URL is not configured", "DATABASE_NOT_CONFIGURED")

    async with await AsyncConnection.connect(settings.database_url, row_factory=dict_row) as conn:
        yield conn
