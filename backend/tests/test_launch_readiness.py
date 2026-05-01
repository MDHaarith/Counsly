import ast
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from app.config import settings
from app.db.queries import compute_safety
from app.models import MarksRequest
from app.routers import auth
from app.routers.config import _round_dates
from app.routers.payments import verify_razorpay_payment_signature, verify_razorpay_webhook_signature


def test_queries_has_no_duplicate_launch_functions() -> None:
    source = Path("app/db/queries.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.AsyncFunctionDef)
        and node.name in {"search_colleges", "move_choice", "update_choice", "remove_choice"}
    ]

    assert names.count("search_colleges") == 1
    assert names.count("move_choice") == 1
    assert names.count("update_choice") == 1
    assert names.count("remove_choice") == 1


def test_marks_request_rejects_out_of_range_marks() -> None:
    with pytest.raises(ValidationError):
        MarksRequest(maths_mark=101, physics_mark=80, chemistry_mark=80)

    with pytest.raises(ValidationError):
        MarksRequest(maths_mark=90, physics_mark=-1, chemistry_mark=80)


def test_round_dates_stop_at_first_gap(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "round_1_date", "2026-07-01")
    monkeypatch.setattr(settings, "round_2_date", "2026-07-05")
    monkeypatch.setattr(settings, "round_3_date", "")
    monkeypatch.setattr(settings, "round_4_date", "2026-07-20")
    monkeypatch.setattr(settings, "round_5_date", "")

    assert [(round_date.round_number, round_date.date) for round_date in _round_dates()] == [
        (1, "2026-07-01"),
        (2, "2026-07-05"),
    ]


def test_compute_safety_uses_asymmetric_cutoff_band() -> None:
    assert compute_safety(3800, 4500) == "safe"
    assert compute_safety(4500, 4500) == "moderate"
    assert compute_safety(4700, 4500) == "moderate"
    assert compute_safety(5000, 4500) == "ambitious"


def test_payment_signature_helpers_reject_invalid_signatures() -> None:
    assert not verify_razorpay_payment_signature("order_1", "pay_1", "invalid", "secret")
    assert not verify_razorpay_webhook_signature(b'{"event":"payment.captured"}', "invalid", "secret")
    assert not verify_razorpay_webhook_signature(b"{}", None, "secret")


def test_cors_origin_regex_allows_vercel_preview_frontends(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "frontend_url", "https://counsly-frontend.vercel.app")
    monkeypatch.setattr(settings, "cors_origins", "https://counsly-frontend.vercel.app,https://counsly.in")

    assert settings.cors_origin_regex
    assert "counsly\\-frontend" in settings.cors_origin_regex
    assert "vercel\\.app" in settings.cors_origin_regex


def test_session_cookie_allows_cross_origin_frontend_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth.settings, "frontend_url", "https://counsly-frontend.vercel.app")

    app = FastAPI()

    @app.get("/set-session")
    async def set_session(request: Request, response: Response) -> dict[str, bool]:
        auth._set_session_cookie(request, response, "token")
        return {"ok": True}

    client = TestClient(app)
    response = client.get(
        "/set-session",
        headers={
            "host": "counsly-backend.vercel.app",
            "x-forwarded-proto": "https",
            "x-forwarded-host": "counsly-backend.vercel.app",
        },
    )

    cookie = response.headers["set-cookie"].lower()
    assert "samesite=none" in cookie
    assert "secure" in cookie


def test_session_cookie_stays_lax_for_same_origin_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth.settings, "frontend_url", "http://testserver")

    app = FastAPI()

    @app.get("/set-session")
    async def set_session(request: Request, response: Response) -> dict[str, bool]:
        auth._set_session_cookie(request, response, "token")
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/set-session")

    assert "samesite=lax" in response.headers["set-cookie"].lower()


def _auth_test_client() -> TestClient:
    app = FastAPI()
    app.include_router(auth.router, prefix="/api/auth")
    return TestClient(app)


def test_google_callback_rejects_invalid_state(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth.settings, "google_client_id", "client-id")
    monkeypatch.setattr(auth.settings, "google_client_secret", "client-secret")
    client = _auth_test_client()
    client.cookies.set(auth.OAUTH_STATE_COOKIE, "expected")

    response = client.get("/api/auth/callback?code=code&state=bad")

    assert response.status_code == 401


