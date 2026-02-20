from __future__ import annotations

from sqlmodel import Session, select

from trendr_api.auth import resolve_auth_context
from trendr_api.models import Artifact, Job, Workflow
from trendr_api.worker import tasks


async def _fake_fetch_youtube_metadata(_: str):
    return {"id": "vid-1", "title": "Demo"}


async def _fake_fetch_youtube_transcript(_: str):
    return {
        "text": "hello world transcript",
        "segments": [{"start": 0.0, "end": 1.0, "text": "hello world"}],
    }


async def _fake_generate_text_output(**_: object):
    return "generated tweet"


def test_run_workflow_executes_nodes_and_generates_artifacts(
    sqlite_engine,
    monkeypatch,
):
    monkeypatch.setattr(tasks, "engine", sqlite_engine)
    monkeypatch.setattr(tasks, "fetch_youtube_metadata", _fake_fetch_youtube_metadata)
    monkeypatch.setattr(tasks, "fetch_youtube_transcript", _fake_fetch_youtube_transcript)
    monkeypatch.setattr(tasks, "generate_text_output", _fake_generate_text_output)

    with Session(sqlite_engine) as session:
        actor = resolve_auth_context(
            session=session,
            user_external_id="workflow-user",
            workspace_slug="workflow-space",
        )

        workflow = Workflow(
            workspace_id=actor.workspace_id,
            name="YT to Tweet",
            definition_json={
                "nodes": [
                    {"id": "ingest", "type": "task", "task": "ingest_youtube"},
                    {"id": "generate", "type": "task", "task": "generate_posts"},
                ],
                "edges": [{"from": "ingest", "to": "generate"}],
            },
        )
        session.add(workflow)
        session.commit()
        session.refresh(workflow)

        parent = Job(
            kind="workflow",
            status="queued",
            workspace_id=actor.workspace_id,
            input={
                "workflow_id": workflow.id,
                "url": "https://youtu.be/dQw4w9WgXcQ",
                "outputs": ["tweet"],
                "tone": "professional",
            },
            output={},
        )
        session.add(parent)
        session.commit()
        session.refresh(parent)

        tasks.run_workflow.run(parent.id)

        session.expire_all()
        refreshed_parent = session.exec(select(Job).where(Job.id == parent.id)).first()
        assert refreshed_parent is not None
        assert refreshed_parent.status == "succeeded"
        assert isinstance(refreshed_parent.output, dict)
        assert len(refreshed_parent.output.get("node_statuses", [])) == 2

        artifacts = session.exec(
            select(Artifact).where(Artifact.workspace_id == actor.workspace_id)
        ).all()
        kinds = {artifact.kind for artifact in artifacts}
        assert "transcript" in kinds
        assert "tweet" in kinds

        child_jobs = session.exec(
            select(Job).where(
                Job.workspace_id == actor.workspace_id,
                Job.kind.in_(["ingest", "generate"]),
            )
        ).all()
        assert len(child_jobs) == 2
        assert all(job.status == "succeeded" for job in child_jobs)
