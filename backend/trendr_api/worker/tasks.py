from __future__ import annotations
from datetime import datetime
from celery import shared_task
from sqlmodel import Session, select

from ..db import engine
from ..models import Artifact, Job
from ..services.ingest import fetch_youtube_metadata, fetch_youtube_transcript
from ..services.generate import generate_text_output


def _update_job(session: Session, job: Job, **kwargs):
    for k, v in kwargs.items():
        setattr(job, k, v)
    job.updated_at = datetime.utcnow()
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


@shared_task(name="trendr.ingest_youtube")
def ingest_youtube(job_id: int):
    with Session(engine) as session:
        job = session.exec(select(Job).where(Job.id == job_id)).first()
        if not job:
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
            return {"ok": True}
        except Exception as e:
            _update_job(
                session,
                job,
                status="failed",
                error=f"{e.__class__.__name__}: {e}",
            )
            return {"ok": False, "error": str(e)}


@shared_task(name="trendr.generate_posts")
def generate_posts(job_id: int):
    with Session(engine) as session:
        job = session.exec(select(Job).where(Job.id == job_id)).first()
        if not job:
            return {"error": "job not found"}

        _update_job(session, job, status="running")
        try:
            payload = job.input or {}
            project_id = job.project_id or payload.get("project_id")
            outputs = payload.get("outputs", ["tweet", "linkedin", "blog"])
            tone = payload.get("tone", "professional")
            brand_voice = payload.get("brand_voice")

            if not project_id:
                raise ValueError("Missing project_id for generation job")

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
                text = _run_async(
                    generate_text_output(
                        transcript=transcript,
                        segments=segments,
                        output_kind=output_kind,
                        tone=tone,
                        brand_voice=brand_voice,
                        provider_name="openai",
                        meta=payload.get("meta"),
                    )
                )
                artifact = Artifact(
                    workspace_id=job.workspace_id,
                    project_id=project_id,
                    kind=output_kind,
                    title=f"{output_kind.title()} Draft",
                    content=text,
                    meta={"tone": tone, "brand_voice": brand_voice},
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
            return {"ok": False, "error": str(e)}


def _run_async(coro):
    """Run an async coroutine in a sync Celery task (skeleton)."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
