from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..auth import AuthContext, require_auth
from ..db import get_session
from ..models import Project, Job
from ..schemas import MediaGenerateRequest, JobOut
from ..worker import tasks

router = APIRouter(prefix="/media", tags=["media"])


@router.post("/generate", response_model=JobOut)
def generate_media(
    payload: MediaGenerateRequest,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    project = session.exec(
        select(Project).where(
            Project.id == payload.project_id,
            Project.workspace_id == actor.workspace_id,
        )
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job = Job(
        kind="media",
        status="queued",
        workspace_id=actor.workspace_id,
        project_id=project.id,
        input=payload.model_dump(),
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    async_result = tasks.generate_media.delay(job_id=job.id)
    job.task_id = async_result.id
    session.add(job)
    session.commit()
    session.refresh(job)

    return JobOut(**job.model_dump())
