from crewai_tools import (
    ArxivPaperTool,
    FileReadTool,
    FirecrawlScrapeWebsiteTool,
    ScrapeWebsiteTool,
    SerperDevTool,
)

from guide_creator_flow.tools.youtube_transcript_tool import YoutubeTranscriptTool

# Tool classes — not instances. Instantiation is deferred to first access so
# importing this module never fails due to missing API keys (e.g. in CI).
_TOOL_CLASSES: dict = {
    "youtube_transcript": YoutubeTranscriptTool,
    "scrape_website":     ScrapeWebsiteTool,
    "firecrawl_scrape":   FirecrawlScrapeWebsiteTool,
    "arxiv_paper":        ArxivPaperTool,
    "file_read":          FileReadTool,
    "serper_search":      SerperDevTool,
}

_cache: dict = {}


class _ToolRegistry:
    def __getitem__(self, key: str):
        if key not in _cache:
            _cache[key] = _TOOL_CLASSES[key]()
        return _cache[key]

    def __contains__(self, key: str) -> bool:
        return key in _TOOL_CLASSES

    def keys(self):
        return _TOOL_CLASSES.keys()


TOOL_REGISTRY = _ToolRegistry()
