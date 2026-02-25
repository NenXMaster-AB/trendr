from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from ..auth import AuthContext, require_auth
from ..db import get_session
from ..schemas import AnalyticsSummaryOut, TimelinePointOut
from ..services.analytics import get_summary, get_timeline

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/summary", response_model=list[AnalyticsSummaryOut])
def analytics_summary(
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
    days: int = Query(default=30, ge=1, le=365),
):
    rows = get_summary(session, workspace_id=actor.workspace_id, days=days)
    return [AnalyticsSummaryOut(**r) for r in rows]


@router.get("/timeline", response_model=list[TimelinePointOut])
def analytics_timeline(
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
    days: int = Query(default=30, ge=1, le=365),
):
    rows = get_timeline(session, workspace_id=actor.workspace_id, days=days)
    return [TimelinePointOut(**r) for r in rows]
