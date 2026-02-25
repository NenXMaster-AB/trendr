from __future__ import annotations

from datetime import datetime, timedelta

from sqlmodel import Session, select

from trendr_api.models import ScheduledPost, Workspace


def _seed_workspace(session: Session) -> int:
    ws = Workspace(name="Test", slug="test-ws")
    session.add(ws)
    session.commit()
    session.refresh(ws)
    return ws.id


def test_check_scheduled_posts_marks_past_due(sqlite_engine):
    from trendr_api.worker import tasks

    with Session(sqlite_engine) as session:
        ws_id = _seed_workspace(session)

        past = ScheduledPost(
            workspace_id=ws_id,
            platform="twitter",
            title="Past",
            content="past",
            scheduled_at=datetime.utcnow() - timedelta(hours=1),
            status="scheduled",
        )
        future = ScheduledPost(
            workspace_id=ws_id,
            platform="twitter",
            title="Future",
            content="future",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
            status="scheduled",
        )
        session.add(past)
        session.add(future)
        session.commit()

    # Monkey-patch the engine used by tasks
    original_engine = tasks.engine
    tasks.engine = sqlite_engine
    try:
        result = tasks.check_scheduled_posts()
    finally:
        tasks.engine = original_engine

    assert result["marked_ready"] == 1

    with Session(sqlite_engine) as session:
        posts = session.exec(select(ScheduledPost)).all()
        statuses = {p.title: p.status for p in posts}
        assert statuses["Past"] == "ready"
        assert statuses["Future"] == "scheduled"
