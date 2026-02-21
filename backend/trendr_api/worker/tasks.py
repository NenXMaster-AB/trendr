from __future__ import annotations
from datetime import datetime
import logging
from typing import Any, Callable

from celery import shared_task
from sqlmodel import Session, select

from ..db import engine
from ..models import Artifact, Job, Project, Template, Workflow
from ..observability import clear_job_id, set_job_id
from ..plugins.providers import register_all
from ..plugins.registry import registry
from ..services.ingest import fetch_youtube_metadata, fetch_youtube_transcript
from ..services.generate import generate_text_output
from ..workflows.engine import topological_order, validate_workflow

logger = logging.getLogger(__name__)


def _update_job(session: Session, job: Job, **kwargs):
    for k, v in kwargs.items():
        setattr(job, k, v)
    job.updated_at = datetime.utcnow()
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def _requery_job(session: Session, job_id: int) -> Job | None:
    return session.exec(select(Job).where(Job.id == job_id)).first()


@shared_task(name="trendr.ingest_youtube")
def ingest_youtube(job_id: int):
    set_job_id(job_id)
    logger.info("celery_task_started", extra={"task": "ingest_youtube"})
    try:
        with Session(engine) as session:
            job = session.exec(select(Job).where(Job.id == job_id)).first()
            if not job:
                logger.warning("celery_task_job_not_found", extra={"task": "ingest_youtube"})
                return {"error": "job not found"}

            _update_job(session, job, status="running")

            try:
                url = job.input.get("url")
                if not isinstance(url, str) or not url.strip():
                    raise ValueError("Missing 'url' in ingest job payload")

                yt_meta = _run_async(fetch_youtube_metadata(url))
                transcript = _run_async(fetch_youtube_transcript(url))

                # Store artifacts
                session.add(
                    Artifact(
                        workspace_id=job.workspace_id,
                        project_id=job.project_id,
                        kind="source_meta",
                        title="YouTube Metadata",
                        content="",
                        meta=yt_meta,
                    )
                )
                session.add(
                    Artifact(
                        workspace_id=job.workspace_id,
                        project_id=job.project_id,
                        kind="transcript",
                        title="Transcript",
                        content=transcript["text"],
                        meta={"segments": transcript["segments"]},
                    )
                )
                session.commit()

                _update_job(
                    session,
                    job,
                    status="succeeded",
                    output={
                        "youtube": yt_meta,
                        "transcript_chars": len(transcript["text"]),
                        "segments": len(transcript["segments"]),
                    },
                )
                logger.info(
                    "celery_task_succeeded",
                    extra={
                        "task": "ingest_youtube",
                        "project_id": job.project_id,
                    },
                )
                return {"ok": True}
            except Exception as e:
                _update_job(
                    session,
                    job,
                    status="failed",
                    error=f"{e.__class__.__name__}: {e}",
                )
                logger.exception("celery_task_failed", extra={"task": "ingest_youtube"})
                return {"ok": False, "error": str(e)}
    finally:
        clear_job_id()


