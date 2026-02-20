from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from trendr_api.api.workflows import create_workflow, list_workflows, run_workflow as run_workflow_api
from trendr_api.auth import AuthContext
from trendr_api.models import Project
from trendr_api.schemas import WorkflowCreate, WorkflowRunRequest


@dataclass
class _FakeAsyncResult:
    id: str


class _FakeTask:
    def delay(self, *, job_id: int):
        return _FakeAsyncResult(id=f"workflow-task-{job_id}")


def _seed_project(session: Session, actor: AuthContext) -> Project:
    project = Project(
        workspace_id=actor.workspace_id,
        name="Workflow project",
        source_type="youtube",
        source_ref="https://youtu.be/dQw4w9WgXcQ",
    )
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


def test_create_and_list_workflows_scoped_to_workspace(
    db_session: Session,
    actor: AuthContext,
    other_actor: AuthContext,
):
    definition = {
        "nodes": [
            {"id": "ingest", "type": "task", "task": "ingest_youtube"},
            {"id": "generate", "type": "task", "task": "generate_posts"},
        ],
        "edges": [{"from": "ingest", "to": "generate"}],
    }

    create_workflow(
        WorkflowCreate(name="Main flow", definition_json=definition),
        session=db_session,
        actor=actor,
    )
    create_workflow(
        WorkflowCreate(name="Other flow", definition_json=definition),
        session=db_session,
        actor=other_actor,
    )

    mine = list_workflows(session=db_session, actor=actor)
    theirs = list_workflows(session=db_session, actor=other_actor)
    assert len(mine) == 1
    assert len(theirs) == 1
    assert mine[0].workspace_id == actor.workspace_id
    assert theirs[0].workspace_id == other_actor.workspace_id


def test_create_workflow_rejects_invalid_definition(
    db_session: Session,
    actor: AuthContext,
):
    with pytest.raises(HTTPException) as exc:
        create_workflow(
            WorkflowCreate(name="Bad flow", definition_json={"nodes": [], "edges": []}),
            session=db_session,
            actor=actor,
        )
    assert exc.value.status_code == 400


def test_run_workflow_creates_workflow_job(
    db_session: Session,
    actor: AuthContext,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr("trendr_api.api.workflows.tasks.run_workflow", _FakeTask())

    definition = {
        "nodes": [
            {"id": "ingest", "type": "task", "task": "ingest_youtube"},
            {"id": "generate", "type": "task", "task": "generate_posts"},
        ],
        "edges": [{"from": "ingest", "to": "generate"}],
    }
    workflow = create_workflow(
        WorkflowCreate(name="Main flow", definition_json=definition),
        session=db_session,
        actor=actor,
    )
    project = _seed_project(db_session, actor)

    job = run_workflow_api(
        workflow_id=workflow.id,
        payload=WorkflowRunRequest(
            project_id=project.id,
            outputs=["tweet"],
            tone="professional",
        ),
        session=db_session,
        actor=actor,
    )

    assert job.kind == "workflow"
    assert job.status == "queued"
    assert job.workspace_id == actor.workspace_id
    assert job.input["workflow_id"] == workflow.id


def test_run_workflow_rejects_cross_workspace_access(
    db_session: Session,
    actor: AuthContext,
    other_actor: AuthContext,
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr("trendr_api.api.workflows.tasks.run_workflow", _FakeTask())

    definition = {
        "nodes": [{"id": "ingest", "type": "task", "task": "ingest_youtube"}],
        "edges": [],
    }
    workflow = create_workflow(
        WorkflowCreate(name="Main flow", definition_json=definition),
        session=db_session,
        actor=actor,
    )

    with pytest.raises(HTTPException) as exc:
        run_workflow_api(
            workflow_id=workflow.id,
            payload=WorkflowRunRequest(outputs=["tweet"]),
            session=db_session,
            actor=other_actor,
        )

    assert exc.value.status_code == 404
