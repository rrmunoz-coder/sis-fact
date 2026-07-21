from sisfact import create_app


def test_health_ok():
    app = create_app(config_path="config-no-existe.ini")
    client = app.test_client()
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "OK"


def test_sources_ok():
    app = create_app(config_path="config-no-existe.ini")
    client = app.test_client()
    response = client.get("/api/v1/sources")
    assert response.status_code == 200
    assert len(response.get_json()) >= 1
