"""App config endpoints for runtime configuration and readiness."""

from fastapi import APIRouter

from app.config import settings
from app.db.connection import get_db_connection
from app.db.queries import fetch_config, fetch_data_freshness
from app.models import AppConfigResponse, RoundDateResponse

router = APIRouter()


def _bool(config: dict, key: str, default: bool) -> bool:
    value = config.get(key, default)
    if isinstance(value, bool):
        return value
    return str(value).lower() == "true"


def _round_dates() -> list[RoundDateResponse]:
    configured_dates = [
        settings.round_1_date,
        settings.round_2_date,
        settings.round_3_date,
        settings.round_4_date,
        settings.round_5_date,
    ]
    rounds: list[RoundDateResponse] = []
    for index, configured_date in enumerate(configured_dates, start=1):
        date = configured_date.strip() if configured_date else ""
        if not date:
            break
        rounds.append(RoundDateResponse(round_number=index, date=date))
    return rounds


@router.get("/status", response_model=AppConfigResponse)
async def get_status() -> AppConfigResponse:
    async with get_db_connection() as conn:
        config = await fetch_config(conn)
        freshness = await fetch_data_freshness(conn)

    round_dates = _round_dates()
    return AppConfigResponse(
        tnea_phase=settings.tnea_phase,
        total_rounds=len(round_dates) if round_dates else settings.total_rounds,
        rank_released=settings.rank_released,
        roll_data_ready=_bool(config, "ROLL_DATA_READY", False),
        rank_lookup_ready=_bool(config, "RANK_LOOKUP_READY", False),
        free_chat_limit=settings.free_chat_limit,
        season_end_date=settings.season_end_date,
        round_dates=round_dates,
        data_freshness=freshness,
    )


@router.get("/ping")
async def config_ping() -> dict:
    return {"module": "config", "status": "ok"}
