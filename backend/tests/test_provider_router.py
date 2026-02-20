from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest

from trendr_api.config import settings
from trendr_api.plugins.registry import registry
from trendr_api.plugins.router import generate_text
from trendr_api.plugins.types import ProviderCapabilities


@dataclass
class _FakeTextProvider:
    name: str
    available: bool = True
    fail_with: Exception | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)
    capabilities: ProviderCapabilities = ProviderCapabilities()

    def is_available(self) -> bool:
        return self.available

    async def generate(self, *, prompt: str, system: str | None = None, meta: dict[str, Any] | None = None) -> str:
        self.calls.append({"prompt": prompt, "system": system, "meta": meta or {}})
        if self.fail_with is not None:
            raise self.fail_with
        return f"{self.name}-ok"


@pytest.fixture
def _provider_state():
    original_providers = dict(registry.text_providers)
    original_default = settings.text_provider_default
    original_fallbacks = settings.text_provider_fallbacks
    try:
        registry.text_providers.clear()
        yield
    finally:
        registry.text_providers.clear()
        registry.text_providers.update(original_providers)
        settings.text_provider_default = original_default
        settings.text_provider_fallbacks = original_fallbacks


@pytest.mark.asyncio
async def test_generate_text_uses_preferred_provider_when_available(_provider_state):
    primary = _FakeTextProvider(name="openai")
    fallback = _FakeTextProvider(name="openai_stub")
    registry.register_text(primary)
    registry.register_text(fallback)

    settings.text_provider_default = "openai"
    settings.text_provider_fallbacks = "openai_stub"

    result = await generate_text(
        prompt="hello",
        system=None,
        meta={"tone": "professional"},
        preferred_provider="openai",
    )

    assert result == "openai-ok"
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 0


@pytest.mark.asyncio
async def test_generate_text_falls_back_when_preferred_unavailable(_provider_state):
    primary = _FakeTextProvider(name="openai", available=False)
    fallback = _FakeTextProvider(name="openai_stub")
    registry.register_text(primary)
    registry.register_text(fallback)

    settings.text_provider_default = "openai"
    settings.text_provider_fallbacks = "openai_stub"

    result = await generate_text(
        prompt="hello",
        system=None,
        meta={},
        preferred_provider="openai",
    )

    assert result == "openai_stub-ok"
    assert len(primary.calls) == 0
    assert len(fallback.calls) == 1


@pytest.mark.asyncio
async def test_generate_text_falls_back_on_provider_error(_provider_state):
    primary = _FakeTextProvider(name="openai", fail_with=RuntimeError("boom"))
    fallback = _FakeTextProvider(name="openai_stub")
    registry.register_text(primary)
    registry.register_text(fallback)

    settings.text_provider_default = "openai"
    settings.text_provider_fallbacks = "openai_stub"

    result = await generate_text(
        prompt="hello",
        system=None,
        meta={},
        preferred_provider="openai",
    )

    assert result == "openai_stub-ok"
    assert len(primary.calls) == 1
    assert len(fallback.calls) == 1


@pytest.mark.asyncio
async def test_generate_text_raises_when_all_providers_fail(_provider_state):
    primary = _FakeTextProvider(name="openai", fail_with=RuntimeError("boom"))
    fallback = _FakeTextProvider(name="openai_stub", available=False)
    registry.register_text(primary)
    registry.register_text(fallback)

    settings.text_provider_default = "openai"
    settings.text_provider_fallbacks = "openai_stub"

    with pytest.raises(RuntimeError, match="All text providers failed"):
        await generate_text(
            prompt="hello",
            system=None,
            meta={},
            preferred_provider="openai",
        )
