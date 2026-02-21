# Trendr (Skeleton)

Trendr is a modular content creation platform that ingests source content (e.g., YouTube), extracts intelligence (transcripts, topics),
and generates multi-platform outputs (tweets, LinkedIn, blog drafts) plus media assets (thumbnails, icons) via pluggable AI providers.

This repo is a **runnable skeleton** (monorepo) with:
- **Backend**: FastAPI + Postgres + Redis + Celery worker
- **Frontend**: Next.js (App Router) + Tailwind + shadcn/ui (light starter)
- **Plugin system**: Provider abstraction + plugin registry (OpenAI + stub fallback)
- **Workflow engine v0**: Workflow definitions persisted + runnable DAG jobs
- **Jobs**: async jobs via Celery; API exposes job status

> This is intentionally minimal: core contracts, folder layout, and a clean runway for building.

## Quickstart (Docker)

1) Copy env templates:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
```

2) Start everything:
```bash
docker compose up --build
```

3) Open:
- Frontend: http://localhost:3000
- Backend docs: http://localhost:8000/docs

## Local Dev (without Docker)

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn trendr_api.main:app --reload --port 8000
```

### Worker
```bash
cd backend
source .venv/bin/activate
celery -A trendr_api.worker.celery_app worker --loglevel=INFO
```

### Frontend
```bash
cd frontend
npm i
npm run dev
```

## Core Concepts

### Projects
A Project represents a content source + generated artifacts.

### Ingestion
`POST /v1/ingest/youtube` creates a job that:
- fetches metadata via YouTube oEmbed (best-effort)
- pulls transcript via `youtube-transcript-api` with URL parsing + fallbacks
- stores transcript + segments (or records a clear `job.error` on failure)

### Generation
`POST /v1/generate` creates a job that:
- loads filesystem templates per output kind (`tweet`, `linkedin`, `blog`)
- applies tone/voice + anti-cliche writing constraints
- routes through text provider chain (`openai` -> `openai_stub` fallback by default)
- stores separate draft artifacts by kind

### Plugins
Providers live in `backend/trendr_api/plugins/`. Add new ones by implementing:
- `TextProvider`
- `ImageProvider`

Workspace-scoped provider keys can be managed from:
- UI: `/providers`
- API: `GET/PUT/DELETE /v1/provider-settings/text/{provider}`

### Workflows
Workflows are persisted in DB and executable via:
- `POST /v1/workflows`
- `GET /v1/workflows`
- `POST /v1/workflows/{id}/run`

Current supported workflow tasks:
- `ingest_youtube`
- `generate_posts`

## Next Steps
- Add transcript fallback path for blocked environments (cookies/proxy or `yt-dlp` subtitle fallback)
- Expand Project Detail UX (artifact kind tabs, richer generate options, filtering)
- Add backend tests (`video_id`, templates, generation, artifact patch, jobs list)
- Add minimal CI (backend tests + frontend build)
- Add auth (Clerk/Auth.js/Keycloak) and multi-tenant workspaces
- Add scheduler + publishing integrations
- Add brand voice memory (RAG + embeddings)
- Add analytics collectors + dashboards

For exact handoff status and next-session checklist, see `docs/SESSION_HANDOFF.md`.

---

**Repo layout**
```
trendr/
  backend/
  frontend/
  docker-compose.yml
```
