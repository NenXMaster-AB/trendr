from fastapi import APIRouter, Depends
from sqlmodel import Session
from ..auth import AuthContext, require_auth
from ..db import get_session
from ..models import Project, Job
from ..schemas import IngestYouTubeRequest, JobOut
from ..worker import tasks

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/youtube", response_model=JobOut)
def ingest_youtube(
    payload: IngestYouTubeRequest,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    name = payload.project_name or "YouTube Import"
    project = Project(
        workspace_id=actor.workspace_id,
        name=name,
        source_type="youtube",
        source_ref=str(payload.url),
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    job = Job(
        kind="ingest",
        status="queued",
        workspace_id=actor.workspace_id,
        project_id=project.id,
        input={"url": str(payload.url)},
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    async_result = tasks.ingest_youtube.delay(job_id=job.id)
    job.task_id = async_result.id
    session.add(job)
    session.commit()
    session.refresh(job)

    return JobOut(**job.model_dump())
