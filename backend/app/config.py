from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    google_client_id: str = ""
    google_client_secret: str = ""
    session_secret: str = "dev-secret-change-in-production"
    supabase_url: str = ""
    supabase_service_key: str = ""
    cors_origins: str = "http://localhost:3000"  # comma-separated
    trusted_hosts: str = "localhost,127.0.0.1"  # comma-separated

    # Optional — chat, payments
    openrouter_api_key: str | None = None
    openrouter_api_url: str | None = None
    openrouter_model: str | None = None
    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_host_list(self) -> list[str]:
        return [host.strip() for host in self.trusted_hosts.split(",") if host.strip()]


settings = Settings()
