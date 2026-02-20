from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException
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

    user = session.exec(
        select(UserAccount).where(UserAccount.external_id == normalized_user_id)
    ).first()
    if not user:
        user = UserAccount(external_id=normalized_user_id)
        session.add(user)
        session.commit()
        session.refresh(user)

    workspace = session.exec(
        select(Workspace).where(Workspace.slug == normalized_slug)
    ).first()
    if not workspace:
        workspace = Workspace(
            name=normalized_slug.replace("-", " ").title() or "Workspace",
            slug=normalized_slug,
        )
        session.add(workspace)
        session.commit()
        session.refresh(workspace)

    membership = session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == user.id,
        )
    ).first()
    if not membership:
        membership = WorkspaceMember(
            workspace_id=workspace.id,
            user_id=user.id,
            role="owner",
        )
        session.add(membership)
        session.commit()

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
