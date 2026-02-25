from __future__ import annotations

import base64
from unittest.mock import AsyncMock, patch

import pytest

from trendr_api.services.media import generate_and_upload_image


@pytest.mark.asyncio
async def test_generate_and_upload_image_with_b64():
    sample_b64 = base64.b64encode(b"fake-png-data").decode()
    mock_generate = AsyncMock(
        return_value={
            "b64": sample_b64,
            "revised_prompt": "A revised cat",
            "size": "1024x1024",
        }
    )
    mock_upload = lambda data, key, ct: f"http://localhost:9000/trendr-media/{key}"

    with (
        patch("trendr_api.services.media.provider_router.generate_image", mock_generate),
        patch("trendr_api.services.media.upload_bytes", mock_upload),
    ):
        result = await generate_and_upload_image(
            prompt="A cat",
            size="1024x1024",
            quality="standard",
            style="vivid",
            workspace_id=1,
            project_id=10,
        )

    assert "http://localhost:9000/trendr-media/projects/10/images/" in result["url"]
    assert result["revised_prompt"] == "A revised cat"
    mock_generate.assert_awaited_once()


@pytest.mark.asyncio
async def test_generate_and_upload_image_with_url_fallback():
    mock_generate = AsyncMock(
        return_value={
            "url": "https://example.com/generated.png",
            "size": "1024x1024",
        }
    )

    with patch("trendr_api.services.media.provider_router.generate_image", mock_generate):
        result = await generate_and_upload_image(
            prompt="A cat",
            workspace_id=1,
            project_id=10,
        )

    assert result["url"] == "https://example.com/generated.png"
