from __future__ import annotations
from typing import Dict, Optional
from .types import TextProvider, ImageProvider


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


registry = PluginRegistry()
