from __future__ import annotations

from fastapi import APIRouter, Depends

from ..auth import AuthContext, require_auth
from ..plugins.registry import registry
from ..schemas import ProviderCapabilitiesOut, ProviderOut

router = APIRouter(prefix="/providers", tags=["providers"])


def _to_provider_out(info: dict) -> ProviderOut:
    return ProviderOut(
        name=str(info["name"]),
        available=bool(info["available"]),
        capabilities=ProviderCapabilitiesOut(**dict(info.get("capabilities") or {})),
    )


@router.get("/text", response_model=list[ProviderOut])
def list_text_providers(actor: AuthContext = Depends(require_auth)):
    return [_to_provider_out(registry.text_provider_info(name)) for name in registry.list_text()]


@router.get("/image", response_model=list[ProviderOut])
def list_image_providers(actor: AuthContext = Depends(require_auth)):
    return [_to_provider_out(registry.image_provider_info(name)) for name in registry.list_image()]
