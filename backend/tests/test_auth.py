from __future__ import annotations

import pytest
from fastapi import HTTPException
from sqlmodel import Session, select

from trendr_api.auth import require_auth, resolve_auth_context
from trendr_api.models import WorkspaceMember


def test_resolve_auth_context_is_idempotent(db_session: Session):
    first = resolve_auth_context(
        session=db_session,
        user_external_id="demo-user",
        workspace_slug="demo-workspace",
    )
    second = resolve_auth_context(
        session=db_session,
        user_external_id="demo-user",
        workspace_slug="demo-workspace",
    )

    assert first.user_id == second.user_id
    assert first.workspace_id == second.workspace_id

    memberships = db_session.exec(
        select(WorkspaceMember).where(
            WorkspaceMember.user_id == first.user_id,
            WorkspaceMember.workspace_id == first.workspace_id,
        )
    ).all()
    assert len(memberships) == 1


def test_require_auth_rejects_missing_user_header(db_session: Session):
    with pytest.raises(HTTPException) as exc:
        require_auth(session=db_session, x_user_id=None, x_workspace_slug="default")
    assert exc.value.status_code == 401
