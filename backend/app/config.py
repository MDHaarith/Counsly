import re
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    google_client_id: str = ""
    google_client_secret: str = ""
    session_secret: str = ""
    session_cookie_name: str = "counsly_session"
    session_ttl_seconds: int = 60 * 60 * 24 * 14
    supabase_url: str = ""
    supabase_service_key: str = ""
    database_url: str = ""
    cors_origins: str = ""  # comma-separated, MUST be set via env
    trusted_hosts: str = ""  # comma-separated, MUST be set via env
    frontend_url: str = ""  # MUST be set via env
    season_year: int = 2026
    # TNEA runtime config (replaces app_config table reads)
    tnea_phase: int = 0
    total_rounds: int = 0
    rank_released: bool = False
    free_chat_limit: int = 3
    season_end_date: str | None = None
    round_1_date: str | None = None
    round_2_date: str | None = None
    round_3_date: str | None = None
    round_4_date: str | None = None
    round_5_date: str | None = None

    # Optional — chat, payments
    openrouter_api_key: str | None = None
    openrouter_api_url: str | None = None
    openrouter_model: str | None = None
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    razorpay_webhook_secret: str | None = None
    razorpay_amount_paise: int = 14900

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        patterns: list[str] = []
        candidates = [self.frontend_url, *self.cors_origin_list]
        seen: set[str] = set()

        for origin in candidates:
            if not origin or origin in seen:
                continue
            seen.add(origin)
            parsed = urlparse(origin)
            if parsed.scheme != "https" or not parsed.netloc.endswith(".vercel.app"):
                continue
            subdomain = parsed.netloc[: -len(".vercel.app")]
            patterns.append(rf"^{re.escape(parsed.scheme)}://{re.escape(subdomain)}(?:-[a-z0-9-]+)?\.vercel\.app$")

        return "|".join(patterns) if patterns else None

    @property
    def trusted_host_list(self) -> list[str]:
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]


settings = Settings()


def validate_runtime_settings() -> None:
    """Fail startup on unsafe production-critical configuration."""
    weak_secrets = {"", "dev-secret-change-in-production", "change-me", "secret"}
    if settings.session_secret in weak_secrets or len(settings.session_secret) < 32:
        raise RuntimeError("SESSION_SECRET must be set to a unique value of at least 32 characters")
