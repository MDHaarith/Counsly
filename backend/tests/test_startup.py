def test_backend_app_imports():
    from backend.main import app

    assert app.title == "Counsly API"
