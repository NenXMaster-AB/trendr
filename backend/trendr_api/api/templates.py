from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from ..auth import AuthContext, require_auth
from ..db import get_session
from ..models import Template
from ..schemas import TemplateCreate, TemplateOut, TemplateUpdate

router = APIRouter(prefix="/templates", tags=["templates"])


def _to_out(template: Template) -> TemplateOut:
    return TemplateOut(
        id=template.id,
        workspace_id=template.workspace_id,
        name=template.name,
        kind=template.kind,
        version=template.version,
        content=template.content,
        meta=template.meta,
        created_at=template.created_at,
    )


@router.get("", response_model=list[TemplateOut])
def list_templates(
    kind: str | None = None,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    stmt = (
        select(Template)
        .where(Template.workspace_id == actor.workspace_id)
        .order_by(Template.id.desc())
    )
    if kind is not None:
        stmt = stmt.where(Template.kind == kind)

    rows = session.exec(stmt).all()
    return [_to_out(template) for template in rows]


@router.post("", response_model=TemplateOut)
def create_template(
    payload: TemplateCreate,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    version = payload.version
    if version is None:
        latest = session.exec(
            select(Template)
            .where(
                Template.workspace_id == actor.workspace_id,
                Template.name == payload.name,
                Template.kind == payload.kind,
            )
            .order_by(Template.version.desc())
        ).first()
        version = (latest.version if latest else 0) + 1

    if version <= 0:
        raise HTTPException(status_code=400, detail="Template version must be >= 1")

    template = Template(
        workspace_id=actor.workspace_id,
        name=payload.name,
        kind=payload.kind,
        version=version,
        content=payload.content,
        meta=payload.meta,
    )

    session.add(template)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Template version already exists for this workspace/name/kind",
        )
    session.refresh(template)
    return _to_out(template)


@router.patch("/{template_id}", response_model=TemplateOut)
def update_template(
    template_id: int,
    payload: TemplateUpdate,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    template = session.exec(
        select(Template).where(
            Template.id == template_id,
            Template.workspace_id == actor.workspace_id,
        )
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    session.add(template)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Template conflict for workspace/name/kind/version",
        )
    session.refresh(template)
    return _to_out(template)


@router.delete("/{template_id}")
def delete_template(
    template_id: int,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    template = session.exec(
        select(Template).where(
            Template.id == template_id,
            Template.workspace_id == actor.workspace_id,
        )
    ).first()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    session.delete(template)
    session.commit()
    return {"ok": True}
