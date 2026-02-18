from __future__ import annotations
from typing import Dict, Any
from datetime import datetime


async def fetch_youtube_metadata(url: str) -> Dict[str, Any]:
    # TODO: integrate official YouTube Data API or a safe extractor.
    return {
        "url": url,
        "title": "Stub YouTube Title",
        "channel": "Stub Channel",
        "published_at": datetime.utcnow().isoformat(),
        "duration_sec": 0,
    }


async def fetch_youtube_transcript(url: str) -> Dict[str, Any]:
    # TODO: integrate transcript sources (official API or transcript libs)
    # Return both full text and basic segments.
    text = (
        "This is a stub transcript. Replace with real transcript extraction. "
        "Trendr will segment this into chapters and key moments."
    )
    segments = [
        {"start": 0, "end": 15, "text": "Stub intro segment."},
        {"start": 15, "end": 60, "text": "Stub main point segment."},
    ]
    return {"text": text, "segments": segments}
