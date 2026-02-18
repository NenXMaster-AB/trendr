# Trendr — Codex Build Roadmap (In-Depth)

## 0) Purpose & Definition of Done

Trendr is a modular content creation platform that:
- Ingests source content (starting with YouTube).
- Extracts intelligence (transcript, segmentation, key moments, topics).
- Generates multi-platform outputs (tweets/threads, LinkedIn posts, blog drafts).
- Generates media assets (thumbnails, icons) via pluggable providers.
- Supports workflows (DAG-style execution), scheduling/publishing, analytics, and team collaboration.
- Is built developer-first: plugin system, templates, API, SDK.

**Definition of Done (MVP → V1):**
- MVP: YouTube URL → transcript stored → generate drafts stored → view/edit drafts in UI.
- V1: Auth + workspaces, workflows, templates, brand voice, media generation, basic scheduling, observability, tests, CI/CD.

---

## 1) Repo & Architecture Goals

### 1.1 Monorepo Layout (Current)
- `backend/` FastAPI + SQLModel + Postgres + Redis + Celery
- `frontend/` Next.js (App Router) + Tailwind
- `docker-compose.yml` local stack

### 1.2 Target Architecture (Evolvable)
**Backend services**
- API: FastAPI (REST)
- Workers: Celery for background jobs (ingest/generate/workflows/media processing)
- DB: Postgres (SQLModel + Alembic migrations)
- Cache/Queue: Redis
- Object storage (V1): S3-compatible for transcripts, artifacts, images, generated files

**AI Layer**
- Provider abstraction for text + image + (later) video models
- Prompt template manager
- Brand voice memory (later: embeddings + vector index)

**Front-end**
- Next.js UI with:
  - Dashboard (Projects, Jobs, Templates)
  - Project detail (Artifacts, Generation, Editing)
  - Workflow builder (later)
  - Publishing calendar (later)

---

## 2) Milestone Plan (High Level)

### Milestone A — “MVP Functional Spine” (1–2 weeks)
Goal: The critical path works end-to-end reliably.

**Deliverables**
- Real YouTube transcript extraction
- Artifact persistence and viewing
- Generation templates per output type
- Job status polling + error surfaces
- Basic editing + export

### Milestone B — “V1 Platform Core” (2–4 weeks)
Goal: Make it multi-tenant, secure, extensible.

**Deliverables**
- Auth + Workspaces
- Template system + variables
- Plugin loader + registry improvements
- Workflow engine (simple DAG) and node/task registry
- Observability + structured logging
- Alembic migrations

### Milestone C — “Media + Publishing” (4–8 weeks)
Goal: Thumbnails/icons + scheduling + posting.

**Deliverables**
- Image generation provider integrations
- Visual templates for thumbnails/icons
- Social integrations (X/LinkedIn) or scheduling queue
- Content calendar UI
- Analytics collection

### Milestone D — “Developer Ecosystem” (8+ weeks)
Goal: Make Trendr a platform.

**Deliverables**
- Plugin marketplace / plugin packaging spec
- Webhooks + SDK
- CLI tool
- Team approvals, roles, audit logs
- Enterprise controls (policy, model routing)

---

## 3) Milestone A — MVP Functional Spine

### A1) Replace Transcript Stub with Real YouTube Transcription
**Backend tasks**
- Implement `services/ingest.py` real transcript fetch:
  - Option 1: Use official YouTube Data API + caption track retrieval (preferred, stable).
  - Option 2: Use a transcript library (fallback if stable).
  - Option 3: Use `yt-dlp` + ASR fallback (Whisper) (heavy, optional).
- Normalize transcript to:
  - `text` full transcript string
  - `segments`: `{start, end, text}` list

**Acceptance criteria**
- Ingest endpoint returns a job id.
- Job succeeds for common YouTube videos with captions.
- Transcript artifact is stored and visible.

**Implementation notes**
- Store raw transcript JSON in `Artifact.meta`.
- Add `artifact.kind="transcript"` and keep `content` as full text.

---

### A2) Segmentation & Key Moments (Basic)
**Backend tasks**
- Add segmentation service:
  - naive: chunk every N seconds or N characters
  - later: topic-based segmentation
- Store:
  - `Artifact.kind="segments"` or embed into transcript meta

**Acceptance criteria**
- Transcript includes segments usable for generation prompts.

---

### A3) Generation Templates per Output Type
**Backend tasks**
- Create prompt templates:
  - `templates/tweet_thread.md`
  - `templates/linkedin_post.md`
  - `templates/blog_post.md`
- Add templating engine:
  - Jinja2 templates OR simple Python `.format()` with safe escaping
- Add endpoint:
  - `GET /v1/templates`
  - `POST /v1/templates` (optional)
- Generation flow:
  - Use transcript + segments + template
  - Produce multiple artifacts:
    - `kind="tweet"`
    - `kind="linkedin"`
    - `kind="blog"`

**Acceptance criteria**
- Generate endpoint creates separate artifacts rather than a single “bundle”
- UI shows each artifact distinctly

---

