from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..auth import AuthContext, require_auth
from ..db import get_session
from ..models import Artifact
from ..schemas import ArtifactUpdate

router = APIRouter(prefix="/artifacts", tags=["artifacts"])

@router.get("")
def list_artifacts(
    project_id: int,
    kind: str | None = None,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    stmt = (
        select(Artifact)
        .where(
            Artifact.project_id == project_id,
            Artifact.workspace_id == actor.workspace_id,
        )
        .order_by(Artifact.id.desc())
    )
    if kind is not None:
        stmt = stmt.where(Artifact.kind == kind)
    rows = session.exec(stmt).all()
    return [a.model_dump() for a in rows]


@router.patch("/{artifact_id}")
def update_artifact(
    artifact_id: int,
    payload: ArtifactUpdate,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    artifact = session.exec(
        select(Artifact).where(
            Artifact.id == artifact_id,
            Artifact.workspace_id == actor.workspace_id,
        )
    ).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(artifact, field, value)

    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return artifact.model_dump()
