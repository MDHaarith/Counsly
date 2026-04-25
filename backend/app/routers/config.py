"""App config endpoints for runtime configuration and readiness."""

from fastapi import APIRouter

from app.db.connection import get_db_connection
from app.db.queries import fetch_config, fetch_data_freshness
from app.models import AppConfigResponse

router = APIRouter()


def _int(config: dict, key: str, default: int) -> int:
    value = config.get(key, default)
    return int(value) if value is not None else default


def _bool(config: dict, key: str, default: bool) -> bool:
    value = config.get(key, default)
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


@router.get("/status", response_model=AppConfigResponse)
async def get_status() -> AppConfigResponse:
    async with get_db_connection() as conn:
        config = await fetch_config(conn)
        freshness = await fetch_data_freshness(conn)

    return AppConfigResponse(
        tnea_phase=_int(config, "TNEA_PHASE", 0),
        total_rounds=_int(config, "TOTAL_ROUNDS", 0),
        rank_released=_bool(config, "RANK_RELEASED", False),
        roll_data_ready=_bool(config, "ROLL_DATA_READY", False),
        rank_lookup_ready=_bool(config, "RANK_LOOKUP_READY", False),
        free_chat_limit=_int(config, "FREE_CHAT_LIMIT", 3),
        season_end_date=config.get("SEASON_END_DATE"),
        broadcast_active=_bool(config, "BROADCAST_ACTIVE", False),
        broadcast_message=config.get("BROADCAST_MESSAGE"),
        data_freshness=freshness,
    )


@router.get("/ping")
async def config_ping() -> dict:
    return {"module": "config", "status": "ok"}
