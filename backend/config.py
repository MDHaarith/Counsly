import os
from typing import Optional


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    DEFAULT_JWT_SECRET = "super-secret-jwt-signing-key-for-tnea-counsly"
    DEFAULT_RAZORPAY_KEY_ID = "rzp_test_mock_id"
    DEFAULT_RAZORPAY_KEY_SECRET = "mock_secret"

    def __init__(self) -> None:
        self.APP_ENV = os.getenv("APP_ENV", os.getenv("ENVIRONMENT", "production")).strip().lower()
        self.GOOGLE_CLIENT_ID: Optional[str] = os.getenv("GOOGLE_CLIENT_ID", None)
        self.RAZORPAY_KEY_ID: str = os.getenv("RAZORPAY_KEY_ID", self.DEFAULT_RAZORPAY_KEY_ID)
        self.RAZORPAY_KEY_SECRET: str = os.getenv("RAZORPAY_KEY_SECRET", self.DEFAULT_RAZORPAY_KEY_SECRET)
        self.AI_PROVIDER_API_KEY: Optional[str] = os.getenv(
            "AI_PROVIDER_API_KEY",
            os.getenv("OPENROUTER_API_KEY", None),
        )
        self.SEASON_END_DATE: str = os.getenv("SEASON_END_DATE", "2027-09-30")
        self.JWT_SECRET: str = os.getenv("JWT_SECRET", self.DEFAULT_JWT_SECRET)
        self.JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV in {"development", "dev", "local", "test"}

    @property
    def DATABASE_URL(self) -> str:
        url = os.getenv("DATABASE_URL")
        if url:
            return url
        if os.path.exists("counsly.db"):
            return "sqlite:///counsly.db"
        if os.path.exists("../counsly.db"):
            return "sqlite:///../counsly.db"
        return "sqlite:///counsly.db"

    @property
    def CORS_ALLOWED_ORIGINS(self) -> list[str]:
        value = os.getenv("CORS_ALLOWED_ORIGINS")
        if value:
            return [item.strip() for item in value.split(",") if item.strip()]
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://counsly.vercel.app",
        ]

    @property
    def AUTO_CREATE_TABLES(self) -> bool:
        return _parse_bool(os.getenv("AUTO_CREATE_TABLES"), default=self.is_development)

    @property
    def ALLOW_DEV_AUTH_FALLBACK(self) -> bool:
        return _parse_bool(os.getenv("ALLOW_DEV_AUTH_FALLBACK"), default=self.is_development)

    @property
    def ALLOW_MOCK_PAYMENTS(self) -> bool:
        return _parse_bool(os.getenv("ALLOW_MOCK_PAYMENTS"), default=self.is_development)

    @property
    def AI_PROVIDER_CONFIGURED(self) -> bool:
        return bool(self.AI_PROVIDER_API_KEY)

    def validate_runtime(self) -> None:
        errors: list[str] = []

        if self.is_production:
            if not os.getenv("DATABASE_URL"):
                errors.append("DATABASE_URL must be set in production.")
            if self.JWT_SECRET == self.DEFAULT_JWT_SECRET or len(self.JWT_SECRET) < 32:
                errors.append("JWT_SECRET must be overridden with a strong value in production.")
            if not self.GOOGLE_CLIENT_ID:
                errors.append("GOOGLE_CLIENT_ID must be set in production.")
            if self.ALLOW_DEV_AUTH_FALLBACK:
                errors.append("ALLOW_DEV_AUTH_FALLBACK must be disabled in production.")
            if self.ALLOW_MOCK_PAYMENTS:
                errors.append("ALLOW_MOCK_PAYMENTS must be disabled in production.")
            if (
                self.RAZORPAY_KEY_ID == self.DEFAULT_RAZORPAY_KEY_ID
                or self.RAZORPAY_KEY_SECRET == self.DEFAULT_RAZORPAY_KEY_SECRET
            ):
                errors.append("Real Razorpay credentials must be configured in production.")

        if errors:
            raise RuntimeError("Invalid runtime configuration: " + " ".join(errors))


settings = Settings()
