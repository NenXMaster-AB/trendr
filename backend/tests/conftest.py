from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

from trendr_api.auth import AuthContext, resolve_auth_context

@pytest.fixture
def sqlite_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def db_session(sqlite_engine) -> Generator[Session, None, None]:
    with Session(sqlite_engine) as session:
        yield session


@pytest.fixture
def actor(db_session: Session) -> AuthContext:
    return resolve_auth_context(
        session=db_session,
        user_external_id="test-user",
        workspace_slug="test-workspace",
    )


@pytest.fixture
def other_actor(db_session: Session) -> AuthContext:
    return resolve_auth_context(
        session=db_session,
        user_external_id="other-user",
        workspace_slug="other-workspace",
    )