### A4) UI Editing + Export
**Frontend tasks**
- Project page:
  - List artifacts by kind
  - Clicking an artifact opens:
    - editor (textarea/markdown editor)
    - save button → `PATCH /v1/artifacts/{id}`
- Add export:
  - Copy-to-clipboard
  - Download markdown file
  - (optional) export JSON bundle

**Backend tasks**
- Add artifact update endpoint:
  - `PATCH /v1/artifacts/{id}`
- Add validation and max sizes

**Acceptance criteria**
- User can edit generated content and persist it.

---

### A5) Error Handling & Job Visibility
**Backend tasks**
- Ensure every Celery task:
  - sets job to `running` then `succeeded`/`failed`
  - captures traceback in `job.error`
- Add `GET /v1/jobs?project_id=...` list endpoint

**Frontend tasks**
- Dashboard shows:
  - latest jobs
  - statuses
  - last error message surfaced

**Acceptance criteria**
- Failures are understandable from UI.

---

## 4) Milestone B — V1 Platform Core

### B1) Auth + Workspaces (Multi-Tenant)
Choose one:
- Auth.js (NextAuth) w/ JWT
- Clerk
- Keycloak (self-host)

**Backend model changes**
- `Workspace` table
- `User` table (or external ID)
- `Project.workspace_id`
- `Artifact.workspace_id`
- `Job.workspace_id`

**API changes**
- Every request requires auth
- Workspace scoping is mandatory

**Acceptance criteria**
- Two users cannot see each other’s projects.

---

### B2) Alembic Migrations
**Backend tasks**
- Set up Alembic
- Replace `create_all` startup behavior
- Create initial migration:
  - project, artifact, job, workspace/user (if included)
- Add `make migrate` scripts

**Acceptance criteria**
- DB can be created from migrations.

---

### B3) Template Manager (CRUD + Variables)
**Features**
- Create templates per output type
- Version templates
- Variables: `{tone}`, `{brand_voice}`, `{audience}`, `{transcript}`, `{segments}`

**Backend**
- `Template` table:
  - `id, workspace_id, name, kind, content, meta, created_at`
- Endpoints:
  - `GET /v1/templates`
  - `POST /v1/templates`
  - `PATCH /v1/templates/{id}`
  - `DELETE /v1/templates/{id}`

**Frontend**
- Template library page
- Simple editor

**Acceptance criteria**
- Generation can pick template id.

---

### B4) Plugin System (Real)
Current registry is in-memory; evolve it.

**Design**
- `TextProvider` / `ImageProvider` interfaces remain
- Add:
  - provider config schema
  - provider capability metadata (max tokens, supports json mode, etc.)
  - provider router (fallback chains)

**Implementation tasks**
- Add `providers/openai.py` real integration
- Add `providers/nanobanana.py` real integration (if API available)
- Add per-workspace provider settings:
  - store keys in secrets manager or encrypted at rest

**Acceptance criteria**
- Providers can be swapped without changing business logic.

---

### B5) Workflow Engine v0 (DAG)
You already have a workflow JSON stub—make it real.

**Workflow concepts**
- Workflow definition:
  - nodes: `{id, type, task, params}`
  - edges
- Task registry:
  - `ingest_youtube`, `segment_transcript`, `generate_tweet`, `generate_linkedin`, `generate_blog`, `generate_thumbnail`
- Executor:
  - topological sort
  - enqueue node tasks
  - store node statuses in job output

**Backend tasks**
- `Workflow` table:
  - `id, workspace_id, name, definition_json`
- Endpoints:
  - `POST /v1/workflows`
  - `GET /v1/workflows`
  - `POST /v1/workflows/{id}/run` → creates a `Job(kind="workflow")`

**Acceptance criteria**
- A workflow run generates the same artifacts as manual steps.

---

### B6) Observability & Logging
**Backend**
- Structured JSON logging
- request_id correlation (middleware)
- Celery task logs include job_id
- Health endpoint expands:
  - DB connectivity
  - Redis connectivity

**Acceptance criteria**
- Debugging production issues is feasible.

---

## 5) Milestone C — Media + Publishing

### C1) Image/Thumbnail/Icon Generation
**Backend**
- Add `POST /v1/media/thumbnail` and `POST /v1/media/icon`
- Accept:
  - base prompt + style preset
  - optional reference image support (later)
- Store outputs:
  - `Artifact.kind="thumbnail"` or `kind="icon"`
  - `meta.url` or `meta.b64`
- Add storage:
  - write images to S3 and store URL

**Frontend**
- Media tab on project:
  - prompt input
  - choose provider
  - generate and preview

**Acceptance criteria**
- You can generate and view a thumbnail for a project.

---

### C2) Scheduling & Publishing (MVP)
**Two-step approach**
- MVP: internal queue and “export-ready” output
- V1: direct publish integrations

**Backend**
- `ScheduledPost` table:
  - `workspace_id, project_id, platform, content, scheduled_at, status`
- Worker runs “publisher” tasks
- Add endpoints:
  - `POST /v1/publish/schedule`
  - `GET /v1/publish/schedule`

