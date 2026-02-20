from __future__ import annotations

from fastapi import HTTPException
import pytest
from sqlmodel import Session

from trendr_api.api.artifacts import update_artifact
from trendr_api.models import Artifact, Project
from trendr_api.schemas import ArtifactUpdate


def _seed_project_and_artifact(session: Session) -> Artifact:
    project = Project(name="P1", source_type="youtube", source_ref="https://youtu.be/dQw4w9WgXcQ")
    session.add(project)
    session.commit()
    session.refresh(project)

    artifact = Artifact(
        project_id=project.id,
        kind="tweet",
        title="Original",
        content="before",
        meta={"v": 1},
    )
    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return artifact


def test_patch_artifact_updates_content(db_session: Session):
    artifact = _seed_project_and_artifact(db_session)
    body = update_artifact(
        artifact.id,
        ArtifactUpdate(content="after", title="Updated"),
        db_session,
    )
    assert body["id"] == artifact.id
    assert body["content"] == "after"
    assert body["title"] == "Updated"


def test_patch_artifact_returns_404_for_missing_id(db_session: Session):
    with pytest.raises(HTTPException) as exc:
        update_artifact(99999, ArtifactUpdate(content="x"), db_session)
    assert exc.value.status_code == 404
    assert exc.value.detail == "Artifact not found"
