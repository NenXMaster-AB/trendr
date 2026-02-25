from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from trendr_api.config import settings
from trendr_api.plugins.registry import registry
from trendr_api.plugins.router import generate_image
from trendr_api.plugins.types import ProviderCapabilities


@dataclass
class _FakeImageProvider:
    name: str
    available: bool = True
    fail_with: Exception | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)
    capabilities: ProviderCapabilities = ProviderCapabilities()

    def is_available(self, *, meta: dict | None = None) -> bool:
        return self.available

    async def generate_image(
        self, *, prompt: str, size: str = "1024x1024", meta: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        self.calls.append({"prompt": prompt, "size": size, "meta": meta or {}})
        if self.fail_with is not None:
            raise self.fail_with
        return {"url": f"https://example.com/{self.name}.png"}


@pytest.fixture
def _image_provider_state():
    original_providers = dict(registry.image_providers)
    original_default = settings.image_provider_default
    original_fallbacks = settings.image_provider_fallbacks
    try:
        registry.image_providers.clear()
        yield
    finally:
        registry.image_providers.clear()
        registry.image_providers.update(original_providers)
        settings.image_provider_default = original_default
        settings.image_provider_fallbacks = original_fallbacks


@pytest.mark.asyncio
async def test_generate_image_uses_preferred_provider(_image_provider_state):
    primary = _FakeImageProvider(name="openai_image")
    fallback = _FakeImageProvider(name="nanobanana")
    registry.register_image(primary)
    registry.register_image(fallback)

    settings.image_provider_default = "openai_image"
    settings.image_provider_fallbacks = "nanobanana"

    result = await generate_image(prompt="A cat", meta={}, preferred_provider="openai_image")

    assert "openai_image" in result["url"]
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 0


@pytest.mark.asyncio
async def test_generate_image_falls_back_on_error(_image_provider_state):
    primary = _FakeImageProvider(name="openai_image", fail_with=RuntimeError("boom"))
    fallback = _FakeImageProvider(name="nanobanana")
    registry.register_image(primary)
    registry.register_image(fallback)

    settings.image_provider_default = "openai_image"
    settings.image_provider_fallbacks = "nanobanana"

    result = await generate_image(prompt="A cat", meta={})

    assert "nanobanana" in result["url"]
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 1


@pytest.mark.asyncio
async def test_generate_image_raises_when_all_fail(_image_provider_state):
    primary = _FakeImageProvider(name="openai_image", fail_with=RuntimeError("boom"))
    fallback = _FakeImageProvider(name="nanobanana", available=False)
    registry.register_image(primary)
    registry.register_image(fallback)

    settings.image_provider_default = "openai_image"
    settings.image_provider_fallbacks = "nanobanana"

    with pytest.raises(RuntimeError, match="All image providers failed"):
        await generate_image(prompt="A cat", meta={})
