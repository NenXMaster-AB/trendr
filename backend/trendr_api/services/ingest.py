from __future__ import annotations
import asyncio
import re
from typing import Any, Dict
from urllib.parse import parse_qs, urlparse

import httpx


YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


class TranscriptFetchError(RuntimeError):
    """Raised when a transcript cannot be fetched for a YouTube video."""


def _is_valid_video_id(value: str | None) -> bool:
    return bool(value and YOUTUBE_ID_RE.match(value))


def extract_video_id(url: str) -> str:
    """Extract a YouTube video ID from common URL formats."""
    parsed = urlparse(url.strip())
    host = parsed.netloc.lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    if host in {"youtu.be", "www.youtu.be"}:
        candidate = path_parts[0] if path_parts else None
        if _is_valid_video_id(candidate):
            return candidate

    if "youtube.com" in host or "youtube-nocookie.com" in host:
        query_video_id = parse_qs(parsed.query).get("v", [None])[0]
        if _is_valid_video_id(query_video_id):
            return query_video_id

        if len(path_parts) >= 2 and path_parts[0] in {"shorts", "embed", "live", "v"}:
            candidate = path_parts[1]
            if _is_valid_video_id(candidate):
                return candidate

    raise ValueError(f"Unsupported YouTube URL format: '{url}'")


async def fetch_youtube_metadata(url: str) -> Dict[str, Any]:
    video_id = extract_video_id(url)
    title = f"YouTube Video {video_id}"
    channel = "Unknown Channel"

    # Lightweight metadata source that does not require API keys.
    try:
        oembed_url = "https://www.youtube.com/oembed"
        params = {
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "format": "json",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            res = await client.get(oembed_url, params=params)
            res.raise_for_status()
            data = res.json()
            title = str(data.get("title") or title)
            channel = str(data.get("author_name") or channel)
    except Exception:
        # Metadata fallback is acceptable for MVP; transcript fetch is authoritative.
        pass

    return {
        "url": url,
        "video_id": video_id,
        "title": title,
        "channel": channel,
        "published_at": None,
        "duration_sec": None,
    }


def _normalize_line(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _format_transcript_error(exc: Exception) -> str:
    name = exc.__class__.__name__
    message = str(exc).strip() or "no details"
    normalized = message.lower()

    if name in {"RequestBlocked", "IpBlocked"} or "no element found" in normalized:
        return (
            f"{name}: {message}. This usually means YouTube blocked transcript requests "
            "from the current IP/environment."
        )
    if name in {"TranscriptsDisabled", "NoTranscriptFound"}:
        return f"{name}: {message}. The video may not have available captions."
    if name == "VideoUnavailable":
        return f"{name}: {message}. The video may be private, region-locked, or removed."
    return f"{name}: {message}"


def _to_raw_entries(fetched: Any) -> list[Dict[str, Any]]:
    if hasattr(fetched, "to_raw_data"):
        return fetched.to_raw_data()
    if isinstance(fetched, list):
        return fetched
    return list(fetched)


def _fetch_transcript_sync(video_id: str) -> list[Dict[str, Any]]:
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError as exc:
        raise TranscriptFetchError(
            "youtube-transcript-api is not installed. Install backend requirements."
        ) from exc

    language_preferences = ["en", "en-US", "en-GB"]
    errors: list[str] = []
    api = YouTubeTranscriptApi()

    try:
        fetched = api.fetch(video_id, languages=language_preferences)
        return _to_raw_entries(fetched)
    except Exception as exc:
        errors.append(_format_transcript_error(exc))

    try:
        transcript_list = api.list(video_id)

        transcript = None
        for picker in (
            lambda tl: tl.find_transcript(language_preferences),
            lambda tl: tl.find_generated_transcript(language_preferences),
            lambda tl: tl.find_manually_created_transcript(language_preferences),
        ):
            try:
                transcript = picker(transcript_list)
                break
            except Exception:
                continue

        if transcript is None:
            transcript = next(iter(transcript_list), None)

        if transcript is None:
            raise TranscriptFetchError("No transcripts returned for this video.")

        fetched = transcript.fetch()
        return _to_raw_entries(fetched)
    except Exception as exc:
        errors.append(_format_transcript_error(exc))

    details = "; ".join(e for e in errors if e) or "unknown transcript retrieval error"
    raise TranscriptFetchError(
        f"Transcript unavailable for video '{video_id}'. Details: {details}"
    )


async def fetch_youtube_transcript(url: str) -> Dict[str, Any]:
    video_id = extract_video_id(url)
    raw_entries = await asyncio.to_thread(_fetch_transcript_sync, video_id)

    segments: list[Dict[str, Any]] = []
    full_text_parts: list[str] = []

    for entry in raw_entries:
        text = _normalize_line(str(entry.get("text", "")))
        if not text:
            continue

        start = float(entry.get("start", 0.0))
        duration = float(entry.get("duration", 0.0))
        end = start + duration

        segments.append(
            {
                "start": round(start, 3),
                "end": round(end, 3),
                "text": text,
            }
        )
        full_text_parts.append(text)

    full_text = " ".join(full_text_parts).strip()
    if not full_text:
        raise TranscriptFetchError(f"Transcript was empty for video '{video_id}'")

    return {"video_id": video_id, "text": full_text, "segments": segments}
