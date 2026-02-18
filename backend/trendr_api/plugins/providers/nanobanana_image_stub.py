from __future__ import annotations
from typing import Dict, Any, Optional

from ..registry import registry


class NanoBananaImageStub:
    name = "nanobanana"

    async def generate_image(self, *, prompt: str, size: str = "1024x1024", meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        # Skeleton stub: replace with real provider integration
        return {
            "url": "https://example.com/placeholder.png",
            "size": size,
            "note": "Stub provider: integrate Nano Banana here.",
            "prompt_preview": prompt[:500],
        }


def register():
    registry.register_image(NanoBananaImageStub())
