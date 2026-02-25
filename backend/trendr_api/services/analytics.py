from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import func, String, cast
from sqlmodel import Session, select

from ..models import Event


def record_event(
    session: Session,
    *,
    workspace_id: int,
    project_id: Optional[int] = None,
    kind: str,
    meta: Optional[Dict[str, Any]] = None,
) -> Event:
    event = Event(
        workspace_id=workspace_id,
        project_id=project_id,
        kind=kind,
        meta=meta or {},
        created_at=datetime.utcnow(),
    )
    session.add(event)
    session.commit()
    session.refresh(event)
    return event


def get_summary(
    session: Session,
    *,
    workspace_id: int,
    days: int = 30,
) -> list[dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    stmt = (
        select(Event.kind, func.count(Event.id).label("count"))
        .where(
            Event.workspace_id == workspace_id,
            Event.created_at >= cutoff,
        )
        .group_by(Event.kind)
        .order_by(func.count(Event.id).desc())
    )
    rows = session.exec(stmt).all()
    return [{"kind": row[0], "count": row[1]} for row in rows]


def get_timeline(
    session: Session,
    *,
    workspace_id: int,
    days: int = 30,
) -> list[dict[str, Any]]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    date_expr = func.substr(cast(Event.created_at, String), 1, 10).label("date")
    stmt = (
        select(date_expr, Event.kind, func.count(Event.id).label("count"))
        .where(
            Event.workspace_id == workspace_id,
            Event.created_at >= cutoff,
        )
        .group_by(date_expr, Event.kind)
        .order_by(date_expr)
    )
    rows = session.exec(stmt).all()
    return [{"date": str(row[0]), "kind": row[1], "count": row[2]} for row in rows]
