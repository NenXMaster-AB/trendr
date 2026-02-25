from __future__ import annotations

import base64
import logging
import uuid
from typing import Any, Dict, Optional

from ..plugins import router as provider_router
from .s3 import upload_bytes

logger = logging.getLogger(__name__)


async def generate_and_upload_image(
    *,
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid",
    workspace_id: int,
    project_id: int,
) -> Dict[str, Any]:
    meta: Dict[str, Any] = {
        "workspace_id": workspace_id,
        "quality": quality,
        "style": style,
    }

    result = await provider_router.generate_image(
        prompt=prompt,
        size=size,
        meta=meta,
    )

    b64_data = result.get("b64")
    if isinstance(b64_data, str) and b64_data:
        image_bytes = base64.b64decode(b64_data)
        key = f"projects/{project_id}/images/{uuid.uuid4().hex}.png"
        url = upload_bytes(image_bytes, key, "image/png")
    else:
        url = result.get("url", "")

    return {
        "url": url,
        "revised_prompt": result.get("revised_prompt", ""),
        "size": size,
    }
