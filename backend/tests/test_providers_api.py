from __future__ import annotations

from dataclasses import dataclass

from trendr_api.api.providers import list_image_providers, list_text_providers
from trendr_api.auth import AuthContext
from trendr_api.plugins.registry import registry
from trendr_api.plugins.types import ProviderCapabilities


@dataclass
class _TextProvider:
    name: str
    available: bool
    capabilities: ProviderCapabilities

    def is_available(self) -> bool:
        return self.available

    async def generate(self, *, prompt: str, system: str | None = None, meta: dict | None = None) -> str:
        return "ok"


@dataclass
class _ImageProvider:
    name: str
    available: bool
    capabilities: ProviderCapabilities

    def is_available(self) -> bool:
        return self.available

    async def generate_image(self, *, prompt: str, size: str = "1024x1024", meta: dict | None = None) -> dict:
        return {"url": "https://example.com"}


def test_provider_listing_returns_capabilities(actor: AuthContext):
    original_text = dict(registry.text_providers)
    original_image = dict(registry.image_providers)

    registry.text_providers.clear()
    registry.image_providers.clear()
    try:
        registry.register_text(
            _TextProvider(
                name="openai",
                available=True,
                capabilities=ProviderCapabilities(max_input_tokens=1000, supports_json_mode=True),
            )
        )
        registry.register_image(
            _ImageProvider(
                name="nanobanana",
                available=False,
                capabilities=ProviderCapabilities(supports_streaming=False),
            )
        )

        text_rows = list_text_providers(actor=actor)
        image_rows = list_image_providers(actor=actor)

        assert len(text_rows) == 1
        assert text_rows[0].name == "openai"
        assert text_rows[0].available is True
        assert text_rows[0].capabilities.max_input_tokens == 1000
        assert text_rows[0].capabilities.supports_json_mode is True

        assert len(image_rows) == 1
        assert image_rows[0].name == "nanobanana"
        assert image_rows[0].available is False
    finally:
        registry.text_providers.clear()
        registry.text_providers.update(original_text)
        registry.image_providers.clear()
        registry.image_providers.update(original_image)
