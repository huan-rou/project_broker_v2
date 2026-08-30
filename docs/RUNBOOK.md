# Runbook

## Local Docker Startup

1. Copy `.env.example` to `.env`.
2. Run `docker compose up --build`.
3. Run `docker compose exec backend alembic upgrade head`.
4. Run `docker compose exec backend python -m app.scripts.seed_demo`.
5. Open http://localhost:5173.

## Expected Preflight States

- `ready`: DB, Redis, worker dependencies, and provider credentials are present.
- `blocked`: required OCR/LLM credentials are missing or infrastructure is unavailable.

## Common Failures

- Missing OCR key: set `OCR_PROVIDER` and `OCR_API_KEY` in `.env`.
- Missing LLM key: set `LLM_PROVIDER` and `LLM_API_KEY` in `.env`.
- DB tables missing: run `alembic upgrade head`.
- Jobs stay queued: check `docker compose logs -f worker`.
