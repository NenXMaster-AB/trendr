from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from ..auth import AuthContext, require_auth
from ..db import get_session
from ..models import ScheduledPost
from ..schemas import ScheduledPostCreate, ScheduledPostUpdate, ScheduledPostOut

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.post("", response_model=ScheduledPostOut)
def create_scheduled_post(
    payload: ScheduledPostCreate,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    now = datetime.utcnow()
    post = ScheduledPost(
        workspace_id=actor.workspace_id,
        project_id=payload.project_id,
        artifact_id=payload.artifact_id,
        platform=payload.platform,
        title=payload.title,
        content=payload.content,
        scheduled_at=payload.scheduled_at,
        status="scheduled",
        meta=payload.meta,
        created_at=now,
        updated_at=now,
    )
    session.add(post)
    session.commit()
    session.refresh(post)
    return ScheduledPostOut(**post.model_dump())


@router.get("", response_model=list[ScheduledPostOut])
def list_scheduled_posts(
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
    project_id: Optional[int] = Query(default=None),
    status: Optional[str] = Query(default=None),
    platform: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=200),
):
    stmt = select(ScheduledPost).where(
        ScheduledPost.workspace_id == actor.workspace_id
    )
    if project_id is not None:
        stmt = stmt.where(ScheduledPost.project_id == project_id)
    if status is not None:
        stmt = stmt.where(ScheduledPost.status == status)
    if platform is not None:
        stmt = stmt.where(ScheduledPost.platform == platform)
    stmt = stmt.order_by(ScheduledPost.scheduled_at.asc()).limit(limit)
    rows = session.exec(stmt).all()
    return [ScheduledPostOut(**r.model_dump()) for r in rows]


@router.patch("/{post_id}", response_model=ScheduledPostOut)
def update_scheduled_post(
    post_id: int,
    payload: ScheduledPostUpdate,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    post = session.exec(
        select(ScheduledPost).where(
            ScheduledPost.id == post_id,
            ScheduledPost.workspace_id == actor.workspace_id,
        )
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(post, key, value)
    post.updated_at = datetime.utcnow()
    session.add(post)
    session.commit()
    session.refresh(post)
    return ScheduledPostOut(**post.model_dump())


@router.delete("/{post_id}", response_model=ScheduledPostOut)
def delete_scheduled_post(
    post_id: int,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    post = session.exec(
        select(ScheduledPost).where(
            ScheduledPost.id == post_id,
            ScheduledPost.workspace_id == actor.workspace_id,
        )
    ).first()
    if not post:
        raise HTTPException(status_code=404, detail="Scheduled post not found")

    post.status = "cancelled"
    post.updated_at = datetime.utcnow()
    session.add(post)
    session.commit()
    session.refresh(post)
    return ScheduledPostOut(**post.model_dump())
