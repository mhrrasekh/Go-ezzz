from __future__ import annotations

import hmac
import json
import time
import uuid
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    access_token: str = ""
    upstream_base_url: str = "http://127.0.0.1:8001/v1"
    upstream_api_key: str = ""
    upstream_model: str = "Qwen/Qwen3-Coder-30B-A3B-Instruct"
    request_timeout_seconds: float = Field(default=180, ge=1, le=600)
    max_request_bytes: int = Field(default=200_000, ge=1024, le=2_000_000)
    allowed_origins: str = "http://localhost:4173"


settings = Settings()
app = FastAPI(
    title="My Private Cloud Coder",
    version="0.1.0",
    description="A private, OpenAI-compatible gateway for an authorized coding model endpoint.",
)

origins = [origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[dict[str, Any]] = Field(min_length=1, max_length=100)
    temperature: float | None = Field(default=0.2, ge=0, le=2)
    max_tokens: int | None = Field(default=4096, ge=1, le=32768)
    stream: bool = False


def require_token(authorization: str | None = Header(default=None)) -> None:
    expected = settings.access_token
    if not expected or len(expected) < 32:
        raise HTTPException(status_code=503, detail="Server access token is not configured securely.")
    scheme, _, supplied = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not supplied or not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid bearer token.")


@app.middleware("http")
async def request_size_guard(request: Request, call_next):
    # Content-Length is checked before FastAPI parses the request body.
    # Chunked requests without Content-Length are not rejected by this guard.
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > settings.max_request_bytes:
                return Response(status_code=413, content="Request body too large.")
        except ValueError:
            return Response(status_code=400, content="Invalid Content-Length.")
    return await call_next(request)


@app.get("/health")
async def health():
    # Intentionally reveals no credentials or upstream configuration.
    return {"status": "ok", "service": "my-private-cloud-coder"}


@app.get("/v1/models", dependencies=[Depends(require_token)])
async def models():
    return {
        "object": "list",
        "data": [{"id": settings.upstream_model, "object": "model", "owned_by": "private-deployment"}],
    }


@app.post("/v1/chat/completions", dependencies=[Depends(require_token)])
async def chat_completions(body: ChatRequest):
    if body.stream:
        raise HTTPException(status_code=501, detail="Streaming is not enabled in this MVP.")
    if not settings.upstream_base_url.startswith(("http://", "https://")):
        raise HTTPException(status_code=503, detail="Upstream endpoint is not configured.")

    headers = {"Content-Type": "application/json"}
    if settings.upstream_api_key:
        headers["Authorization"] = f"Bearer {settings.upstream_api_key}"

    payload = body.model_dump(exclude_none=True)
    payload["model"] = settings.upstream_model
    # Keep coding guidance consistent while allowing the caller to supply its own system message.
    if not any(str(message.get("role", "")).lower() == "system" for message in body.messages):
        payload["messages"] = [
            {
                "role": "system",
                "content": (
                    "You are a careful senior software engineer. Explain assumptions briefly, "
                    "prefer small testable changes, preserve existing architecture, never claim "
                    "tests passed unless they were actually run, and flag security risks. "
                    "Do not execute tools or modify files unless an authorized tool runner is added."
                ),
            },
            *body.messages,
        ]

    request_id = "req_" + uuid.uuid4().hex
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            upstream = await client.post(
                settings.upstream_base_url.rstrip("/") + "/chat/completions",
                headers=headers,
                json=payload,
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Model endpoint timed out.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Could not reach the model endpoint.") from exc

    if upstream.status_code >= 400:
        # Do not forward provider bodies that may contain sensitive deployment details.
        raise HTTPException(status_code=502, detail=f"Model endpoint returned HTTP {upstream.status_code}.")
    try:
        result = upstream.json()
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Model endpoint returned invalid JSON.") from exc
    if not isinstance(result, dict):
        raise HTTPException(status_code=502, detail="Model endpoint returned an invalid response shape.")

    result.setdefault("id", "chatcmpl-" + uuid.uuid4().hex)
    result.setdefault("object", "chat.completion")
    result.setdefault("created", int(time.time()))
    result.setdefault("model", settings.upstream_model)
    result["x_request_id"] = request_id
    return result
