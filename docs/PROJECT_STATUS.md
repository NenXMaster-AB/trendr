# Project Status (Canonical)

Last updated: 2026-02-21

## Phase A (Directive)
- `A1` Completed
- `A2` Completed
- `A3` Completed
- `A4` Completed
- `A5` Completed
- `A6` Completed
- `A7` Completed
- `A8` Completed (backend tests passing)
- `A9` Pending (CI workflow file not yet added)

## Milestone B (Roadmap)
- `B1` Mostly completed (workspace-scoped auth + membership roles)
- `B2` Completed (Alembic migrations in repo)
- `B3` Completed (template CRUD + frontend template page)
- `B4` Mostly completed (provider registry/router + OpenAI integration + workspace key settings UI/API)
- `B5` Completed (workflow model + API + runner v0 + UI page)
- `B6` Pending/Partial (basic logging only; no request-id correlation or expanded health checks yet)

## Security Progress
- Implemented workspace-scoped provider key storage.
- Implemented encrypted-at-rest secret persistence (application-managed key material via `SECRETS_ENCRYPTION_KEY`).
- Implemented RBAC guard for settings mutation endpoints (`admin`/`owner` required).
- Implemented provider settings UI (`/providers`) for save/remove and status visibility.

## Next Priorities
1. Add CI (`A9`) in `.github/workflows/ci.yml`.
2. Complete observability hardening (`B6`).
3. Security hardening follow-ups:
   - key rotation strategy,
   - audit log events for secret changes,
   - managed secret backend/KMS integration.
