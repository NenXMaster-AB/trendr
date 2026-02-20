from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..auth import AuthContext, require_auth
from ..db import get_session
from ..models import Project, Job, Template
from ..schemas import GenerateRequest, JobOut
from ..worker import tasks

router = APIRouter(prefix="/generate", tags=["generate"])

@router.post("", response_model=JobOut)
def generate(
    payload: GenerateRequest,
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

    if payload.template_id is not None:
        template = session.exec(
            select(Template).where(
                Template.id == payload.template_id,
                Template.workspace_id == actor.workspace_id,
            )
        ).first()
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        incompatible_output = next(
            (output for output in payload.outputs if output != template.kind),
            None,
        )
        if incompatible_output is not None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Template kind '{template.kind}' does not match output "
                    f"'{incompatible_output}'"
                ),
            )

    job = Job(
        kind="generate",
        status="queued",
        workspace_id=actor.workspace_id,
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
