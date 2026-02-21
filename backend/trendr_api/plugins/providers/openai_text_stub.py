from __future__ import annotations
from typing import Any, Dict, Optional

from ..registry import registry
from ..types import ProviderCapabilities


class OpenAITextStub:
    name = "openai_stub"
    capabilities = ProviderCapabilities(
        max_input_tokens=8_000,
        max_output_tokens=2_000,
        supports_json_mode=False,
        supports_streaming=False,
        supports_system_prompt=True,
    )

    def is_available(self, *, meta: Optional[Dict[str, Any]] = None) -> bool:
        return True

    async def generate(self, *, prompt: str, system: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> str:
        # Deterministic local fallback when remote providers are unavailable.
        tone = (meta or {}).get("tone", "professional")
        return (
            "/* Trendr stub output (OpenAI) */\n"
            f"Tone: {tone}\n"
            "Prompt received:\n"
            f"{prompt[:2000]}"
        )


def register():
    registry.register_text(OpenAITextStub())
