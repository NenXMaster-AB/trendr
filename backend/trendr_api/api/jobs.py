from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..db import get_session
from ..models import Job
from ..schemas import JobOut

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("", response_model=list[JobOut])
def list_jobs(
    project_id: int | None = None,
    limit: int = 50,
    session: Session = Depends(get_session),
):
    safe_limit = max(1, min(limit, 200))
    stmt = select(Job).order_by(Job.id.desc()).limit(safe_limit)
    if project_id is not None:
        stmt = stmt.where(Job.project_id == project_id)
    rows = session.exec(stmt).all()
    return [JobOut(**row.model_dump()) for row in rows]

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, session: Session = Depends(get_session)):
    job = session.exec(select(Job).where(Job.id == job_id)).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobOut(**job.model_dump())
