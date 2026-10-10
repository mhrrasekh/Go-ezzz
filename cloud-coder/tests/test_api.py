from fastapi.testclient import TestClient

from app.main import app, settings

client = TestClient(app)


def test_health_is_public_and_does_not_expose_config():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "my-private-cloud-coder"}


def test_models_requires_configured_token(monkeypatch):
    monkeypatch.setattr(settings, "access_token", "a" * 40)
    response = client.get("/v1/models")
    assert response.status_code == 401


def test_models_accepts_valid_token(monkeypatch):
    token = "a" * 40
    monkeypatch.setattr(settings, "access_token", token)
    response = client.get("/v1/models", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == settings.upstream_model
