from sisfact import create_app


def app_client():
    app = create_app(test_config={"TESTING": True})
    return app.test_client()


def test_health_text_plain():
    response = app_client().get("/health")
    assert response.status_code == 200
    assert response.mimetype == "text/plain"
    assert b"Billing One" in response.data


def test_health_json():
    response = app_client().get("/api/v1/health")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["status"] == "OK"
    assert payload["version"] == "0.2.0"


def test_login_visible_without_database_access():
    response = app_client().get("/login")
    assert response.status_code == 200
    assert b"Billing One" in response.data


def test_security_headers_present():
    response = app_client().get("/health")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers.get("X-Request-ID")
