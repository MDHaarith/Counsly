import pytest
from fastapi import Request, HTTPException
from app.auth.session import create_session, verify_session
from app.auth.middleware import get_current_user
from unittest.mock import MagicMock

@pytest.mark.asyncio
async def test_session_creation_and_verification():
    user_id = "user-123"
    token = await create_session(user_id)
    assert token is not None

    payload = await verify_session(token)
    assert payload["sub"] == user_id

@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    user_id = "user-456"
    token = await create_session(user_id)

    # Mock request
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": f"Bearer {token}"}

    user = await get_current_user(request)
    assert user["sub"] == user_id

@pytest.mark.asyncio
async def test_get_current_user_missing_header():
    request = MagicMock(spec=Request)
    request.headers = {}

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(request)
    assert excinfo.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_invalid_prefix():
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Basic some-token"}

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(request)
    assert excinfo.value.status_code == 401

@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer invalid-token"}

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(request)
    assert excinfo.value.status_code == 401
