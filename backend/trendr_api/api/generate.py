from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..db import get_session
from ..models import Project, Job
from ..schemas import GenerateRequest, JobOut
from ..worker import tasks

router = APIRouter(prefix="/generate", tags=["generate"])

@router.post("", response_model=JobOut)
def generate(payload: GenerateRequest, session: Session = Depends(get_session)):
    project = session.exec(select(Project).where(Project.id == payload.project_id)).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    job = Job(
        kind="generate",
        status="queued",
        project_id=project.id,
        input=payload.model_dump(),
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    async_result = tasks.generate_posts.delay(job_id=job.id)
    job.task_id = async_result.id
    session.add(job)
    session.commit()
    session.refresh(job)

    return JobOut(**job.model_dump())
