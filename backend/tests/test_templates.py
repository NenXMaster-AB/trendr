from __future__ import annotations

import pytest

from trendr_api.services.templates import (
    format_segments,
    load_template,
    render_template,
    template_filename,
)


def test_load_template_for_tweet_kind():
    template = load_template("tweet")
    assert "transcript" in template.lower()
    assert "{tone}" in template


def test_template_filename_rejects_unknown_kind():
    with pytest.raises(ValueError, match="Unknown output kind"):
        template_filename("newsletter")


def test_render_template_raises_on_missing_context_key():
    with pytest.raises(ValueError, match="missing context value"):
        render_template("Tone: {tone}, Transcript: {transcript}", {"tone": "professional"})


def test_format_segments_outputs_timestamped_lines():
    text = format_segments(
        [
            {"start": 1.0, "end": 2.5, "text": "First line"},
            {"start": 2.5, "end": 4.0, "text": "Second line"},
        ]
    )
    assert "[1.0-2.5] First line" in text
    assert "[2.5-4.0] Second line" in text
