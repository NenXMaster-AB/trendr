from __future__ import annotations

from sqlmodel import Session

from trendr_api.auth import AuthContext
from trendr_api.services.analytics import get_summary, get_timeline, record_event


def test_record_event(db_session: Session, actor: AuthContext):
    event = record_event(
        db_session,
        workspace_id=actor.workspace_id,
        kind="job_completed",
        meta={"job_id": 1},
    )
    assert event.id is not None
    assert event.kind == "job_completed"


def test_get_summary(db_session: Session, actor: AuthContext):
    record_event(db_session, workspace_id=actor.workspace_id, kind="job_completed")
    record_event(db_session, workspace_id=actor.workspace_id, kind="job_completed")
    record_event(db_session, workspace_id=actor.workspace_id, kind="artifact_created")

    summary = get_summary(db_session, workspace_id=actor.workspace_id, days=30)
    kinds = {s["kind"]: s["count"] for s in summary}
    assert kinds["job_completed"] == 2
    assert kinds["artifact_created"] == 1


def test_get_summary_excludes_other_workspace(
    db_session: Session, actor: AuthContext, other_actor: AuthContext
):
    record_event(db_session, workspace_id=actor.workspace_id, kind="job_completed")
    record_event(db_session, workspace_id=other_actor.workspace_id, kind="job_completed")

    summary = get_summary(db_session, workspace_id=actor.workspace_id, days=30)
    assert len(summary) == 1
    assert summary[0]["count"] == 1


def test_get_timeline(db_session: Session, actor: AuthContext):
    record_event(db_session, workspace_id=actor.workspace_id, kind="job_completed")
    record_event(db_session, workspace_id=actor.workspace_id, kind="artifact_created")

    timeline = get_timeline(db_session, workspace_id=actor.workspace_id, days=30)
    assert len(timeline) >= 1
    assert all("date" in point and "kind" in point and "count" in point for point in timeline)
