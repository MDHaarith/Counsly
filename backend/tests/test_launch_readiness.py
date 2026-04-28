import ast
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from pydantic import ValidationError

from app.config import settings
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


def test_payment_signature_helpers_reject_invalid_signatures() -> None:
    assert not verify_razorpay_payment_signature("order_1", "pay_1", "invalid", "secret")
    assert not verify_razorpay_webhook_signature(b'{"event":"payment.captured"}', "invalid", "secret")
    assert not verify_razorpay_webhook_signature(b"{}", None, "secret")


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
