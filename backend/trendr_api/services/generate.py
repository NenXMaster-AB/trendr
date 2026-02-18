from __future__ import annotations
from typing import Any, Dict, Optional

from ..plugins import registry
from .templates import format_segments, load_template, render_template
from .writing import build_writing_constraints, extract_source_facts


def build_prompt(
    *,
    transcript: str,
    segments: list[dict[str, Any]] | None,
    output_kind: str,
    tone: str,
    brand_voice: Optional[str],
    audience: Optional[str],
    notes: Optional[str],
) -> str:
    template = load_template(output_kind)
    writing_constraints = build_writing_constraints(
        output_kind=output_kind,
        tone=tone,
        audience=audience,
        notes=notes,
    )
    return render_template(
        template,
        {
            "tone": tone,
            "brand_voice": brand_voice or "N/A",
            "audience": audience or "General audience",
            "notes": notes or "None",
            "transcript": transcript,
            "segments": format_segments(segments),
            "source_facts": extract_source_facts(
                transcript=transcript,
                segments=segments,
            ),
            "writing_constraints": writing_constraints,
        },
    )


async def generate_text_output(
    *,
    transcript: str,
    segments: list[dict[str, Any]] | None,
    output_kind: str,
    tone: str,
    brand_voice: Optional[str],
    provider_name: str = "openai",
    meta: Optional[Dict[str, Any]] = None,
) -> str:
    provider = registry.get_text(provider_name)
    prompt_meta = meta or {}
    prompt = build_prompt(
        transcript=transcript,
        segments=segments,
        output_kind=output_kind,
        tone=tone,
        brand_voice=brand_voice,
        audience=prompt_meta.get("audience"),
        notes=prompt_meta.get("notes"),
    )
    return await provider.generate(
        prompt=prompt,
        system=None,
        meta={**prompt_meta, "tone": tone, "output_kind": output_kind},
    )
