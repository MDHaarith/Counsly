"""Shared API error helpers."""

from fastapi import HTTPException, status


def api_error(status_code: int, error: str, code: str) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"error": error, "code": code})


def service_unavailable(error: str, code: str = "SERVICE_UNAVAILABLE") -> HTTPException:
    return api_error(status.HTTP_503_SERVICE_UNAVAILABLE, error, code)
