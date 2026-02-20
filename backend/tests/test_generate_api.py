from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from trendr_api.auth import AuthContext
from trendr_api.api.generate import generate
from trendr_api.models import Project, Template
from trendr_api.schemas import GenerateRequest


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


def _seed_template(session: Session, actor: AuthContext, *, kind: str) -> Template:
    template = Template(
        workspace_id=actor.workspace_id,
        name=f"{kind.title()} default",
        kind=kind,
        version=1,
        content="Tone: {tone}\nTranscript: {transcript}\nSegments: {segments}",
        meta={},
    )
    session.add(template)
    session.commit()
    session.refresh(template)
    return template


def test_generate_accepts_matching_template_id(
    db_session: Session,
    actor: AuthContext,
    monkeypatch: pytest.MonkeyPatch,
):
    project = _seed_project(db_session, actor)
    template = _seed_template(db_session, actor, kind="tweet")
    monkeypatch.setattr("trendr_api.api.generate.tasks.generate_posts", _FakeTask())

    job = generate(
        GenerateRequest(
            project_id=project.id,
            outputs=["tweet"],
            tone="professional",
            template_id=template.id,
        ),
        session=db_session,
        actor=actor,
    )

    assert job.project_id == project.id
    assert job.input["template_id"] == template.id


def test_generate_rejects_mismatched_template_kind(
    db_session: Session,
    actor: AuthContext,
    monkeypatch: pytest.MonkeyPatch,
):
    project = _seed_project(db_session, actor)
    template = _seed_template(db_session, actor, kind="blog")
    monkeypatch.setattr("trendr_api.api.generate.tasks.generate_posts", _FakeTask())

    with pytest.raises(HTTPException) as exc:
        generate(
            GenerateRequest(
                project_id=project.id,
                outputs=["tweet"],
                tone="professional",
                template_id=template.id,
            ),
            session=db_session,
            actor=actor,
        )

    assert exc.value.status_code == 400


def test_generate_rejects_cross_workspace_template(
    db_session: Session,
    actor: AuthContext,
    other_actor: AuthContext,
    monkeypatch: pytest.MonkeyPatch,
):
    project = _seed_project(db_session, actor)
    other_template = _seed_template(db_session, other_actor, kind="tweet")
    monkeypatch.setattr("trendr_api.api.generate.tasks.generate_posts", _FakeTask())

    with pytest.raises(HTTPException) as exc:
        generate(
            GenerateRequest(
                project_id=project.id,
                outputs=["tweet"],
                tone="professional",
                template_id=other_template.id,
            ),
            session=db_session,
            actor=actor,
        )

    assert exc.value.status_code == 404
