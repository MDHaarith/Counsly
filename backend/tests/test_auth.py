import pytest
from datetime import datetime, timedelta, UTC
from jose import jwt
from fastapi import Request, HTTPException
from app.auth.session import create_session, verify_session, ALGORITHM
from app.auth.middleware import get_current_user
from app.config import settings

@pytest.mark.asyncio
async def test_create_and_verify_session():
    user_id = "test-user-123"
    token = await create_session(user_id)
    assert isinstance(token, str)

    payload = await verify_session(token)
    assert payload["sub"] == user_id
    assert "exp" in payload
    assert "iat" in payload

@pytest.mark.asyncio
async def test_verify_invalid_token():
    with pytest.raises(ValueError, match="Invalid or expired token"):
        await verify_session("invalid-token")

@pytest.mark.asyncio
async def test_verify_expired_token():
    # Create an expired token
    to_encode = {
        "sub": "test-user",
        "exp": datetime.now(UTC) - timedelta(minutes=1),
        "iat": datetime.now(UTC) - timedelta(minutes=10),
    }
    expired_token = jwt.encode(to_encode, settings.session_secret, algorithm=ALGORITHM)

    with pytest.raises(ValueError, match="Invalid or expired token"):
        await verify_session(expired_token)

@pytest.mark.asyncio
async def test_get_current_user_success():
    user_id = "test-user-456"
    token = await create_session(user_id)

    # Mock FastAPI Request
    request = Request(scope={"type": "http", "headers": [(b"authorization", f"Bearer {token}".encode())]})

    payload = await get_current_user(request)
    assert payload["sub"] == user_id

@pytest.mark.asyncio
async def test_get_current_user_missing_header():
    request = Request(scope={"type": "http", "headers": []})

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(request)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Missing or invalid authentication token"

@pytest.mark.asyncio
async def test_get_current_user_invalid_bearer():
    request = Request(scope={"type": "http", "headers": [(b"authorization", b"NotBearer token")]})

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(request)
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Missing or invalid authentication token"

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    request = Request(scope={"type": "http", "headers": [(b"authorization", b"Bearer invalid-token")]})

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(request)
    assert excinfo.value.status_code == 401
    assert "Invalid or expired token" in excinfo.value.detail
