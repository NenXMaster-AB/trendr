from __future__ import annotations

from contextvars import ContextVar


_request_id_var: ContextVar[str | None] = ContextVar("trendr_request_id", default=None)
_job_id_var: ContextVar[str | None] = ContextVar("trendr_job_id", default=None)


def set_request_id(request_id: str | None) -> None:
    _request_id_var.set(request_id)


def get_request_id() -> str | None:
    return _request_id_var.get()


def clear_request_id() -> None:
    _request_id_var.set(None)


def set_job_id(job_id: int | str | None) -> None:
    _job_id_var.set(str(job_id) if job_id is not None else None)


def get_job_id() -> str | None:
    return _job_id_var.get()


def clear_job_id() -> None:
    _job_id_var.set(None)
