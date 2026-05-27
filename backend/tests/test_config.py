from backend.config import Settings


def test_validate_runtime_rejects_insecure_production_defaults(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ALLOW_DEV_AUTH_FALLBACK", raising=False)
    monkeypatch.delenv("JWT_SECRET", raising=False)

    settings = Settings()

    try:
        settings.validate_runtime()
        assert False, "validate_runtime should fail for insecure production defaults"
    except RuntimeError as exc:
        message = str(exc)
        assert "DATABASE_URL must be set in production." in message
        assert "JWT_SECRET must be overridden" in message
        assert "GOOGLE_CLIENT_ID must be set in production." in message


def test_validate_runtime_accepts_explicit_production_configuration(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "postgresql+psycopg2://user:pass@db:5432/counsly")
    monkeypatch.setenv("JWT_SECRET", "12345678901234567890123456789012")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "google-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("ALLOW_DEV_AUTH_FALLBACK", "false")

    settings = Settings()
    settings.validate_runtime()
