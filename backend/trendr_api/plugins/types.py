from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, Optional, Protocol


@dataclass(frozen=True)
class ProviderCapabilities:
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
    supports_json_mode: bool = False
    supports_streaming: bool = False
    supports_system_prompt: bool = True


class TextProvider(Protocol):
    name: str
    capabilities: ProviderCapabilities

    def is_available(self) -> bool:
        ...

    async def generate(
        self,
        *,
        prompt: str,
        system: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> str:
        ...


class ImageProvider(Protocol):
    name: str
    capabilities: ProviderCapabilities

    def is_available(self) -> bool:
        ...

    async def generate_image(
        self,
        *,
        prompt: str,
        size: str = "1024x1024",
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return dict with at least: { 'url': str } or { 'b64': str }"""
        ...
