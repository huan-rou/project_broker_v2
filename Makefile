.PHONY: up migrate seed logs smoke

up:
	docker compose up --build

migrate:
	docker compose exec backend alembic upgrade head

seed:
	docker compose exec backend python -m app.scripts.seed_demo

logs:
	docker compose logs -f backend worker

smoke:
	powershell -ExecutionPolicy Bypass -File scripts/smoke.ps1
