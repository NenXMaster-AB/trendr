from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

from ...config import settings
from ..registry import registry
from ..types import ProviderCapabilities


class OpenAITextProvider:
    name = "openai"
    capabilities = ProviderCapabilities(
        max_input_tokens=128_000,
        max_output_tokens=16_384,
        supports_json_mode=True,
        supports_streaming=False,
        supports_system_prompt=True,
    )

    def __init__(self) -> None:
        self._api_key = settings.openai_api_key
        self._model = settings.openai_model
        self._base_url = settings.openai_base_url.rstrip("/")

    def is_available(self) -> bool:
        return bool(self._api_key)

    async def generate(
        self,
        *,
        prompt: str,
        system: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not self._api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")

        request_meta = meta or {}
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
        }

        temperature = request_meta.get("temperature")
        if isinstance(temperature, (int, float)):
            payload["temperature"] = float(temperature)

        max_tokens = request_meta.get("max_output_tokens")
        if isinstance(max_tokens, int) and max_tokens > 0:
            payload["max_tokens"] = max_tokens

        url = f"{self._base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code >= 400:
            detail = response.text.strip()
            if len(detail) > 500:
                detail = f"{detail[:500]}..."
            raise RuntimeError(f"OpenAI API {response.status_code}: {detail}")

        data = response.json()
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenAI API returned no choices")

        message = choices[0].get("message")
        if not isinstance(message, dict):
            raise RuntimeError("OpenAI API response missing message")

        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        raise RuntimeError("OpenAI API response missing text content")


def register() -> None:
    registry.register_text(OpenAITextProvider())
