from __future__ import annotations

from sqlmodel import Session

from trendr_api.auth import AuthContext
from trendr_api.api.jobs import list_jobs
from trendr_api.models import Job, Project


def _seed_jobs(session: Session, actor: AuthContext, other_actor: AuthContext):
    p1 = Project(workspace_id=actor.workspace_id, name="P1", source_type="youtube", source_ref="url-1")
    p2 = Project(workspace_id=other_actor.workspace_id, name="P2", source_type="youtube", source_ref="url-2")
    session.add(p1)
    session.add(p2)
    session.commit()
    session.refresh(p1)
    session.refresh(p2)

    jobs = [
        Job(kind="ingest", status="succeeded", workspace_id=actor.workspace_id, project_id=p1.id, input={}, output={}),
        Job(kind="generate", status="queued", workspace_id=actor.workspace_id, project_id=p1.id, input={}, output={}),
        Job(kind="ingest", status="failed", workspace_id=other_actor.workspace_id, project_id=p2.id, input={}, output={}),
    ]
    for job in jobs:
        session.add(job)
    session.commit()
    return p1.id, p2.id


def test_list_jobs_filters_by_project_id(db_session: Session, actor: AuthContext, other_actor: AuthContext):
    p1_id, _ = _seed_jobs(db_session, actor, other_actor)
    items = list_jobs(project_id=p1_id, limit=20, session=db_session, actor=actor)
    assert len(items) == 2
    assert all(item.project_id == p1_id for item in items)


def test_list_jobs_applies_limit_bounds(db_session: Session, actor: AuthContext, other_actor: AuthContext):
    _seed_jobs(db_session, actor, other_actor)
    assert len(list_jobs(limit=1, session=db_session, actor=actor)) == 1
    # Router clamps lower bound to 1.
    assert len(list_jobs(limit=0, session=db_session, actor=actor)) == 1


def test_list_jobs_scoped_to_workspace(db_session: Session, actor: AuthContext, other_actor: AuthContext):
    _seed_jobs(db_session, actor, other_actor)
    actor_items = list_jobs(limit=20, session=db_session, actor=actor)
    other_items = list_jobs(limit=20, session=db_session, actor=other_actor)
    assert len(actor_items) == 2
    assert len(other_items) == 1
    assert all(item.workspace_id == actor.workspace_id for item in actor_items)
    assert all(item.workspace_id == other_actor.workspace_id for item in other_items)
