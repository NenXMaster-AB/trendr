from __future__ import annotations

from typing import Any, Dict, Optional

import httpx
from sqlmodel import Session

from ...config import settings
from ...db import engine
from ...services.provider_settings import get_workspace_provider_api_key
from ..registry import registry
from ..types import ProviderCapabilities


class OpenAIImageProvider:
    name = "openai_image"
    capabilities = ProviderCapabilities(
        max_input_tokens=4000,
        max_output_tokens=None,
        supports_json_mode=False,
        supports_streaming=False,
        supports_system_prompt=False,
    )

    def __init__(self) -> None:
        self._api_key = settings.openai_api_key
        self._model = settings.dalle_model
        self._base_url = settings.openai_base_url.rstrip("/")

    def _workspace_api_key(self, workspace_id: int | None) -> str | None:
        if workspace_id is None:
            return None
        with Session(engine) as session:
            return get_workspace_provider_api_key(
                session=session,
                workspace_id=workspace_id,
                provider="openai",
            )

    def _resolve_api_key(self, meta: Optional[Dict[str, Any]]) -> str | None:
        request_meta = meta or {}
        workspace_raw = request_meta.get("workspace_id")
        workspace_id: int | None
        try:
            workspace_id = int(workspace_raw) if workspace_raw is not None else None
        except (TypeError, ValueError):
            workspace_id = None
        workspace_key = self._workspace_api_key(workspace_id)
        return workspace_key or self._api_key

    def is_available(self, *, meta: Optional[Dict[str, Any]] = None) -> bool:
        return bool(self._resolve_api_key(meta))

    async def generate_image(
        self,
        *,
        prompt: str,
        size: str = "1024x1024",
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        resolved_api_key = self._resolve_api_key(meta)
        if not resolved_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured for image generation")

        request_meta = meta or {}
        payload: dict[str, Any] = {
            "model": self._model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "b64_json",
        }

        quality = request_meta.get("quality")
        if isinstance(quality, str) and quality in ("standard", "hd"):
            payload["quality"] = quality

        style = request_meta.get("style")
        if isinstance(style, str) and style in ("vivid", "natural"):
            payload["style"] = style

        url = f"{self._base_url}/images/generations"
        headers = {
            "Authorization": f"Bearer {resolved_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code >= 400:
            detail = response.text.strip()
            if len(detail) > 500:
                detail = f"{detail[:500]}..."
            raise RuntimeError(f"OpenAI Images API {response.status_code}: {detail}")

        data = response.json()
        items = data.get("data")
        if not isinstance(items, list) or not items:
            raise RuntimeError("OpenAI Images API returned no data")

        item = items[0]
        result: Dict[str, Any] = {"size": size}

        b64 = item.get("b64_json")
        if isinstance(b64, str) and b64:
            result["b64"] = b64

        revised = item.get("revised_prompt")
        if isinstance(revised, str) and revised:
            result["revised_prompt"] = revised

        image_url = item.get("url")
        if isinstance(image_url, str) and image_url:
            result["url"] = image_url

        return result


def register() -> None:
    registry.register_image(OpenAIImageProvider())