def test_google_start_sets_secure_state_cookie_only_on_https(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth.settings, "google_client_id", "client-id")

    async def fake_google_url(redirect_uri: str, state: str) -> str:
        return f"https://accounts.google.test/start?redirect_uri={redirect_uri}&state={state}"

    monkeypatch.setattr(auth, "get_google_auth_url", fake_google_url)
    client = _auth_test_client()

    http_response = client.get("/api/auth/google/start", follow_redirects=False)
    https_response = client.get("/api/auth/google/start", headers={"x-forwarded-proto": "https"}, follow_redirects=False)

    assert "secure" not in http_response.headers["set-cookie"].lower()
    assert "secure" in https_response.headers["set-cookie"].lower()


def test_google_callback_uses_verified_id_token_claims_without_userinfo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth.settings, "google_client_id", "client-id")
    monkeypatch.setattr(auth.settings, "google_client_secret", "client-secret")
    monkeypatch.setattr(auth.settings, "frontend_url", "https://counsly-frontend.vercel.app")
    monkeypatch.setattr(auth.settings, "season_year", 2026)

    class FakeResponse:
        status_code = 200

        def json(self) -> dict[str, str]:
            return {"id_token": "good-id-token"}

    class FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(self, *args: object, **kwargs: object) -> FakeResponse:
            return FakeResponse()

        async def get(self, *args: object, **kwargs: object) -> FakeResponse:
            raise AssertionError("userinfo should not be called when verified id_token claims are sufficient")

    class FakeCursor:
        def __init__(self) -> None:
            self.fetchone_calls = 0

        async def __aenter__(self) -> "FakeCursor":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def execute(self, *args: object, **kwargs: object) -> None:
            return None

        async def fetchone(self) -> dict[str, str]:
            self.fetchone_calls += 1
            if self.fetchone_calls == 1:
                return {"id": "identity-id", "auth_user_id": "auth-user-id"}
            if self.fetchone_calls == 2:
                return {"id": "550e8400-e29b-41d4-a716-446655440000"}
            raise AssertionError("unexpected fetchone call")

    class FakeConnection:
        def cursor(self, *args: object, **kwargs: object) -> FakeCursor:
            return FakeCursor()

        async def commit(self) -> None:
            return None

    class FakeConnectionContext:
        async def __aenter__(self) -> FakeConnection:
            return FakeConnection()

        async def __aexit__(self, *args: object) -> None:
            return None

    def verified_claims(_token: str) -> dict[str, object]:
        return {
            "sub": "google-sub",
            "email": "student@example.com",
            "email_verified": True,
            "name": "Student User",
            "picture": "https://example.com/avatar.png",
        }

    async def fake_create_session(user_id: str) -> str:
        assert user_id == "550e8400-e29b-41d4-a716-446655440000"
        return "session-token"

    monkeypatch.setattr(auth.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(auth, "_verify_google_id_token", verified_claims)
    monkeypatch.setattr(auth, "get_db_connection", lambda: FakeConnectionContext())
    monkeypatch.setattr(auth, "create_session", fake_create_session)

    client = _auth_test_client()
    client.cookies.set(auth.OAUTH_STATE_COOKIE, "expected")

    response = client.get("/api/auth/callback?code=code&state=expected", headers={"x-forwarded-proto": "https"}, follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "https://counsly-frontend.vercel.app/dashboard"
    cookie = response.headers["set-cookie"].lower()
    assert "counsly_session=session-token" in cookie
    assert "samesite=none" in cookie


def test_google_callback_rejects_invalid_id_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(auth.settings, "google_client_id", "client-id")
    monkeypatch.setattr(auth.settings, "google_client_secret", "client-secret")

    class FakeResponse:
        status_code = 200

        def json(self) -> dict[str, str]:
            return {"access_token": "access-token", "id_token": "bad-id-token"}

    class FakeAsyncClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, *args: object) -> None:
            return None

        async def post(self, *args: object, **kwargs: object) -> FakeResponse:
            return FakeResponse()

        async def get(self, *args: object, **kwargs: object) -> FakeResponse:
            raise AssertionError("userinfo should not be called when id_token is invalid")

    def reject_id_token(token: str) -> dict:
        raise ValueError("invalid")

    monkeypatch.setattr(auth.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(auth, "_verify_google_id_token", reject_id_token)

    client = _auth_test_client()
    client.cookies.set(auth.OAUTH_STATE_COOKIE, "expected")

    response = client.get("/api/auth/callback?code=code&state=expected")

    assert response.status_code == 401
