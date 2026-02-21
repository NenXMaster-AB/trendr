from __future__ import annotations

from dataclasses import dataclass

import pytest
from fastapi import HTTPException
from sqlmodel import Session, select

from trendr_api.api.provider_settings import (
    delete_text_provider_setting,
    list_text_provider_settings,
    upsert_text_provider_setting,
)
from trendr_api.auth import AuthContext, resolve_auth_context
from trendr_api.models import WorkspaceMember
from trendr_api.plugins.registry import registry
from trendr_api.plugins.types import ProviderCapabilities
from trendr_api.schemas import ProviderApiKeyUpdate


@dataclass
class _TextProvider:
    name: str
    capabilities: ProviderCapabilities

    def is_available(self, *, meta: dict | None = None) -> bool:
        return True

    async def generate(self, *, prompt: str, system: str | None = None, meta: dict | None = None) -> str:
        return "ok"


def _seed_provider_registry():
    original_text = dict(registry.text_providers)
    registry.text_providers.clear()
    registry.register_text(
        _TextProvider(
            name="openai",
            capabilities=ProviderCapabilities(max_input_tokens=10_000),
        )
    )
    return original_text


def test_provider_settings_round_trip(db_session: Session, actor: AuthContext):
    original_text = _seed_provider_registry()
    try:
        saved = upsert_text_provider_setting(
            "openai",
            ProviderApiKeyUpdate(api_key="sk-trendr-test-123456789"),
            session=db_session,
            actor=actor,
        )
        assert saved.provider == "openai"
        assert saved.has_api_key is True
        assert saved.configured_via == "workspace"
        assert saved.key_hint == "***6789"

        listed = list_text_provider_settings(session=db_session, actor=actor)
        openai_row = next(row for row in listed if row.provider == "openai")
        assert openai_row.has_api_key is True
        assert openai_row.configured_via == "workspace"

        deleted = delete_text_provider_setting("openai", session=db_session, actor=actor)
        assert deleted["ok"] is True
    finally:
        registry.text_providers.clear()
        registry.text_providers.update(original_text)


def test_provider_settings_require_admin_role(db_session: Session, actor: AuthContext):
    original_text = _seed_provider_registry()
    try:
        membership = db_session.exec(
            select(WorkspaceMember).where(
                WorkspaceMember.workspace_id == actor.workspace_id,
                WorkspaceMember.user_id == actor.user_id,
            )
        ).first()
        assert membership is not None
        membership.role = "member"
        db_session.add(membership)
        db_session.commit()

        member_actor = resolve_auth_context(
            session=db_session,
            user_external_id=actor.user_external_id,
            workspace_slug=actor.workspace_slug,
        )

        with pytest.raises(HTTPException) as exc:
            upsert_text_provider_setting(
                "openai",
                ProviderApiKeyUpdate(api_key="sk-trendr-test-123456789"),
                session=db_session,
                actor=member_actor,
            )
        assert exc.value.status_code == 403
    finally:
        registry.text_providers.clear()
        registry.text_providers.update(original_text)


def test_provider_settings_reject_unknown_provider(db_session: Session, actor: AuthContext):
    original_text = dict(registry.text_providers)
    registry.text_providers.clear()
    try:
        with pytest.raises(HTTPException) as exc:
            upsert_text_provider_setting(
                "unknown-provider",
                ProviderApiKeyUpdate(api_key="sk-trendr-test-123456789"),
                session=db_session,
                actor=actor,
            )
        assert exc.value.status_code == 404
    finally:
        registry.text_providers.clear()
        registry.text_providers.update(original_text)
