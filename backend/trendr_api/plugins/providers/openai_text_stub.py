from __future__ import annotations
from typing import Optional, Dict, Any
import os

from ..registry import registry


class OpenAITextStub:
    name = "openai"

    async def generate(self, *, prompt: str, system: Optional[str] = None, meta: Optional[Dict[str, Any]] = None) -> str:
        # Skeleton stub: replace with real OpenAI SDK calls
        # Keep deterministic for now.
        tone = (meta or {}).get("tone", "professional")
        return (
            "/* Trendr stub output (OpenAI) */\n"
            f"Tone: {tone}\n"
            "Prompt received:\n"
            f"{prompt[:2000]}"
        )


def register():
    registry.register_text(OpenAITextStub())
