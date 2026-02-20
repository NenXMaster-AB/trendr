from __future__ import annotations

from sqlmodel import Session

from trendr_api.api.jobs import list_jobs
from trendr_api.models import Job, Project


def _seed_jobs(session: Session):
    p1 = Project(name="P1", source_type="youtube", source_ref="url-1")
    p2 = Project(name="P2", source_type="youtube", source_ref="url-2")
    session.add(p1)
    session.add(p2)
    session.commit()
    session.refresh(p1)
    session.refresh(p2)

    jobs = [
        Job(kind="ingest", status="succeeded", project_id=p1.id, input={}, output={}),
        Job(kind="generate", status="queued", project_id=p1.id, input={}, output={}),
        Job(kind="ingest", status="failed", project_id=p2.id, input={}, output={}),
    ]
    for job in jobs:
        session.add(job)
    session.commit()
    return p1.id, p2.id


def test_list_jobs_filters_by_project_id(db_session: Session):
    p1_id, _ = _seed_jobs(db_session)
    items = list_jobs(project_id=p1_id, limit=20, session=db_session)
    assert len(items) == 2
    assert all(item.project_id == p1_id for item in items)


def test_list_jobs_applies_limit_bounds(db_session: Session):
    _seed_jobs(db_session)
    assert len(list_jobs(limit=1, session=db_session)) == 1
    # Router clamps lower bound to 1.
    assert len(list_jobs(limit=0, session=db_session)) == 1
