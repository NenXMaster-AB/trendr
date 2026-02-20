from __future__ import annotations
from dataclasses import asdict
from typing import Any, Dict

from .types import ImageProvider, TextProvider


class PluginRegistry:
    def __init__(self) -> None:
        self.text_providers: Dict[str, TextProvider] = {}
        self.image_providers: Dict[str, ImageProvider] = {}

    def register_text(self, provider: TextProvider) -> None:
        self.text_providers[provider.name] = provider

    def register_image(self, provider: ImageProvider) -> None:
        self.image_providers[provider.name] = provider

    def get_text(self, name: str) -> TextProvider:
        if name not in self.text_providers:
            raise KeyError(f"Unknown text provider: {name}")
        return self.text_providers[name]

    def get_image(self, name: str) -> ImageProvider:
        if name not in self.image_providers:
            raise KeyError(f"Unknown image provider: {name}")
        return self.image_providers[name]

    def list_text(self) -> list[str]:
        return sorted(self.text_providers.keys())

    def list_image(self) -> list[str]:
        return sorted(self.image_providers.keys())

    def text_provider_info(self, name: str) -> dict[str, Any]:
        provider = self.get_text(name)
        capabilities = getattr(provider, "capabilities", None)
        return {
            "name": provider.name,
            "available": bool(provider.is_available()),
            "capabilities": asdict(capabilities) if capabilities is not None else {},
        }

    def image_provider_info(self, name: str) -> dict[str, Any]:
        provider = self.get_image(name)
        capabilities = getattr(provider, "capabilities", None)
        return {
            "name": provider.name,
            "available": bool(provider.is_available()),
            "capabilities": asdict(capabilities) if capabilities is not None else {},
        }


registry = PluginRegistry()