def _workflow_ingest_youtube(
    *,
    session: Session,
    workflow_job: Job,
    node: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    params = node.get("params")
    node_params = params if isinstance(params, dict) else {}

    url = node_params.get("url") or context.get("url")
    if not isinstance(url, str) or not url.strip():
        raise ValueError("Workflow ingest_youtube node requires a 'url'")

    project_id = context.get("project_id")
    if project_id is None:
        project_name = node_params.get("project_name") or context.get("project_name") or "Workflow Import"
        project = Project(
            workspace_id=workflow_job.workspace_id,
            name=str(project_name),
            source_type="youtube",
            source_ref=url,
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        if project.id is None:
            raise RuntimeError("Failed to create project for workflow ingest")
        project_id = project.id
        context["project_id"] = project_id

    ingest_job = Job(
        kind="ingest",
        status="queued",
        workspace_id=workflow_job.workspace_id,
        project_id=int(project_id),
        input={"url": url},
        output={},
    )
    session.add(ingest_job)
    session.commit()
    session.refresh(ingest_job)
    if ingest_job.id is None:
        raise RuntimeError("Failed to create ingest child job")

    ingest_youtube(ingest_job.id)
    session.expire_all()
    refreshed = _requery_job(session, ingest_job.id)
    if not refreshed or refreshed.status != "succeeded":
        error = refreshed.error if refreshed else "Ingest job not found after execution"
        raise RuntimeError(error or "Ingest workflow node failed")

    return {
        "kind": "ingest",
        "job_id": refreshed.id,
        "project_id": refreshed.project_id,
        "status": refreshed.status,
    }


def _workflow_generate_posts(
    *,
    session: Session,
    workflow_job: Job,
    node: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    params = node.get("params")
    node_params = params if isinstance(params, dict) else {}

    project_id = node_params.get("project_id") or context.get("project_id")
    if project_id is None:
        raise ValueError("Workflow generate_posts node requires a project_id")

    outputs = node_params.get("outputs") or context.get("outputs") or ["tweet", "linkedin", "blog"]
    tone = node_params.get("tone") or context.get("tone") or "professional"
    brand_voice = node_params.get("brand_voice")
    if brand_voice is None:
        brand_voice = context.get("brand_voice")
    template_id = node_params.get("template_id")
    if template_id is None:
        template_id = context.get("template_id")
    meta = node_params.get("meta")
    if meta is None:
        meta = context.get("meta")

    generate_job = Job(
        kind="generate",
        status="queued",
        workspace_id=workflow_job.workspace_id,
        project_id=int(project_id),
        input={
            "project_id": int(project_id),
            "outputs": outputs,
            "tone": tone,
            "brand_voice": brand_voice,
            "template_id": template_id,
            "meta": meta or {},
        },
        output={},
    )
    session.add(generate_job)
    session.commit()
    session.refresh(generate_job)
    if generate_job.id is None:
        raise RuntimeError("Failed to create generate child job")

    generate_posts(generate_job.id)
    session.expire_all()
    refreshed = _requery_job(session, generate_job.id)
    if not refreshed or refreshed.status != "succeeded":
        error = refreshed.error if refreshed else "Generate job not found after execution"
        raise RuntimeError(error or "Generate workflow node failed")

    output = refreshed.output if isinstance(refreshed.output, dict) else {}
    context["artifact_ids"] = output.get("artifact_ids", [])

    return {
        "kind": "generate",
        "job_id": refreshed.id,
        "status": refreshed.status,
        "artifact_ids": output.get("artifact_ids", []),
    }


WORKFLOW_TASK_HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "ingest_youtube": _workflow_ingest_youtube,
    "generate_posts": _workflow_generate_posts,
}


def _ensure_providers_registered() -> None:
    if registry.list_text():
        return
    register_all()


@shared_task(name="trendr.generate_posts")
def generate_posts(job_id: int):
    set_job_id(job_id)
    logger.info("celery_task_started", extra={"task": "generate_posts"})
    _ensure_providers_registered()
    try:
        with Session(engine) as session:
            job = session.exec(select(Job).where(Job.id == job_id)).first()
            if not job:
                logger.warning("celery_task_job_not_found", extra={"task": "generate_posts"})
                return {"error": "job not found"}

            _update_job(session, job, status="running")
            try:
                payload = job.input or {}
                project_id = job.project_id or payload.get("project_id")
                outputs = payload.get("outputs", ["tweet", "linkedin", "blog"])
                tone = payload.get("tone", "professional")
                brand_voice = payload.get("brand_voice")
                template_id = payload.get("template_id")

                if not project_id:
                    raise ValueError("Missing project_id for generation job")

                template = None
                if template_id is not None:
                    try:
                        template_id_int = int(template_id)
                    except (TypeError, ValueError):
                        raise ValueError("Invalid template_id")
                    template = session.exec(
                        select(Template).where(
                            Template.id == template_id_int,
                            Template.workspace_id == job.workspace_id,
                        )
                    ).first()
                    if not template:
                        raise ValueError(f"Template {template_id_int} not found")

                # Get transcript
                transcript_art = session.exec(
                    select(Artifact).where(
                        Artifact.workspace_id == job.workspace_id,
                        Artifact.project_id == project_id,
                        Artifact.kind == "transcript",
                    ).order_by(Artifact.id.desc())
                ).first()

                transcript = transcript_art.content if transcript_art else "No transcript found. (Run ingest first.)"
                segments = (
                    transcript_art.meta.get("segments", [])
                    if transcript_art and isinstance(transcript_art.meta, dict)
                    else []
                )

                created_artifact_ids = []
                for output_kind in outputs:
                    if template is not None and output_kind != template.kind:
                        raise ValueError(
                            f"Template kind '{template.kind}' does not match output '{output_kind}'"
                        )
                    text = _run_async(
                        generate_text_output(
                            transcript=transcript,
                            segments=segments,
                            output_kind=output_kind,
                            tone=tone,
                            brand_voice=brand_voice,
                            provider_name="openai",
                            meta={**(payload.get("meta") or {}), "workspace_id": job.workspace_id},
                            template_content=template.content if template else None,
                        )
                    )
                    artifact = Artifact(
                        workspace_id=job.workspace_id,
                        project_id=project_id,
                        kind=output_kind,
                        title=f"{output_kind.title()} Draft",
                        content=text,
                        meta={
                            "tone": tone,
                            "brand_voice": brand_voice,
                            "template_id": template.id if template else None,
                            "template_version": template.version if template else None,
                        },
                    )
                    session.add(artifact)
                    session.flush()
                    if artifact.id is not None:
                        created_artifact_ids.append(artifact.id)
                session.commit()

                _update_job(
                    session,
                    job,
                    status="succeeded",
                    output={
                        "generated": True,
                        "outputs": outputs,
                        "artifact_ids": created_artifact_ids,
                        "template_id": template.id if template else None,
                    },
                )
                logger.info(
                    "celery_task_succeeded",
                    extra={
                        "task": "generate_posts",
                        "project_id": project_id,
                        "artifacts_created": len(created_artifact_ids),
                    },
                )
                return {"ok": True}
            except Exception as e:
                _update_job(
                    session,
                    job,
                    status="failed",
                    error=f"{e.__class__.__name__}: {e}",
                )
                logger.exception("celery_task_failed", extra={"task": "generate_posts"})
                return {"ok": False, "error": str(e)}
    finally:
        clear_job_id()


@shared_task(name="trendr.run_workflow")
def run_workflow(job_id: int):
    set_job_id(job_id)
    logger.info("celery_task_started", extra={"task": "run_workflow"})
    try:
        with Session(engine) as session:
            job = session.exec(select(Job).where(Job.id == job_id)).first()
            if not job:
                logger.warning("celery_task_job_not_found", extra={"task": "run_workflow"})
                return {"error": "job not found"}

            node_statuses: list[dict[str, Any]] = []
            _update_job(session, job, status="running")
            try:
                payload = job.input or {}
                workflow_id_raw = payload.get("workflow_id")
                if workflow_id_raw is None:
                    raise ValueError("Missing workflow_id in workflow job payload")
                workflow_id = int(workflow_id_raw)

                workflow = session.exec(
                    select(Workflow).where(
                        Workflow.id == workflow_id,
                        Workflow.workspace_id == job.workspace_id,
                    )
                ).first()
                if not workflow:
                    raise ValueError(f"Workflow {workflow_id} not found")

                definition = workflow.definition_json if isinstance(workflow.definition_json, dict) else {}
                validate_workflow(definition, supported_tasks=set(WORKFLOW_TASK_HANDLERS.keys()))
                ordered_nodes = topological_order(definition)

                project_id_raw = payload.get("project_id")
                project_id = int(project_id_raw) if project_id_raw is not None else None
                context: dict[str, Any] = {
                    "project_id": project_id,
                    "url": payload.get("url"),
                    "project_name": payload.get("project_name"),
                    "outputs": payload.get("outputs"),
                    "tone": payload.get("tone"),
                    "brand_voice": payload.get("brand_voice"),
                    "template_id": payload.get("template_id"),
                    "meta": payload.get("meta"),
                }

                for node in ordered_nodes:
                    node_id = str(node.get("id"))
                    task_name = str(node.get("task"))
                    started_at = datetime.utcnow().isoformat()
                    handler = WORKFLOW_TASK_HANDLERS.get(task_name)
                    if handler is None:
                        raise ValueError(f"Unsupported workflow task '{task_name}'")

                    try:
                        result = handler(
                            session=session,
                            workflow_job=job,
                            node=node,
                            context=context,
                        )
                        node_statuses.append(
                            {
                                "node_id": node_id,
                                "task": task_name,
                                "status": "succeeded",
                                "started_at": started_at,
                                "finished_at": datetime.utcnow().isoformat(),
                                "result": result,
                            }
                        )
                    except Exception as node_exc:
                        node_statuses.append(
                            {
                                "node_id": node_id,
                                "task": task_name,
                                "status": "failed",
                                "started_at": started_at,
                                "finished_at": datetime.utcnow().isoformat(),
                                "error": f"{node_exc.__class__.__name__}: {node_exc}",
                            }
                        )
                        raise

                _update_job(
                    session,
                    job,
                    status="succeeded",
                    project_id=context.get("project_id"),
                    output={
                        "workflow_id": workflow.id,
                        "workflow_name": workflow.name,
                        "project_id": context.get("project_id"),
                        "artifact_ids": context.get("artifact_ids", []),
                        "node_statuses": node_statuses,
                    },
                )
                logger.info(
                    "celery_task_succeeded",
                    extra={
                        "task": "run_workflow",
                        "workflow_id": workflow_id,
                        "nodes_executed": len(node_statuses),
                    },
                )
                return {"ok": True}
            except Exception as e:
                _update_job(
                    session,
                    job,
                    status="failed",
                    error=f"{e.__class__.__name__}: {e}",
                    output={
                        "node_statuses": node_statuses,
                    },
                )
                logger.exception("celery_task_failed", extra={"task": "run_workflow"})
                return {"ok": False, "error": str(e)}
    finally:
        clear_job_id()


def _run_async(coro):
    """Run an async coroutine in a sync Celery task (skeleton)."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
