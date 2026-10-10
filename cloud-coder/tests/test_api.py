import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app, settings

client = TestClient(app)
TOKEN = "t" * 40


@pytest.fixture(autouse=True)
def configured_token(monkeypatch):
    monkeypatch.setattr(settings, "access_token", TOKEN)
    monkeypatch.setattr(settings, "upstream_base_url", "http://model.test/v1")
    monkeypatch.setattr(settings, "upstream_api_key", "")


def auth(token=TOKEN):
    return {"Authorization": f"Bearer {token}"}


def test_health_is_public_and_does_not_expose_config():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "my-private-cloud-coder"}


@pytest.mark.parametrize("authorization", [None, "Basic " + TOKEN, "Bearer wrong"])
def test_models_rejects_missing_or_invalid_token(authorization):
    headers = {} if authorization is None else {"Authorization": authorization}
    assert client.get("/v1/models", headers=headers).status_code == 401


def test_models_rejects_unconfigured_or_short_token(monkeypatch):
    monkeypatch.setattr(settings, "access_token", "short")
    assert client.get("/v1/models", headers=auth("short")).status_code == 503


def test_models_accepts_valid_token():
    response = client.get("/v1/models", headers=auth())
    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == settings.upstream_model


def test_chat_injects_coding_system_prompt_and_uses_configured_model(monkeypatch):
    seen = {}

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": "ok"}}]}

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, **kwargs):
            seen["url"] = url
            seen["payload"] = kwargs["json"]
            return FakeResponse()

    monkeypatch.setattr("app.main.httpx.AsyncClient", FakeAsyncClient)
    response = client.post(
        "/v1/chat/completions",
        headers=auth(),
        json={"messages": [{"role": "user", "content": "Fix this bug"}]},
    )
    assert response.status_code == 200
    assert seen["url"] == "http://model.test/v1/chat/completions"
    assert seen["payload"]["model"] == settings.upstream_model
    assert seen["payload"]["messages"][0]["role"] == "system"
    assert "senior software engineer" in seen["payload"]["messages"][0]["content"]
    assert response.json()["choices"][0]["message"]["content"] == "ok"
    assert response.json()["x_request_id"].startswith("req_")


def test_chat_preserves_callers_system_message(monkeypatch):
    seen = {}

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {}

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, **kwargs):
            seen.update(kwargs["json"])
            return FakeResponse()

    monkeypatch.setattr("app.main.httpx.AsyncClient", FakeAsyncClient)
    response = client.post(
        "/v1/chat/completions",
        headers=auth(),
        json={"messages": [
            {"role": "system", "content": "Custom system"},
            {"role": "user", "content": "Hi"},
        ]},
    )
    assert response.status_code == 200
    assert seen["messages"][0]["content"] == "Custom system"


def test_chat_requires_authentication():
    response = client.post("/v1/chat/completions", json={"messages": [{"role": "user", "content": "Hi"}]})
    assert response.status_code == 401


def test_chat_rejects_streaming_until_implemented():
    response = client.post(
        "/v1/chat/completions",
        headers=auth(),
        json={"messages": [{"role": "user", "content": "Hi"}], "stream": True},
    )
    assert response.status_code == 501


def test_chat_maps_upstream_timeout_to_504(monkeypatch):
    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            raise httpx.TimeoutException("private upstream details")

    monkeypatch.setattr("app.main.httpx.AsyncClient", FakeAsyncClient)
    response = client.post(
        "/v1/chat/completions",
        headers=auth(),
        json={"messages": [{"role": "user", "content": "Hi"}]},
    )
    assert response.status_code == 504
    assert "private upstream details" not in response.text


@pytest.mark.parametrize("upstream_json", ["not-json", [], None])
def test_chat_rejects_invalid_upstream_response(monkeypatch, upstream_json):
    class FakeResponse:
        status_code = 200

        def json(self):
            if upstream_json == "not-json":
                raise json.JSONDecodeError("bad json", "", 0)
            return upstream_json

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("app.main.httpx.AsyncClient", FakeAsyncClient)
    response = client.post(
        "/v1/chat/completions",
        headers=auth(),
        json={"messages": [{"role": "user", "content": "Hi"}]},
    )
    assert response.status_code == 502


def test_chat_does_not_leak_upstream_error_body(monkeypatch):
    class FakeResponse:
        status_code = 500
        text = "secret internal endpoint info"

    class FakeAsyncClient:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("app.main.httpx.AsyncClient", FakeAsyncClient)
    response = client.post(
        "/v1/chat/completions",
        headers=auth(),
        json={"messages": [{"role": "user", "content": "Hi"}]},
    )
    assert response.status_code == 502
    assert "secret internal endpoint info" not in response.text


def test_request_size_guard_rejects_oversized_content_length(monkeypatch):
    monkeypatch.setattr(settings, "max_request_bytes", 1024)
    response = client.post(
        "/v1/chat/completions",
        headers={**auth(), "Content-Length": "2048"},
        content=b"x",
    )
    assert response.status_code == 413
