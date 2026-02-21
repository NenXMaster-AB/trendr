from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from ..auth import AuthContext, require_auth, require_workspace_role
from ..config import settings
from ..db import get_session
from ..plugins.registry import registry
from ..schemas import ProviderApiKeyUpdate, ProviderSettingOut
from ..services.provider_settings import (
    delete_workspace_provider_api_key,
    get_workspace_provider_credential,
    upsert_workspace_provider_api_key,
)

router = APIRouter(prefix="/provider-settings", tags=["provider-settings"])


def _validate_provider(provider_name: str) -> None:
    if provider_name not in registry.list_text():
        raise HTTPException(status_code=404, detail=f"Unknown text provider '{provider_name}'")


def _to_setting_out(*, provider_name: str, workspace_id: int, session: Session) -> ProviderSettingOut:
    record = get_workspace_provider_credential(
        session=session,
        workspace_id=workspace_id,
        provider=provider_name,
    )
    if record:
        return ProviderSettingOut(
            provider=provider_name,
            has_api_key=True,
            key_hint=record.key_hint or None,
            configured_via="workspace",
            updated_at=record.updated_at,
        )

    env_available = provider_name == "openai" and bool(settings.openai_api_key)
    return ProviderSettingOut(
        provider=provider_name,
        has_api_key=env_available,
        configured_via="environment" if env_available else None,
    )


@router.get("/text", response_model=list[ProviderSettingOut])
def list_text_provider_settings(
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    return [
        _to_setting_out(provider_name=name, workspace_id=actor.workspace_id, session=session)
        for name in registry.list_text()
    ]


@router.put("/text/{provider_name}", response_model=ProviderSettingOut)
def upsert_text_provider_setting(
    provider_name: str,
    payload: ProviderApiKeyUpdate,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    _validate_provider(provider_name)
    require_workspace_role(actor, "admin")
    upsert_workspace_provider_api_key(
        session=session,
        workspace_id=actor.workspace_id,
        provider=provider_name,
        api_key=payload.api_key,
    )
    return _to_setting_out(
        provider_name=provider_name,
        workspace_id=actor.workspace_id,
        session=session,
    )


@router.delete("/text/{provider_name}")
def delete_text_provider_setting(
    provider_name: str,
    session: Session = Depends(get_session),
    actor: AuthContext = Depends(require_auth),
):
    _validate_provider(provider_name)
    require_workspace_role(actor, "admin")
    deleted = delete_workspace_provider_api_key(
        session=session,
        workspace_id=actor.workspace_id,
        provider=provider_name,
    )
    return {"ok": deleted}
