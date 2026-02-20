from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ..auth import AuthContext, require_auth
from ..db import get_session
from ..models import Job, Project, Workflow
from ..schemas import JobOut, WorkflowCreate, WorkflowOut, WorkflowRunRequest
from ..worker import tasks
from ..workflows.engine import validate_workflow

router = APIRouter(prefix="/workflows", tags=["workflows"])


def _to_out(workflow: Workflow) -> WorkflowOut:
    return WorkflowOut(
        id=workflow.id,
        workspace_id=workflow.workspace_id,
        name=workflow.name,
        definition_json=workflow.definition_json,
        created_at=workflow.created_at,
    )


@router.post("", response_model=WorkflowOut)
def create_workflow(
    payload: WorkflowCreate,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    try:
        validate_workflow(
            payload.definition_json,
            supported_tasks=set(tasks.WORKFLOW_TASK_HANDLERS.keys()),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    workflow = Workflow(
        workspace_id=actor.workspace_id,
        name=payload.name,
        definition_json=payload.definition_json,
    )
    session.add(workflow)
    session.commit()
    session.refresh(workflow)
    return _to_out(workflow)


@router.get("", response_model=list[WorkflowOut])
def list_workflows(
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    rows = session.exec(
        select(Workflow)
        .where(Workflow.workspace_id == actor.workspace_id)
        .order_by(Workflow.id.desc())
    ).all()
    return [_to_out(workflow) for workflow in rows]


@router.post("/{workflow_id}/run", response_model=JobOut)
def run_workflow(
    workflow_id: int,
    payload: WorkflowRunRequest,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    workflow = session.exec(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.workspace_id == actor.workspace_id,
        )
    ).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    try:
        validate_workflow(
            workflow.definition_json,
            supported_tasks=set(tasks.WORKFLOW_TASK_HANDLERS.keys()),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    project_id = payload.project_id
    if project_id is not None:
        project = session.exec(
            select(Project).where(
                Project.id == project_id,
                Project.workspace_id == actor.workspace_id,
            )
        ).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

    run_input = payload.model_dump(mode="json")
    run_input["workflow_id"] = workflow.id

    job = Job(
        kind="workflow",
        status="queued",
        workspace_id=actor.workspace_id,
        project_id=project_id,
        input=run_input,
        output={},
    )
    session.add(job)
    session.commit()
    session.refresh(job)

    async_result = tasks.run_workflow.delay(job_id=job.id)
    job.task_id = async_result.id
    session.add(job)
    session.commit()
    session.refresh(job)

    return JobOut(**job.model_dump())
