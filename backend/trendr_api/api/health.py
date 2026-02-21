from __future__ import annotations

from fastapi import APIRouter, Response, status
from redis import Redis
from sqlalchemy import text

from ..config import settings
from ..db import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health(response: Response):
    checks: dict[str, dict[str, str]] = {
        "db": {"status": "ok"},
        "redis": {"status": "ok"},
    }

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        checks["db"] = {"status": "error", "detail": str(exc)}

    try:
        client = Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
        client.ping()
    except Exception as exc:
        checks["redis"] = {"status": "error", "detail": str(exc)}

    overall = "ok" if all(item["status"] == "ok" for item in checks.values()) else "degraded"
    if overall != "ok":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {"status": overall, "checks": checks}
