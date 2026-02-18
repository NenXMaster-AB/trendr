# Repository Guidelines

## Project Structure & Module Organization
Trendr is a small monorepo with two apps and shared infra at the root:
- `backend/`: FastAPI API, SQLModel models, Celery worker, and plugin/workflow scaffolding.
  - Core package: `backend/trendr_api/`
  - API routes: `backend/trendr_api/api/`
  - Business logic: `backend/trendr_api/services/`
  - Async jobs: `backend/trendr_api/worker/`
  - Provider plugins: `backend/trendr_api/plugins/`
- `frontend/`: Next.js App Router UI with Tailwind.
  - Routes: `frontend/app/`
  - Reusable UI: `frontend/components/`
  - Client API helpers: `frontend/lib/`
- `docs/`: roadmap and agent/build directives.

## Build, Test, and Development Commands
- `docker compose up --build`: run full stack (frontend, backend, db, redis) locally.
- `cd backend && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`: backend setup.
- `cd backend && uvicorn trendr_api.main:app --reload --port 8000`: run API at `:8000`.
- `cd backend && celery -A trendr_api.worker.celery_app worker --loglevel=INFO`: run worker.
- `cd frontend && npm i`: install frontend deps.
- `cd frontend && npm run dev | build | start | lint`: dev server, production build, serve build, lint.

## Coding Style & Naming Conventions
- Python: PEP 8, 4-space indentation, type hints, `snake_case` for functions/modules, `PascalCase` for classes/schemas.
- TypeScript/React: strict mode is enabled (`frontend/tsconfig.json`); use `PascalCase` for components and route-folder naming per Next.js conventions.
- Keep API contracts aligned: schema changes should be reflected in backend schemas and frontend callers.

## Testing Guidelines
- Automated tests are not yet committed in this skeleton.
- Add backend tests under `backend/tests/` using `pytest` naming (`test_*.py`).
- Add frontend tests as `*.test.ts(x)` near components/routes once a runner is introduced.
- Minimum bar for PRs: smoke-check ingest, generate, jobs, and artifact flows via API docs/UI.

## Commit & Pull Request Guidelines
- Follow scoped Conventional Commit style used in project docs: `feat(area): ...`, `fix(area): ...`, `chore(area): ...`, `test(area): ...`.
- Keep commits focused and small (one concern per commit).
- PRs should include:
  - concise problem/solution summary,
  - impacted paths/endpoints,
  - manual verification steps,
  - UI screenshots for frontend changes,
  - linked issue/task when applicable.

## Security & Configuration Tips
- Copy env templates before running: `backend/.env.example` and `frontend/.env.local.example`.
- Do not commit secrets; keep keys in local env files.
- Tighten permissive CORS/default secrets before any non-local deployment.
