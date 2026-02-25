from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from trendr_api.auth import AuthContext
from trendr_api.api.media import generate_media
from trendr_api.models import Project
from trendr_api.schemas import MediaGenerateRequest


@dataclass
class _FakeAsyncResult:
    id: str


class _FakeTask:
    def delay(self, *, job_id: int):
        return _FakeAsyncResult(id=f"task-{job_id}")


def _seed_project(session: Session, actor: AuthContext) -> Project:
    project = Project(
        workspace_id=actor.workspace_id,
        name="P1",
        source_type="youtube",
        source_ref="https://youtu.be/dQw4w9WgXcQ",
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def test_media_generate_creates_job(
    db_session: Session,
    actor: AuthContext,
    monkeypatch: pytest.MonkeyPatch,
):
    project = _seed_project(db_session, actor)
    monkeypatch.setattr("trendr_api.api.media.tasks.generate_media", _FakeTask())

    job = generate_media(
        MediaGenerateRequest(
            project_id=project.id,
            prompt="A cat sitting on a desk",
        ),
        session=db_session,
        actor=actor,
    )

    assert job.kind == "media"
    assert job.project_id == project.id
    assert job.input["prompt"] == "A cat sitting on a desk"


def test_media_generate_rejects_cross_workspace_project(
    db_session: Session,
    actor: AuthContext,
    other_actor: AuthContext,
    monkeypatch: pytest.MonkeyPatch,
):
    project = _seed_project(db_session, other_actor)
    monkeypatch.setattr("trendr_api.api.media.tasks.generate_media", _FakeTask())

    with pytest.raises(HTTPException) as exc:
        generate_media(
            MediaGenerateRequest(
                project_id=project.id,
                prompt="A cat",
            ),
            session=db_session,
            actor=actor,
        )

    assert exc.value.status_code == 404
