from __future__ import annotations

from typing import Any

import pytest

from trendr_api.services.generate import build_prompt, generate_text_output


def test_build_prompt_includes_core_context():
    prompt = build_prompt(
        transcript="This is the transcript.",
        segments=[{"start": 0.0, "end": 2.0, "text": "Key line"}],
        output_kind="tweet",
        tone="professional",
        brand_voice="sharp and direct",
        audience="Founders",
        notes="Avoid buzzwords",
    )
    assert "This is the transcript." in prompt
    assert "sharp and direct" in prompt
    assert "Founders" in prompt
    assert "Avoid buzzwords" in prompt


def test_build_prompt_uses_template_override():
    prompt = build_prompt(
        transcript="This is the transcript.",
        segments=[{"start": 0.0, "end": 2.0, "text": "Key line"}],
        output_kind="tweet",
        tone="professional",
        brand_voice="sharp and direct",
        audience="Founders",
        notes="Avoid buzzwords",
        template_content="Tone={tone}\\nTranscript={transcript}\\nSegments={segments}",
    )
    assert "Tone=professional" in prompt
    assert "Transcript=This is the transcript." in prompt
    assert "Key line" in prompt


@pytest.mark.asyncio
async def test_generate_text_output_calls_provider_with_expected_meta(monkeypatch):
    calls: list[dict[str, Any]] = []

    async def _generate_text(*, prompt: str, system: str | None, meta: dict[str, Any], preferred_provider: str | None):
        calls.append(
            {
                "prompt": prompt,
                "system": system,
                "meta": meta,
                "preferred_provider": preferred_provider,
            }
        )
        return "fake-output"

    monkeypatch.setattr("trendr_api.services.generate.provider_router.generate_text", _generate_text)

    result = await generate_text_output(
        transcript="T",
        segments=[{"start": 0.0, "end": 1.0, "text": "segment"}],
        output_kind="linkedin",
        tone="authoritative",
        brand_voice="precise",
        provider_name="openai",
        meta={"audience": "PMs", "notes": "Use concrete examples"},
        template_content=(
            "Tone={tone}\\nAudience={audience}\\nTranscript={transcript}\\n"
            "Segments={segments}"
        ),
    )

    assert result == "fake-output"
    assert len(calls) == 1
    call = calls[0]
    assert call["meta"]["tone"] == "authoritative"
    assert call["meta"]["output_kind"] == "linkedin"
    assert call["preferred_provider"] == "openai"
    assert "segment" in call["prompt"]
