# My Private Cloud Coder

A private, OpenAI-compatible gateway for coding models. It adds a private bearer token and a coding-oriented system prompt so compatible clients can use an authorized model provider through one endpoint.

## Important hosting and billing facts

This repository does **not** provide private access to OpenAI's internal ChatGPT servers and does not create compute on OpenAI infrastructure. It can call the official OpenAI API with your own API key, or an authorized OpenAI-compatible inference endpoint. API usage is billed separately from a ChatGPT subscription; check your API billing and limits before use. Never commit real API keys or secrets to Git.

## Quick start with the official OpenAI API

1. Copy `.env.example` to `.env`.
2. Create your own API key in the official OpenAI Platform and add it to `UPSTREAM_API_KEY` in the local `.env` file only.
3. Set `UPSTREAM_BASE_URL=https://api.openai.com/v1`.
4. The example model is `gpt-6-sol`, intended for complex coding and agentic workflows. If it is not enabled for your API project, choose a model your account can access.
5. Replace `ACCESS_TOKEN` with a random secret of at least 32 characters.
6. Run `docker compose up --build -d`.
7. The gateway binds to `127.0.0.1:8000` by default. Put it behind HTTPS and an authenticated reverse proxy before remote use.

Create a local access token with PowerShell:

```powershell
[Convert]::ToBase64String([Security.Cryptography.RandomNumberGenerator]::GetBytes(48))
```

Official API docs: https://developers.openai.com/api/docs/models/all and https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create.

## Alternative: host an open-weight model

You can instead set `UPSTREAM_BASE_URL` and `UPSTREAM_MODEL` to your own authorized OpenAI-compatible inference endpoint. The example open-weight model used in earlier versions was `Qwen/Qwen3-Coder-30B-A3B-Instruct`. It is large and may require a substantial GPU; hardware rental may cost money.

Example vLLM command on a compatible GPU host (run separately from this gateway):

```bash
vllm serve Qwen/Qwen3-Coder-30B-A3B-Instruct \
  --host 127.0.0.1 \
  --port 8001 \
  --served-model-name Qwen/Qwen3-Coder-30B-A3B-Instruct
```

If the model runs on the same host, set `UPSTREAM_BASE_URL=http://host.docker.internal:8001/v1` where supported, or configure a shared Docker network and use the model service name. Do not expose the model server publicly without authentication and network controls.

## Connect a client

Set the client's base URL to `http://127.0.0.1:8000/v1`, use the configured `ACCESS_TOKEN` as the bearer token, and select the model returned by `GET /v1/models`.

## Security and limitations

- Bearer-token authentication uses constant-time comparison.
- The request-size guard checks `Content-Length`; chunked requests without that header are not yet bounded by this middleware.
- Timeouts and generic upstream error messages reduce accidental disclosure of provider details.
- CORS origins are configurable.
- Docker uses loopback-only port binding, a non-root runtime, read-only root filesystem, and no-new-privileges.
- GitHub Actions runs automated tests on changes under `cloud-coder/`.
- Streaming, repository indexing, long-term project memory, file editing, terminal execution, autonomous agent loops, billing, rate limiting, and multi-user accounts are not implemented yet.
- Do not expose this service directly to the public internet without HTTPS, request-rate limits, access controls, and operational monitoring.

The current MVP is a gateway, not a newly trained foundation model. It does not yet act autonomously on code repositories, and no deployment or API call has been run from this change.
