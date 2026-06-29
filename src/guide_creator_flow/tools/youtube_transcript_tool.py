import re
from typing import Type

from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

_WATCH_RE = re.compile(r"[?&]v=([0-9A-Za-z_-]{11})")
_SHORT_RE = re.compile(r"youtu\.be/([0-9A-Za-z_-]{11})")


class YoutubeTranscriptInput(BaseModel):
    url: str = Field(..., description="YouTube video URL to fetch the transcript for.")


class YoutubeTranscriptTool(BaseTool):
    name: str = "YouTube Transcript Fetcher"
    description: str = (
        "Fetches the full transcript of a YouTube video given its URL. "
        "Returns plain text of the transcript."
    )
    args_schema: Type[BaseModel] = YoutubeTranscriptInput

    def _run(self, url: str) -> str:
        video_id = self._extract_video_id(url)
        if not video_id:
            return f"ERROR: Could not extract video ID from URL: {url}"
        try:
            transcript = YouTubeTranscriptApi().fetch(video_id)
            return " ".join(snippet.text for snippet in transcript)
        except TranscriptsDisabled:
            return f"ERROR: Transcripts are disabled for video: {url}"
        except NoTranscriptFound:
            return f"ERROR: No transcript found for video: {url}"
        except Exception as e:
            return f"ERROR: Failed to fetch transcript for {url}: {e}"

    @staticmethod
    def _extract_video_id(url: str) -> str:
        match = _WATCH_RE.search(url) or _SHORT_RE.search(url)
        return match.group(1) if match else ""
