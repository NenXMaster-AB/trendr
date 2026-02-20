from __future__ import annotations

from fastapi import HTTPException
from sqlmodel import Session

from trendr_api.auth import AuthContext
from trendr_api.api.templates import create_template, delete_template, list_templates, update_template
from trendr_api.schemas import TemplateCreate, TemplateUpdate


def test_create_template_auto_increments_version(db_session: Session, actor: AuthContext):
    first = create_template(
        TemplateCreate(name="Main", kind="tweet", content="Tone: {tone}"),
        session=db_session,
        actor=actor,
    )
    second = create_template(
        TemplateCreate(name="Main", kind="tweet", content="Tone: {tone}\\nTranscript: {transcript}"),
        session=db_session,
        actor=actor,
    )

    assert first.version == 1
    assert second.version == 2


def test_list_templates_filters_workspace_and_kind(
    db_session: Session,
    actor: AuthContext,
    other_actor: AuthContext,
):
    create_template(
        TemplateCreate(name="Tweet A", kind="tweet", content="Tweet template"),
        session=db_session,
        actor=actor,
    )
    create_template(
        TemplateCreate(name="Blog A", kind="blog", content="Blog template"),
        session=db_session,
        actor=actor,
    )
    create_template(
        TemplateCreate(name="Tweet B", kind="tweet", content="Other workspace"),
        session=db_session,
        actor=other_actor,
    )

    actor_items = list_templates(session=db_session, actor=actor)
    actor_tweets = list_templates(kind="tweet", session=db_session, actor=actor)
    other_items = list_templates(session=db_session, actor=other_actor)

    assert len(actor_items) == 2
    assert len(actor_tweets) == 1
    assert actor_tweets[0].kind == "tweet"
    assert len(other_items) == 1


def test_update_and_delete_template_are_workspace_scoped(
    db_session: Session,
    actor: AuthContext,
    other_actor: AuthContext,
):
    item = create_template(
        TemplateCreate(name="Draft", kind="linkedin", content="Old"),
        session=db_session,
        actor=actor,
    )

    updated = update_template(
        template_id=item.id,
        payload=TemplateUpdate(content="New", name="Draft v1"),
        session=db_session,
        actor=actor,
    )
    assert updated.content == "New"
    assert updated.name == "Draft v1"

    try:
        update_template(
            template_id=item.id,
            payload=TemplateUpdate(content="Bad"),
            session=db_session,
            actor=other_actor,
        )
        raise AssertionError("expected HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 404

    delete_result = delete_template(template_id=item.id, session=db_session, actor=actor)
    assert delete_result["ok"] is True

    try:
        delete_template(template_id=item.id, session=db_session, actor=actor)
        raise AssertionError("expected HTTPException")
    except HTTPException as exc:
        assert exc.status_code == 404
