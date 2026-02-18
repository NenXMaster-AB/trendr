from __future__ import annotations

from typing import Any, Iterable


BANNED_PHRASES = [
    "in today's fast-paced world",
    "delve into",
    "ever-evolving landscape",
    "game-changer",
    "unlock the power of",
    "leverage",
    "in conclusion",
    "it's important to note",
    "at the end of the day",
    "seamlessly",
]


def build_writing_constraints(
    *,
    output_kind: str,
    tone: str,
    audience: str | None,
    notes: str | None,
) -> str:
    audience_line = audience or "General audience"
    notes_line = notes or "None"
    banned = ", ".join(f"'{phrase}'" for phrase in BANNED_PHRASES)

    return (
        f"Output kind: {output_kind}\n"
        f"Tone target: {tone}\n"
        f"Audience target: {audience_line}\n"
        f"Additional notes: {notes_line}\n"
        "Quality constraints:\n"
        "- Use concrete details from source facts; avoid generic advice.\n"
        "- Use natural, varied sentence lengths.\n"
        "- Prefer plain words over buzzwords.\n"
        "- No padding intros/outros.\n"
        "- Avoid these phrases entirely: "
        f"{banned}.\n"
    )


def extract_source_facts(
    *,
    transcript: str,
    segments: Iterable[dict[str, Any]] | None,
    limit: int = 6,
) -> str:
    facts: list[str] = []

    if segments:
        for seg in segments:
            text = str(seg.get("text", "")).strip()
            if not text:
                continue
            start = seg.get("start")
            end = seg.get("end")
            facts.append(f"- [{start}-{end}] {text}")
            if len(facts) >= limit:
                return "\n".join(facts)

    for sentence in transcript.split("."):
        clean = sentence.strip()
        if len(clean) < 25:
            continue
        facts.append(f"- {clean}.")
        if len(facts) >= limit:
            break

    if not facts:
        return "- No concrete source facts extracted."
    return "\n".join(facts)
