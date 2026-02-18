from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable


class TemplateNotFoundError(FileNotFoundError):
    """Raised when a filesystem template for an output kind cannot be found."""


TEMPLATE_FILES: dict[str, str] = {
    "tweet": "tweet_thread.md",
    "linkedin": "linkedin_post.md",
    "blog": "blog_post.md",
}


def _templates_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "templates"


def template_filename(kind: str) -> str:
    filename = TEMPLATE_FILES.get(kind)
    if not filename:
        supported = ", ".join(sorted(TEMPLATE_FILES.keys()))
        raise ValueError(f"Unknown output kind '{kind}'. Supported kinds: {supported}")
    return filename


def load_template(kind: str) -> str:
    filename = template_filename(kind)
    path = _templates_dir() / filename
    if not path.exists():
        raise TemplateNotFoundError(
            f"Template for output kind '{kind}' was not found at '{path}'"
        )
    return path.read_text(encoding="utf-8")


def format_segments(segments: Iterable[Dict[str, Any]] | None) -> str:
    if not segments:
        return "No transcript segments available."

    lines = []
    for segment in segments:
        start = segment.get("start")
        end = segment.get("end")
        text = str(segment.get("text", "")).strip()
        lines.append(f"[{start}-{end}] {text}")
    return "\n".join(lines)


def render_template(template: str, ctx: Dict[str, Any]) -> str:
    try:
        return template.format(**ctx)
    except KeyError as exc:
        missing_key = exc.args[0]
        raise ValueError(
            f"Template render failed: missing context value '{missing_key}'"
        ) from exc
