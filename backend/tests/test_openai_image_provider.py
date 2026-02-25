from __future__ import annotations

import base64
from typing import Any

import pytest

from trendr_api.config import settings
from trendr_api.plugins.providers.openai_image import OpenAIImageProvider


class _FakeResponse:
    def __init__(self, *, status_code: int, payload: dict[str, Any], text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeAsyncClient:
    def __init__(self, response: _FakeResponse) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, *, json: dict[str, Any], headers: dict[str, str]):
        self.calls.append({"url": url, "json": json, "headers": headers})
        return self.response


@pytest.mark.asyncio
async def test_openai_image_provider_returns_b64(monkeypatch):
    original_key = settings.openai_api_key
    settings.openai_api_key = "test-key"

    sample_b64 = base64.b64encode(b"fake-png").decode()
    fake_response = _FakeResponse(
        status_code=200,
        payload={
            "data": [
                {
                    "b64_json": sample_b64,
                    "revised_prompt": "A revised prompt",
                }
            ]
        },
    )
    fake_client = _FakeAsyncClient(response=fake_response)
    monkeypatch.setattr(
        "trendr_api.plugins.providers.openai_image.httpx.AsyncClient",
        lambda *, timeout: fake_client,
    )

    try:
        provider = OpenAIImageProvider()
        result = await provider.generate_image(
            prompt="A cat",
            size="1024x1024",
            meta={"quality": "hd", "style": "natural"},
        )
    finally:
        settings.openai_api_key = original_key

    assert result["b64"] == sample_b64
    assert result["revised_prompt"] == "A revised prompt"
    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["url"].endswith("/images/generations")
    assert call["json"]["quality"] == "hd"
    assert call["json"]["style"] == "natural"
    assert call["json"]["response_format"] == "b64_json"


@pytest.mark.asyncio
async def test_openai_image_provider_raises_on_api_error(monkeypatch):
    original_key = settings.openai_api_key
    settings.openai_api_key = "test-key"

    fake_response = _FakeResponse(
        status_code=400,
        payload={},
        text="Bad request",
    )
    fake_client = _FakeAsyncClient(response=fake_response)
    monkeypatch.setattr(
        "trendr_api.plugins.providers.openai_image.httpx.AsyncClient",
        lambda *, timeout: fake_client,
    )

    try:
        provider = OpenAIImageProvider()
        with pytest.raises(RuntimeError, match="OpenAI Images API 400"):
            await provider.generate_image(prompt="A cat", meta={})
    finally:
        settings.openai_api_key = original_key


def test_openai_image_provider_unavailable_without_key():
    original_key = settings.openai_api_key
    settings.openai_api_key = None
    try:
        provider = OpenAIImageProvider()
        assert provider.is_available() is False
    finally:
        settings.openai_api_key = original_key
