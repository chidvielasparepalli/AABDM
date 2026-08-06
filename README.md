# AABDM

AI-Assisted Business Development Manager — FastAPI backend.

## Stack
- FastAPI + SQLAlchemy 2.0 (sync)
- Clerk JWT auth (PyJWT, JWKS)
- SQLite dev / PostgreSQL prod (via `DATABASE_URL`)
- Alembic migrations
- slowapi rate limiting, structured JSON logging, request-ID middleware

## Quick start

```bash
cd apps/api
python -m venv .venv && .venv/Scripts/activate   # Windows
pip install -r requirements.txt
cp .env.example .env                              # set CLERK_PUBLISHABLE_KEY
uvicorn app.main:app --reload                     # auto-runs alembic upgrade head
```

Open `http://localhost:8000/docs`.

## Tests

```bash
cd apps/api
pytest --cov=app --cov-report=term-missing        # 69 tests, 89% coverage
ruff check app tests                              # lint
```

## Migrations

```bash
cd apps/api
alembic revision --autogenerate -m "description"  # new migration
alembic upgrade head                              # apply
```

`create_all` no longer used — schema fully migration-managed. Auto-migrate on
boot (disable via `AUTO_MIGRATE=false`).

## Docker

```bash
docker compose up --build        # api + postgres, auto-migrates on boot
```

## Deploy notes
- Set `DATABASE_URL` to Postgres, real `CLERK_PUBLISHABLE_KEY`
- Rate limit defaults 100/min/IP (in-memory — swap to Redis storage for multi-worker)
- CI: `.github/workflows/ci.yml` — lint, test (py3.11/3.12), Docker build
