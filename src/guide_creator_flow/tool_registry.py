from crewai_tools import (
    ScrapeWebsiteTool, FileReadTool,
    FirecrawlScrapeWebsiteTool, SerperDevTool, ArxivPaperTool,
)
from guide_creator_flow.tools.youtube_transcript_tool import YoutubeTranscriptTool

TOOL_REGISTRY: dict = {
    "youtube_transcript": YoutubeTranscriptTool(),
    "scrape_website":     ScrapeWebsiteTool(),
    "firecrawl_scrape":   FirecrawlScrapeWebsiteTool(),
    "arxiv_paper":        ArxivPaperTool(),
    "file_read":          FileReadTool(),
    "serper_search":      SerperDevTool(),
}