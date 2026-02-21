from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from ..models import ProviderCredential
from ..security import decrypt_secret, encrypt_secret, secret_hint


def get_workspace_provider_credential(
    *,
    session: Session,
    workspace_id: int,
    provider: str,
) -> ProviderCredential | None:
    return session.exec(
        select(ProviderCredential).where(
            ProviderCredential.workspace_id == workspace_id,
            ProviderCredential.provider == provider,
        )
    ).first()


def get_workspace_provider_api_key(
    *,
    session: Session,
    workspace_id: int,
    provider: str,
) -> Optional[str]:
    record = get_workspace_provider_credential(
        session=session,
        workspace_id=workspace_id,
        provider=provider,
    )
    if not record:
        return None
    return decrypt_secret(record.encrypted_api_key)


def upsert_workspace_provider_api_key(
    *,
    session: Session,
    workspace_id: int,
    provider: str,
    api_key: str,
) -> ProviderCredential:
    encrypted = encrypt_secret(api_key)
    hint = secret_hint(api_key)
    now = datetime.utcnow()

    record = get_workspace_provider_credential(
        session=session,
        workspace_id=workspace_id,
        provider=provider,
    )
    if record is None:
        record = ProviderCredential(
            workspace_id=workspace_id,
            provider=provider,
            encrypted_api_key=encrypted,
            key_hint=hint,
            created_at=now,
            updated_at=now,
        )
    else:
        record.encrypted_api_key = encrypted
        record.key_hint = hint
        record.updated_at = now

    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def delete_workspace_provider_api_key(
    *,
    session: Session,
    workspace_id: int,
    provider: str,
) -> bool:
    record = get_workspace_provider_credential(
        session=session,
        workspace_id=workspace_id,
        provider=provider,
    )
    if not record:
        return False
    session.delete(record)
    session.commit()
    return True
