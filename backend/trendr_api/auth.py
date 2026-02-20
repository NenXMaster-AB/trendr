from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from .db import get_session
from .models import UserAccount, Workspace, WorkspaceMember


@dataclass
class AuthContext:
    user_id: int
    user_external_id: str
    workspace_id: int
    workspace_slug: str


def _normalize_workspace_slug(slug: str) -> str:
    value = slug.strip().lower().replace(" ", "-")
    if not value:
        raise HTTPException(status_code=400, detail="Workspace slug cannot be empty")
    return value


def _get_or_create_user(session: Session, external_id: str) -> UserAccount:
    user = session.exec(
        select(UserAccount).where(UserAccount.external_id == external_id)
    ).first()
    if user:
        return user

    user = UserAccount(external_id=external_id)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        # Another request created the same user concurrently.
        session.rollback()
        user = session.exec(
            select(UserAccount).where(UserAccount.external_id == external_id)
        ).first()
        if not user:
            raise
        return user

    session.refresh(user)
    return user


def _get_or_create_workspace(session: Session, slug: str) -> Workspace:
    workspace = session.exec(
        select(Workspace).where(Workspace.slug == slug)
    ).first()
    if workspace:
        return workspace

    workspace = Workspace(
        name=slug.replace("-", " ").title() or "Workspace",
        slug=slug,
    )
    session.add(workspace)
    try:
        session.commit()
    except IntegrityError:
        # Another request created the same workspace concurrently.
        session.rollback()
        workspace = session.exec(
            select(Workspace).where(Workspace.slug == slug)
        ).first()
        if not workspace:
            raise
        return workspace

    session.refresh(workspace)
    return workspace


def _ensure_workspace_membership(
    *,
    session: Session,
    workspace_id: int,
    user_id: int,
) -> None:
    membership = session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace_id,
            WorkspaceMember.user_id == user_id,
        )
    ).first()
    if membership:
        return

    session.add(
        WorkspaceMember(
            workspace_id=workspace_id,
            user_id=user_id,
            role="owner",
        )
    )
    try:
        session.commit()
    except IntegrityError:
        # Another request created the membership concurrently.
        session.rollback()


def resolve_auth_context(
    *,
    session: Session,
    user_external_id: str,
    workspace_slug: str,
) -> AuthContext:
    normalized_user_id = user_external_id.strip()
    if not normalized_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")

    normalized_slug = _normalize_workspace_slug(workspace_slug)

    user = _get_or_create_user(session, normalized_user_id)
    workspace = _get_or_create_workspace(session, normalized_slug)
    _ensure_workspace_membership(
        session=session,
        workspace_id=workspace.id,
        user_id=user.id,
    )

    return AuthContext(
        user_id=user.id,
        user_external_id=normalized_user_id,
        workspace_id=workspace.id,
        workspace_slug=workspace.slug,
    )


def require_auth(
    session: Session = Depends(get_session),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_workspace_slug: str | None = Header(default="default", alias="X-Workspace-Slug"),
) -> AuthContext:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")

    return resolve_auth_context(
        session=session,
        user_external_id=x_user_id,
        workspace_slug=x_workspace_slug or "default",
    )
