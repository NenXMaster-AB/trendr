from __future__ import annotations

from fastapi import Response, status

from trendr_api.api import health as health_api


class _RedisOK:
    def ping(self) -> bool:
        return True


class _RedisFail:
    def ping(self) -> bool:
        raise RuntimeError("redis down")


def test_health_returns_ok_when_db_and_redis_are_available(sqlite_engine, monkeypatch):
    monkeypatch.setattr(health_api, "engine", sqlite_engine)
    monkeypatch.setattr(health_api.Redis, "from_url", lambda *args, **kwargs: _RedisOK())

    response = Response()
    payload = health_api.health(response)

    assert response.status_code == status.HTTP_200_OK
    assert payload["status"] == "ok"
    assert payload["checks"]["db"]["status"] == "ok"
    assert payload["checks"]["redis"]["status"] == "ok"


def test_health_returns_503_when_redis_check_fails(sqlite_engine, monkeypatch):
    monkeypatch.setattr(health_api, "engine", sqlite_engine)
    monkeypatch.setattr(health_api.Redis, "from_url", lambda *args, **kwargs: _RedisFail())

    response = Response()
    payload = health_api.health(response)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert payload["status"] == "degraded"
    assert payload["checks"]["db"]["status"] == "ok"
    assert payload["checks"]["redis"]["status"] == "error"
