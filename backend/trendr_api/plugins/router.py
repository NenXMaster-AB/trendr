from __future__ import annotations

from typing import Any

from ..config import settings
from .registry import registry


def _normalize_chain(chain: list[str]) -> list[str]:
    seen: set[str] = set()
    normalized: list[str] = []
    for item in chain:
        candidate = item.strip()
        if not candidate or candidate in seen:
            continue
        normalized.append(candidate)
        seen.add(candidate)
    return normalized


def text_fallback_chain(*, preferred: str | None = None) -> list[str]:
    chain = [preferred or settings.text_provider_default, *settings.text_provider_fallback_list]
    return _normalize_chain(chain)


async def generate_text(
    *,
    prompt: str,
    system: str | None,
    meta: dict[str, Any],
    preferred_provider: str | None = None,
) -> str:
    errors: list[str] = []

    for provider_name in text_fallback_chain(preferred=preferred_provider):
        try:
            provider = registry.get_text(provider_name)
        except KeyError as exc:
            errors.append(f"{provider_name}: {exc}")
            continue

        if not provider.is_available(meta=meta):
            errors.append(f"{provider_name}: unavailable (missing credentials/config)")
            continue

        try:
            return await provider.generate(prompt=prompt, system=system, meta=meta)
        except Exception as exc:  # pragma: no cover - error path exercised in tests
            errors.append(f"{provider_name}: {exc.__class__.__name__}: {exc}")

    detail = "; ".join(errors) if errors else "no providers configured"
    raise RuntimeError(f"All text providers failed: {detail}")
