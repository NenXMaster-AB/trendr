from __future__ import annotations
from typing import Protocol, Dict, Any, Optional, List


class TextProvider(Protocol):
    name: str

    async def generate(
        self,
        *,
        prompt: str,
        system: Optional[str] = None,
        meta: Optional[Dict[str, Any]] = None
    ) -> str:
        ...


class ImageProvider(Protocol):
    name: str

    async def generate_image(
        self,
        *,
        prompt: str,
        size: str = "1024x1024",
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return dict with at least: { 'url': str } or { 'b64': str }"""
        ...
