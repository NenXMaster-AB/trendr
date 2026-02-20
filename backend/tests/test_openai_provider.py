from __future__ import annotations

from typing import Any

import pytest

from trendr_api.config import settings
from trendr_api.plugins.providers.openai_text import OpenAITextProvider


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
async def test_openai_provider_generate_parses_chat_completion(monkeypatch):
    original_key = settings.openai_api_key
    original_model = settings.openai_model
    original_base = settings.openai_base_url

    settings.openai_api_key = "test-key"
    settings.openai_model = "gpt-test"
    settings.openai_base_url = "https://api.openai.com/v1"

    fake_response = _FakeResponse(
        status_code=200,
        payload={
            "choices": [
                {
                    "message": {
                        "content": "Generated output",
                    }
                }
            ]
        },
    )
    fake_client = _FakeAsyncClient(response=fake_response)

    def _client_factory(*, timeout: int):
        assert timeout == 45
        return fake_client

    monkeypatch.setattr("trendr_api.plugins.providers.openai_text.httpx.AsyncClient", _client_factory)

    try:
        provider = OpenAITextProvider()
        result = await provider.generate(
            prompt="hello",
            system="be concise",
            meta={"temperature": 0.3, "max_output_tokens": 120},
        )
    finally:
        settings.openai_api_key = original_key
        settings.openai_model = original_model
        settings.openai_base_url = original_base

    assert result == "Generated output"
    assert len(fake_client.calls) == 1
    call = fake_client.calls[0]
    assert call["url"].endswith("/chat/completions")
    assert call["json"]["model"] == "gpt-test"
    assert call["json"]["temperature"] == 0.3
    assert call["json"]["max_tokens"] == 120
    assert call["headers"]["Authorization"] == "Bearer test-key"


def test_openai_provider_unavailable_without_api_key():
    original_key = settings.openai_api_key
    settings.openai_api_key = None
    try:
        provider = OpenAITextProvider()
    finally:
        settings.openai_api_key = original_key

    assert provider.is_available() is False
