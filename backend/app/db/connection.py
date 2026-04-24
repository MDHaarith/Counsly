"""Database connection management."""

from psycopg import AsyncConnection


async def get_db_connection() -> AsyncConnection:
    """Return a new async PostgreSQL connection.

    Uses SUPABASE_URL and SUPABASE_SERVICE_KEY from settings.
    Connection is NOT auto-closed — the caller (or a context manager)
    is responsible for closing it.
    """
    # TODO: implement using settings.supabase_url and settings.supabase_service_key
    raise NotImplementedError("Database connection not yet implemented")
