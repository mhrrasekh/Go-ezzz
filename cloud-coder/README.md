# My Private Cloud Coder

A private, OpenAI-compatible gateway for a coding-focused open model served by an OpenAI-compatible inference engine (for example, vLLM). It adds a private bearer token and a coding-oriented system prompt so compatible clients can use the endpoint.

## Important truth about hosting

This repository does **not** include model weights and does not create compute on OpenAI/ChatGPT servers. It is deployable source code. To run a real model, you need a server you control or an authorized inference endpoint. A GPU host sized for the chosen model may incur costs; this is not automatically free. No API key or real secret should be committed to Git.

## Quick start

1. Copy `.env.example` to `.env`.
2. Set `ACCESS_TOKEN` to a random secret of at least 32 characters.
3. Set `UPSTREAM_BASE_URL` and `UPSTREAM_MODEL` to your OpenAI-compatible inference endpoint and model ID.
4. If the upstream requires authentication, set `UPSTREAM_API_KEY` in the local `.env` file.
5. Run `docker compose up --build -d`.
6. The gateway binds to `127.0.0.1:8000` by default. Put it behind HTTPS and an authenticated reverse proxy before remote use.

Generate a token locally with PowerShell:

```powershell
[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
```

## OpenAI-compatible client

Set the client's base URL to `http://127.0.0.1:8000/v1`, use the configured bearer token, and select the model returned by `GET /v1/models`.

## Included

- Bearer-token authentication with constant-time comparison.
- Request size limit, timeout, and restricted CORS origins.
- Generic upstream error messages that avoid leaking provider response bodies.
- Health endpoint that does not disclose configuration.
- Docker deployment with loopback-only port binding and non-root runtime.
- Basic auth and health tests.

## Not implemented yet

- Streaming responses.
- Repository indexing or long-term project memory.
- File editing, terminal execution, autonomous agent loops, billing, rate limiting, and multi-user accounts.
- TLS/reverse proxy setup and production monitoring.

Do not expose this service directly to the public internet without HTTPS, rate limiting, access controls, and operational monitoring. The current MVP is a gateway, not a newly trained foundation model.
