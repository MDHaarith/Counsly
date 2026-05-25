from backend.routes.logging import build_client_error_log


def test_build_client_error_log_preserves_fr115_fields():
    record = build_client_error_log({
        "kind": "api_error",
        "endpoint": "/choices/",
        "error_type": "server_error",
        "message": "Database unavailable",
        "status": 500,
        "user_id_hash": "abc123",
        "timestamp": "2026-05-23T10:00:00.000Z",
    })

    assert record.kind == "api_error"
    assert record.endpoint == "/choices/"
    assert record.error_type == "server_error"
    assert record.status_code == 500
    assert record.user_id_hash == "abc123"


def test_build_client_error_log_defaults_bad_status_to_none():
    record = build_client_error_log({
        "kind": "client_js_error",
        "endpoint": "/dashboard",
        "error_type": "TypeError",
        "message": "Render failed",
        "status": 0,
        "user_id_hash": "abc123",
    })

    assert record.status_code is None
