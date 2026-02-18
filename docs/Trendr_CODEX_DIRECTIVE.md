# Trendr --- Codex Agent Directive (Build Script)

This document is written as an **agent-executable build script** for
Codex/Claude Code. Follow it in order. Keep commits small and scoped. Do
not introduce new frameworks unless explicitly directed.

------------------------------------------------------------------------

## 0) Ground Rules

### Repo

Monorepo: - `backend/` (FastAPI + SQLModel + Postgres + Redis +
Celery) - `frontend/` (Next.js App Router)

### Constraints

-   No breaking API changes without updating `schemas.py` + UI callers.
-   Prefer pure functions in `services/` with unit tests.
-   Every DB schema change must use Alembic once enabled.
-   All endpoints must validate inputs with Pydantic and return
    consistent JSON errors.

### Commit Style

-   `feat(area): ...`
-   `fix(area): ...`
-   `chore(area): ...`
-   `test(area): ...`

### Definition of Done for each step

-   Code compiles
-   Lint/typecheck passes (best-effort)
-   Docker compose works end-to-end
-   New endpoints appear in `/docs`
-   Minimal tests exist for core logic

------------------------------------------------------------------------

## 1) Immediate Objective (MVP+)

Deliver an end-to-end flow: 1) User pastes YouTube URL in UI 2) Backend
ingests: fetches metadata + transcript (REAL, not stub if possible) 3)
Backend stores transcript as artifacts 4) User clicks "Generate Posts"
5) Backend generates and stores **three separate artifacts**: tweet,
linkedin, blog 6) UI shows each artifact and allows editing + saving

------------------------------------------------------------------------

## 2) Task Index

### Phase A --- MVP Core

A1. Backend: Artifact update endpoint (PATCH)\
A2. Frontend: Artifact editor + save\
A3. Backend: Generation outputs split into separate artifacts\
A4. Backend: Template system (filesystem templates) + selection per
output kind\
A5. Backend: Ingest YouTube transcript (replace stub)\
A6. Backend: Improve job listing + project detail support\
A7. Frontend: Project detail improvements (tabs, artifact kinds, better
UX)\
A8. Tests: service tests + API integration smoke tests\
A9. CI (optional, minimal): backend tests + frontend build

### Phase B --- V1 Platform Core (after MVP)

B1. Alembic migrations\
B2. Auth + Workspaces\
B3. Templates CRUD in DB\
B4. Workflow runner v0

This directive focuses on **Phase A**.

------------------------------------------------------------------------

## 3) Phase A --- Detailed Build Steps

## A1) Backend: Artifact Update Endpoint (PATCH)

### Goal

Allow UI to update stored generated content.

### Files to modify/add

-   `backend/trendr_api/api/artifacts.py` (add patch route)
-   `backend/trendr_api/schemas.py` (add request/response schemas)

### API Contract

**PATCH** `/v1/artifacts/{artifact_id}`

Request JSON:

``` json
{
  "title": "Optional title",
  "content": "Updated content",
  "meta": { "optional": "json" }
}
```

Response JSON: - full artifact record (same shape as list endpoint)

### Implementation

1)  Add schema `ArtifactUpdate` in `schemas.py` with optional `title`,
    `content`, `meta`.
2)  Add endpoint:
    -   Validate artifact exists else 404.
    -   Apply provided fields only.
    -   Return updated artifact dict.

### Acceptance tests

-   PATCH updates content and persists.
-   PATCH non-existent artifact returns 404.

### Commit

`feat(api): add PATCH /artifacts/{id}`

------------------------------------------------------------------------

## A2) Frontend: Artifact Editor + Save

### Goal

User edits artifact content and saves.

### Files to modify/add

-   `frontend/app/projects/[id]/page.tsx`

### UX Requirements

-   Each artifact card includes:
    -   "Edit" button
    -   When editing: textarea with Save/Cancel
-   On Save:
    -   call `PATCH /v1/artifacts/{artifact_id}` with `{ content }`
    -   optimistic update OR refetch artifacts

### Acceptance

-   User can edit tweet/linkedin/blog artifacts and changes persist
    after refresh.

### Commit

`feat(ui): artifact editor with save`

------------------------------------------------------------------------

## A3) Backend: Split Generated Outputs into Separate Artifacts

### Goal

Store: - `Artifact.kind="tweet"` - `Artifact.kind="linkedin"` -
`Artifact.kind="blog"`

### Files

-   `backend/trendr_api/services/generate.py`
-   `backend/trendr_api/worker/tasks.py`
-   (optional) `backend/trendr_api/templates/`

