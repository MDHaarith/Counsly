"""Database connection management."""

import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.config import settings

_pool: AsyncConnectionPool | None = None
_is_serverless = os.environ.get("VERCEL") == "1"


async def open_db_pool() -> None:
    """Open the shared PostgreSQL pool for the FastAPI process."""
    global _pool
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    if _pool is None:
        _pool = AsyncConnectionPool(
            settings.database_url,
            min_size=0 if _is_serverless else 5,
            max_size=2 if _is_serverless else 20,
            kwargs={"row_factory": dict_row},
            open=False,
        )
    if _pool.closed:
        await _pool.open()


async def close_db_pool() -> None:
    """Close the shared PostgreSQL pool during app shutdown."""
    global _pool
    if _pool is not None and not _pool.closed:
        await _pool.close()


@asynccontextmanager
async def get_db_connection() -> AsyncGenerator[AsyncConnection, None]:
    """Yield a PostgreSQL connection from the process-wide pool."""
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    await open_db_pool()
    assert _pool is not None
    async with _pool.connection() as conn:
        yield conn
