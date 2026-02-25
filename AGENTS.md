# Repository Guidelines

## Project Structure & Module Organization
Trendr is a monorepo with two apps and shared infra at the root:
- `backend/`: FastAPI API, SQLModel models, Celery worker + beat, plugin system.
  - Core package: `backend/trendr_api/`
  - API routes: `backend/trendr_api/api/` (health, projects, ingest, generate, jobs, artifacts, templates, workflows, providers, provider_settings, media, schedule, analytics)
  - Business logic: `backend/trendr_api/services/` (ingest, generate, templates, writing, provider_settings, s3, media, analytics)
  - Async jobs: `backend/trendr_api/worker/` (celery_app, tasks)
  - Provider plugins: `backend/trendr_api/plugins/` (registry, router, types, providers/)
  - Migrations: `backend/alembic/versions/` (7 migrations: initial schema through events)
  - Tests: `backend/tests/` (28+ test files, pytest + pytest-asyncio)
- `frontend/`: Next.js 15 App Router UI with Tailwind + Recharts.
  - Routes: `frontend/app/` (dashboard, projects/[id], templates, workflows, providers, schedule, analytics)
  - Reusable UI: `frontend/components/` (header)
  - Client API helpers: `frontend/lib/api.ts`
- `docs/`: roadmap and agent/build directives.

## Services (docker-compose.yml)
7 services: postgres, redis, minio (S3-compatible storage), backend (FastAPI), worker (Celery), beat (Celery Beat), frontend (Next.js).

## Build, Test, and Development Commands
- `docker compose up --build`: run full stack locally.
- `cd backend && source .venv/bin/activate && pip install -r requirements.txt`: backend setup.
- `cd backend && source .venv/bin/activate && pytest tests/ -q`: run all backend tests (78 tests).
- `cd backend && uvicorn trendr_api.main:app --reload --port 8000`: run API at `:8000`.
- `cd backend && celery -A trendr_api.worker.celery_app worker --loglevel=INFO`: run worker.
- `cd backend && celery -A trendr_api.worker.celery_app beat --loglevel=INFO`: run beat scheduler.
- `cd frontend && npm i`: install frontend deps.
- `cd frontend && npm run dev | build | start | lint`: dev server, production build, serve build, lint.
- `docker compose exec backend alembic upgrade head`: run DB migrations.

## Database Models
Workspace, UserAccount, WorkspaceMember, Project, Artifact, Job, Template, Workflow, ProviderCredential, ScheduledPost, Event.

## Key Patterns
- **Auth**: header-based (`X-User-Id`, `X-Workspace-Slug`) with auto-provisioning. See `auth.py`.
- **Provider plugins**: registry + fallback router pattern for both text and image providers.
- **Celery tasks**: Job-based pattern — create Job row, dispatch task, task updates Job status.
- **Migrations**: idempotent pattern with `_table_names()` / `_index_names()` guards.
- **Frontend UI**: dark zinc theme, card pattern (`rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6`).

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indentation, type hints, `snake_case` for functions/modules, `PascalCase` for classes/schemas.
- TypeScript/React: strict mode enabled; `PascalCase` for components, route-folder naming per Next.js conventions.
- Keep API contracts aligned: schema changes reflected in backend schemas and frontend callers.

## Testing Guidelines
- Backend tests under `backend/tests/` using `pytest` naming (`test_*.py`).
- Tests use SQLite in-memory via `conftest.py` fixtures (`db_session`, `actor`, `other_actor`).
- Test patterns: direct function calls for API tests, monkeypatch for provider/task tests.
- Always activate venv before running: `source backend/.venv/bin/activate`.

## Commit & Pull Request Guidelines
- Follow scoped Conventional Commit style: `feat(area): ...`, `fix(area): ...`, `chore(area): ...`, `test(area): ...`.
- Keep commits focused and small (one concern per commit).

## Milestone Status
- **Milestone A (MVP)**: Complete — YouTube ingestion, multi-format generation, artifact editing.
- **Milestone B (Platform Core)**: Complete — Auth/workspaces, templates CRUD, workflows, provider system, observability.
- **Milestone C (Media + Publishing + Analytics)**: Complete — DALL-E 3 image generation, MinIO S3 storage, content scheduling with Celery Beat, analytics with Recharts dashboard.
- **Milestone D (Developer Ecosystem)**: Next — Plugin packaging spec, webhooks, SDK, rate limiting, CI/CD.

## Security & Configuration Tips
- `.env` is gitignored. Required vars: DATABASE_URL, REDIS_URL, CELERY_*, OPENAI_API_KEY, JWT_SECRET, S3_* (MinIO).
- Do not commit secrets; keep keys in local env files.
- Tighten permissive CORS/default secrets before any non-local deployment.
