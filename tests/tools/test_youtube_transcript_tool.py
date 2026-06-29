from unittest.mock import MagicMock, patch

import pytest
from youtube_transcript_api import NoTranscriptFound, TranscriptsDisabled
from youtube_transcript_api._transcripts import FetchedTranscriptSnippet

from guide_creator_flow.tools.youtube_transcript_tool import YoutubeTranscriptTool

TOOL = YoutubeTranscriptTool()
VIDEO_ID = "dQw4w9WgXcQ"


def make_snippets(*texts):
    return [FetchedTranscriptSnippet(text=t, start=float(i), duration=1.0) for i, t in enumerate(texts)]


def patch_fetch(return_value=None, side_effect=None):
    mock_instance = MagicMock()
    if side_effect:
        mock_instance.fetch.side_effect = side_effect
    else:
        mock_instance.fetch.return_value = return_value
    return patch(
        "guide_creator_flow.tools.youtube_transcript_tool.YouTubeTranscriptApi",
        return_value=mock_instance,
    )


# --- _extract_video_id ---

def test_valid_watch_url():
    assert TOOL._extract_video_id(f"https://www.youtube.com/watch?v={VIDEO_ID}") == VIDEO_ID


def test_valid_short_url():
    assert TOOL._extract_video_id(f"https://youtu.be/{VIDEO_ID}") == VIDEO_ID


def test_watch_url_with_extra_params():
    assert TOOL._extract_video_id(f"https://www.youtube.com/watch?v={VIDEO_ID}&t=42s") == VIDEO_ID


def test_malformed_url_returns_empty():
    assert TOOL._extract_video_id("https://example.com/not-a-video") == ""


def test_empty_url_returns_empty():
    assert TOOL._extract_video_id("") == ""


# --- _run: video ID extraction failure ---

def test_malformed_url_run_returns_error_string():
    result = TOOL._run(url="https://example.com/not-a-video")
    assert result.startswith("ERROR:")
    assert "Could not extract video ID" in result


# --- _run: successful transcript ---

def test_successful_transcript_returns_joined_text():
    with patch_fetch(return_value=make_snippets("Hello", "world")):
        result = TOOL._run(url=f"https://www.youtube.com/watch?v={VIDEO_ID}")
    assert result == "Hello world"


def test_successful_transcript_single_entry():
    with patch_fetch(return_value=make_snippets("Only line")):
        result = TOOL._run(url=f"https://youtu.be/{VIDEO_ID}")
    assert result == "Only line"


# --- _run: TranscriptsDisabled ---

def test_transcripts_disabled_returns_error_string():
    with patch_fetch(side_effect=TranscriptsDisabled(VIDEO_ID)):
        result = TOOL._run(url=f"https://www.youtube.com/watch?v={VIDEO_ID}")
    assert result.startswith("ERROR:")
    assert "disabled" in result.lower()


# --- _run: NoTranscriptFound ---

def test_no_transcript_found_returns_error_string():
    with patch_fetch(side_effect=NoTranscriptFound(VIDEO_ID, [], {})):
        result = TOOL._run(url=f"https://www.youtube.com/watch?v={VIDEO_ID}")
    assert result.startswith("ERROR:")
    assert "No transcript found" in result


# --- _run: unexpected exception ---

def test_unexpected_exception_returns_error_string():
    with patch_fetch(side_effect=RuntimeError("network failure")):
        result = TOOL._run(url=f"https://www.youtube.com/watch?v={VIDEO_ID}")
    assert result.startswith("ERROR:")
    assert "network failure" in result


# --- correct video ID passed to fetch ---

def test_correct_video_id_passed_to_fetch():
    mock_instance = MagicMock()
    mock_instance.fetch.return_value = make_snippets("mocked")
    with patch(
        "guide_creator_flow.tools.youtube_transcript_tool.YouTubeTranscriptApi",
        return_value=mock_instance,
    ):
        TOOL._run(url=f"https://www.youtube.com/watch?v={VIDEO_ID}")
    mock_instance.fetch.assert_called_once_with(VIDEO_ID)
