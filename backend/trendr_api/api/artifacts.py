from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..db import get_session
from ..models import Artifact
from ..schemas import ArtifactUpdate

router = APIRouter(prefix="/artifacts", tags=["artifacts"])

@router.get("")
def list_artifacts(project_id: int, session: Session = Depends(get_session)):
    rows = session.exec(select(Artifact).where(Artifact.project_id == project_id).order_by(Artifact.id.desc())).all()
    return [a.model_dump() for a in rows]


@router.patch("/{artifact_id}")
def update_artifact(artifact_id: int, payload: ArtifactUpdate, session: Session = Depends(get_session)):
    artifact = session.exec(select(Artifact).where(Artifact.id == artifact_id)).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(artifact, field, value)

    session.add(artifact)
    session.commit()
    session.refresh(artifact)
    return artifact.model_dump()
