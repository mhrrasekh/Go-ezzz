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

## Connecting an authorized model

The default model setting is `Qwen/Qwen3-Coder-30B-A3B-Instruct`, a coding-focused open-weight model. It is large: do not assume it will run on an ordinary CPU or small GPU. Check the model card and serving-engine requirements before renting hardware. The upstream must expose an OpenAI-compatible `/v1/chat/completions` endpoint.

Example vLLM command on a compatible GPU host (run separately from this gateway):

```bash
vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct \
  --host 127.0.0.1 \
  --port 8001 \
  --served-model-name Qwen/Qwen3-Coder-30B-A3B-Instruct
```

If the model runs on the same host, set `UPSTREAM_BASE_URL=http://host.docker.internal:8001/v1` where supported, or configure a shared Docker network and use the model service name. Do not expose the model server publicly without authentication and network controls. The command above is an example, not proof that the model can run on your current hardware.

## OpenAI-compatible client

Set the client's base URL to `http://127.0.0.1:8000/v1`, use the configured bearer token, and select the model returned by `GET /v1/models`.

## Security and limitations

- Bearer-token authentication uses constant-time comparison.
- The request-size guard checks `Content-Length`; chunked requests without that header are not yet bounded by this middleware.
- Timeouts and generic upstream error messages reduce accidental disclosure of provider details.
- CORS origins are configurable.
- Docker uses loopback-only port binding, a non-root runtime, read-only root filesystem, and no-new-privileges.
- GitHub Actions runs automated tests on changes under `cloud-coder/`.
- Streaming, repository indexing, long-term project memory, file editing, terminal execution, autonomous agent loops, billing, rate limiting, and multi-user accounts are not implemented yet.
- Do not expose this service directly to the public internet without HTTPS, request-rate limits, access controls, and operational monitoring.

The current MVP is a gateway, not a newly trained foundation model. It does not yet act autonomously on code repositories.