**Frontend**
- Calendar view
- Queue view

**Acceptance criteria**
- Posts can be scheduled and marked as “ready/sent/failed”.

---

### C3) Analytics (Basic)
**Backend**
- Collect:
  - generation counts
  - job durations
  - token usage (if providers return it)
- Store in `Event` table or metrics system

**Frontend**
- Simple analytics dashboard:
  - # projects created
  - # artifacts generated
  - average job latency

**Acceptance criteria**
- You can measure usage trends.

---

## 6) Milestone D — Developer Ecosystem & Scaling

### D1) Plugin Packaging Spec
**Goal**
- Third-party plugins can be installed without editing core code.

**Plan**
- Define plugin manifest:
  - name, version, type (text/image/workflow node)
  - entrypoint module
  - config schema
- Support loading plugins from:
  - local folder
  - pip package
  - remote registry (future)

**Acceptance criteria**
- A plugin can add a new workflow node type.

---

### D2) API Keys, Webhooks, SDK
**Backend**
- API keys per workspace
- Webhooks:
  - `job.succeeded`, `job.failed`, `artifact.created`
- SDK:
  - python client
  - typescript client

**Acceptance criteria**
- External apps can trigger ingestion/generation and receive events.

---

### D3) Scale & Hardening
- Rate limiting
- Idempotency keys
- Retries with backoff
- Large artifact storage in S3
- Background processing for heavy operations
- Queue separation:
  - ingest queue
  - generate queue
  - media queue

---

## 7) Security & Compliance Checklist (Do This Early)

### Data
- Encrypt secrets at rest
- Don’t store provider API keys in plaintext
- Add artifact redaction utilities (PII scrub optional)

### Auth
- JWT validation in backend
- Workspace authorization guardrails

### AppSec
- Input validation
- Size limits (upload limits, transcript max)
- SSRF protection (YouTube URL fetch safety)
- Dependency scanning (Dependabot)

---

## 8) Testing Strategy

### Unit tests
- Template rendering
- Provider routing
- Workflow topological sort
- Transcript parsing normalization

### Integration tests
- API endpoints using test DB
- Celery task execution
- Full: ingest → generate → artifacts exist

### Frontend tests
- Smoke test pages
- API client error handling

**Acceptance criteria**
- CI runs test suite and blocks merges on failure.

---

## 9) CI/CD & Environments

### Local
- docker compose for everything

### Staging
- Render/Railway/Fly.io
- Managed Postgres + Redis
- S3 bucket for artifacts

### Production
- Same as staging + observability
- Blue/green deploy (optional)

**CI tasks**
- backend lint + tests
- frontend build + typecheck
- security scanning

---

## 10) Concrete Next Actions for Codex (Start Here)

### Step 1 (Backend): Transcript
- Implement `fetch_youtube_transcript(url)`
- Add robust error handling
- Store transcript artifact

### Step 2 (Backend): Template + Separate artifacts
- Create templates folder
- Update generation task to create 3 artifacts

### Step 3 (Frontend): Artifact viewer/editor
- Add artifact detail page or modal
- Add PATCH endpoint

### Step 4: Migrations + Auth planning
- Add alembic
- Decide auth provider

---

## 11) API Contracts (Current + Planned)

### Current (Skeleton)
- `POST /v1/ingest/youtube`
- `POST /v1/generate`
- `GET /v1/jobs/{job_id}`
- `GET /v1/projects`
- `GET /v1/artifacts?project_id=...`

### Planned
- `PATCH /v1/artifacts/{id}`
- `GET/POST/PATCH/DELETE /v1/templates`
- `GET/POST /v1/workflows`
- `POST /v1/workflows/{id}/run`
- `POST /v1/media/thumbnail`
- `POST /v1/publish/schedule`

---

## 12) Data Model (Planned)

### Existing
- Project
- Artifact
- Job

### Add
- Workspace
- Template
- Workflow
- ScheduledPost
- Event (metrics/audit)

---

## 13) Coding Standards (Important)
- Backend:
  - typed functions
  - explicit error types
  - structured logs
- Frontend:
  - keep API client in `lib/api.ts`
  - validate forms
  - optimistic UI where safe
- Always add:
  - docstrings for services
  - tests for new services
  - migration for schema changes

---

## 14) “Stretch” Features (After V1)
- Brand voice memory via embeddings + vector store
- Trend detection + research assistant
- A/B variants and scoring
- Auto-short clip extraction (video pipeline)
- Multi-model routing (cost/latency controls)
- Team approvals and roles
- Template marketplace

---

## 15) Notes for Codex Execution
When implementing each milestone:
1. Update API schemas first (Pydantic)
2. Implement service layer (pure functions)
3. Implement Celery tasks
4. Implement API endpoints
5. Implement UI
6. Add tests
7. Update README / env examples

Keep commits scoped:
- `feat(ingest): real transcript extraction`
- `feat(generate): template manager + per-output artifacts`
- `feat(ui): artifact editor + save`
- `chore(db): alembic migrations`

---

END

