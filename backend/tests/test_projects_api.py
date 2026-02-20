from __future__ import annotations

from fastapi import HTTPException
from sqlmodel import Session

from trendr_api.auth import AuthContext
from trendr_api.api.projects import create_project, get_project, list_projects
from trendr_api.schemas import ProjectCreate


def test_projects_are_scoped_to_workspace(db_session: Session, actor: AuthContext, other_actor: AuthContext):
    p1 = create_project(
        ProjectCreate(name="A", source_ref="https://youtu.be/dQw4w9WgXcQ"),
        session=db_session,
        actor=actor,
    )
    p2 = create_project(
        ProjectCreate(name="B", source_ref="https://youtu.be/oHg5SJYRHA0"),
        session=db_session,
        actor=other_actor,
    )

    actor_projects = list_projects(session=db_session, actor=actor)
    other_projects = list_projects(session=db_session, actor=other_actor)

    assert len(actor_projects) == 1
    assert len(other_projects) == 1
    assert actor_projects[0].id == p1.id
    assert other_projects[0].id == p2.id


def test_get_project_blocks_cross_workspace_access(
    db_session: Session,
    actor: AuthContext,
    other_actor: AuthContext,
):
    p1 = create_project(
        ProjectCreate(name="A", source_ref="https://youtu.be/dQw4w9WgXcQ"),
        session=db_session,
        actor=actor,
    )

    # Owner can fetch.
    own = get_project(project_id=p1.id, session=db_session, actor=actor)
    assert own.id == p1.id

    # Other workspace sees 404.
    try:
        get_project(project_id=p1.id, session=db_session, actor=other_actor)
        raise AssertionError("expected HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 404