### Implementation approach

1)  Modify generate service to accept `output_kind` and return single
    string.
2)  In Celery task:
    -   For each output in outputs:
        -   render template
        -   call provider
        -   create artifact with `kind=output_kind`
3)  Optionally store a small `generated_bundle` artifact.

### Acceptance

-   After generation job, artifacts list includes at least 3 items:
    tweet/linkedin/blog.

### Commit

`feat(generate): store per-output artifacts`

------------------------------------------------------------------------

## A4) Backend: Filesystem Template System (MVP)

### Goal

Use real prompt templates instead of hardcoded mega-prompt.

### Files/Dirs

Add: - `backend/trendr_api/templates/` - `tweet_thread.md` -
`linkedin_post.md` - `blog_post.md` -
`backend/trendr_api/services/templates.py`

Modify: - `backend/trendr_api/services/generate.py`

### Template Contract

Placeholders: - `{tone}` - `{brand_voice}` - `{transcript}` -
`{segments}` - `{audience}` (optional) - `{notes}` (optional)

### Implementation

1)  `load_template(kind: str) -> str`
2)  `render_template(template: str, ctx: dict) -> str`
3)  Generation uses template based on output kind.

### Acceptance

-   Changing template file changes output behavior.
-   Missing template fails job gracefully with clear error.

### Commit

`feat(templates): filesystem prompt templates`

------------------------------------------------------------------------

## A5) Backend: Replace YouTube Transcript Stub with Real Extraction

### Goal

Make ingestion real enough for MVP.

### Files

-   `backend/trendr_api/services/ingest.py`

### Implementation Options

**Option A (fastest):** transcript library + video id extraction.\
**Option B:** YouTube Data API captions track.

### Requirements

Robust `extract_video_id(url)` supporting: - `watch?v=` - `youtu.be/` -
`youtube.com/shorts/`

Return format:

``` json
{
  "text": "full transcript",
  "segments": [{"start": 12.3, "end": 16.8, "text": "..."}]
}
```

Failure: - Job `failed` - `job.error` explains transcript unavailable.

### Commit

`feat(ingest): real youtube transcript extraction`

------------------------------------------------------------------------

## A6) Backend: Jobs Listing + Project Detail Support

### Files

-   `backend/trendr_api/api/jobs.py`
-   `backend/trendr_api/api/projects.py`
-   `backend/trendr_api/api/artifacts.py`

### Endpoints

-   `GET /v1/jobs?project_id=123`
-   `GET /v1/projects/{id}`
-   `GET /v1/artifacts?project_id=123&kind=tweet`

### Commit

`feat(api): add project/job endpoints for UI`

------------------------------------------------------------------------

## A7) Frontend: Project Detail UX Improvements

### Requirements

-   Header: name, source link, job status
-   Tabs:
    -   All
    -   Transcript
    -   Tweets
    -   LinkedIn
    -   Blog
-   Generate modal:
    -   outputs checkboxes
    -   tone dropdown
    -   brand voice textarea

### Files

-   `frontend/app/projects/[id]/page.tsx`
-   optional components

### Commit

`feat(ui): project detail filters + generate options`

------------------------------------------------------------------------

## A8) Tests

### Backend test stack

-   pytest
-   pytest-asyncio
-   httpx

### Files

-   `backend/tests/test_templates.py`
-   `backend/tests/test_video_id_parse.py`
-   `backend/tests/test_generate_service.py`

### Requirements

-   Template rendering works
-   Video id parsing works
-   Generation returns string

### Commit

`test(backend): add unit tests`

------------------------------------------------------------------------

## A9) Minimal CI

### GitHub Actions

Add: - `.github/workflows/ci.yml`

Jobs: - backend tests - frontend build

### Commit

`chore(ci): add workflow`

------------------------------------------------------------------------

## 4) Acceptance Test Script (Manual)

``` bash
docker compose up --build
```

Steps: 1. Open dashboard 2. Paste YouTube URL 3. Import → wait success
4. Generate posts → wait success 5. Edit artifact → save → refresh

------------------------------------------------------------------------

## 5) Non-Goals (MVP)

-   Auth/workspaces
-   Vector DB
-   Scheduling
-   Workflow UI
-   Analytics
-   Marketplace

------------------------------------------------------------------------

## 6) Deliverable Summary

By end of Phase A: - Real transcript ingest - Per-output artifacts -
Editable artifacts UI - Templates - Tests - Clean commits

------------------------------------------------------------------------

END
