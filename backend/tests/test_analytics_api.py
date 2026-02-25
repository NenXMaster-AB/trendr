from __future__ import annotations

from sqlmodel import Session

from trendr_api.auth import AuthContext
from trendr_api.api.analytics import analytics_summary, analytics_timeline
from trendr_api.services.analytics import record_event


def test_analytics_summary_endpoint(db_session: Session, actor: AuthContext):
    record_event(db_session, workspace_id=actor.workspace_id, kind="job_completed")
    record_event(db_session, workspace_id=actor.workspace_id, kind="artifact_created")

    result = analytics_summary(session=db_session, actor=actor, days=30)
    assert len(result) == 2
    kinds = {r.kind for r in result}
    assert "job_completed" in kinds
    assert "artifact_created" in kinds


def test_analytics_timeline_endpoint(db_session: Session, actor: AuthContext):
    record_event(db_session, workspace_id=actor.workspace_id, kind="job_completed")

    result = analytics_timeline(session=db_session, actor=actor, days=30)
    assert len(result) >= 1
    assert result[0].kind == "job_completed"
    assert result[0].count == 1
