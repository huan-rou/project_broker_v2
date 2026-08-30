# Project Broker V2

Docker-first thin slice for a functional Australian mortgage broker workflow:
Documents -> OCR/evidence -> Fact Find review -> calculator adapters -> lender results.

## First Run

```powershell
Copy-Item .env.example .env
docker compose up --build
```

In another terminal:

```powershell
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed_demo
```

Open:

- Frontend: http://localhost:5173
- Backend health: http://localhost:8000/health
- Preflight: http://localhost:8000/api/v1/system/preflight

## Demo Credentials

The frontend login is intentionally thin. Use:

- Broker: `broker@example.com`
- Admin-style placeholder: `admin@example.com`

Any password is accepted in this skeleton.

## Provider Policy

This repo does not include a fake OCR/LLM fallback. OCR and bridge jobs require provider settings in `.env` and will fail with structured errors when credentials are missing. Seeded data exists for UI and workflow development.

## Useful Commands

```powershell
docker compose up --build
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.scripts.seed_demo
docker compose logs -f backend worker
```

## Current Scope

This is a minimal implementation skeleton. It intentionally prioritizes stable contracts, Docker deployability, job traceability, and UI navigation over full OCR/LLM/calculator fidelity.
