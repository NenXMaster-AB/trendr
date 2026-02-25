from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import HTTPException
import pytest
from sqlmodel import Session

from trendr_api.auth import AuthContext
from trendr_api.api.schedule import (
    create_scheduled_post,
    delete_scheduled_post,
    list_scheduled_posts,
    update_scheduled_post,
)
from trendr_api.schemas import ScheduledPostCreate, ScheduledPostUpdate


def _create(session: Session, actor: AuthContext, **kwargs) -> int:
    defaults = {
        "platform": "twitter",
        "title": "Test",
        "content": "Hello world",
        "scheduled_at": datetime.utcnow() + timedelta(hours=1),
    }
    defaults.update(kwargs)
    post = create_scheduled_post(
        ScheduledPostCreate(**defaults),
        session=session,
        actor=actor,
    )
    return post.id


def test_create_scheduled_post(db_session: Session, actor: AuthContext):
    post = create_scheduled_post(
        ScheduledPostCreate(
            platform="twitter",
            title="Tweet 1",
            content="Hello",
            scheduled_at=datetime.utcnow() + timedelta(hours=1),
        ),
        session=db_session,
        actor=actor,
    )
    assert post.status == "scheduled"
    assert post.platform == "twitter"


def test_list_scheduled_posts(db_session: Session, actor: AuthContext):
    _create(db_session, actor, title="A")
    _create(db_session, actor, title="B")

    posts = list_scheduled_posts(
        session=db_session,
        actor=actor,
        project_id=None,
        status=None,
        platform=None,
        limit=50,
    )
    assert len(posts) == 2


def test_list_filters_by_status(db_session: Session, actor: AuthContext):
    post_id = _create(db_session, actor, title="A")
    _create(db_session, actor, title="B")

    delete_scheduled_post(post_id, session=db_session, actor=actor)

    posts = list_scheduled_posts(
        session=db_session,
        actor=actor,
        project_id=None,
        status="cancelled",
        platform=None,
        limit=50,
    )
    assert len(posts) == 1
    assert posts[0].title == "A"


def test_update_scheduled_post(db_session: Session, actor: AuthContext):
    post_id = _create(db_session, actor)
    updated = update_scheduled_post(
        post_id,
        ScheduledPostUpdate(title="Updated"),
        session=db_session,
        actor=actor,
    )
    assert updated.title == "Updated"


def test_update_cross_workspace_fails(
    db_session: Session,
    actor: AuthContext,
    other_actor: AuthContext,
):
    post_id = _create(db_session, actor)

    with pytest.raises(HTTPException) as exc:
        update_scheduled_post(
            post_id,
            ScheduledPostUpdate(title="hacked"),
            session=db_session,
            actor=other_actor,
        )
    assert exc.value.status_code == 404


def test_delete_cancels_post(db_session: Session, actor: AuthContext):
    post_id = _create(db_session, actor)
    result = delete_scheduled_post(post_id, session=db_session, actor=actor)
    assert result.status == "cancelled"
