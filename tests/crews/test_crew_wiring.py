"""Crew wiring tests — verify instantiation and structure without making LLM calls."""

from unittest.mock import MagicMock, patch

import pytest
from crewai import Crew
from crewai.tools import BaseTool

from guide_creator_flow.tool_registry import TOOL_REGISTRY


EXPECTED_REGISTRY_KEYS = {
    "youtube_transcript",
    "scrape_website",
    "firecrawl_scrape",
    "arxiv_paper",
    "file_read",
    "serper_search",
}

# A fake TOOL_REGISTRY where every key returns a MagicMock spec'd to BaseTool.
# spec=BaseTool makes Pydantic's isinstance check pass when Agent validates tools.
# Patched at the research_crew module level so @agent methods never instantiate
# real tools that require API keys.
MOCK_REGISTRY = {key: MagicMock(spec=BaseTool) for key in EXPECTED_REGISTRY_KEYS}


# ---------------------------------------------------------------------------
# Tool Registry
# ---------------------------------------------------------------------------

def test_tool_registry_imports():
    """TOOL_REGISTRY import completes without error."""
    assert TOOL_REGISTRY is not None


def test_tool_registry_keys():
    """All 6 expected keys are present in TOOL_REGISTRY."""
    assert EXPECTED_REGISTRY_KEYS == set(TOOL_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Research Crew — standard @crew
# ---------------------------------------------------------------------------

@patch("guide_creator_flow.crews.research_crew.research_crew.TOOL_REGISTRY", MOCK_REGISTRY)
def test_research_crew_instantiates():
    """ResearchCrew().crew() returns a Crew object."""
    from guide_creator_flow.crews.research_crew.research_crew import ResearchCrew
    crew = ResearchCrew().crew()
    assert isinstance(crew, Crew)


@patch("guide_creator_flow.crews.research_crew.research_crew.TOOL_REGISTRY", MOCK_REGISTRY)
def test_research_crew_is_hierarchical():
    """Research Crew uses hierarchical process."""
    from crewai import Process
    from guide_creator_flow.crews.research_crew.research_crew import ResearchCrew
    crew = ResearchCrew().crew()
    assert crew.process == Process.hierarchical


@patch("guide_creator_flow.crews.research_crew.research_crew.TOOL_REGISTRY", MOCK_REGISTRY)
def test_research_crew_has_five_agents():
    """Standard Research Crew has all 5 agents registered."""
    from guide_creator_flow.crews.research_crew.research_crew import ResearchCrew
    crew = ResearchCrew().crew()
    assert len(crew.agents) == 5


@patch("guide_creator_flow.crews.research_crew.research_crew.TOOL_REGISTRY", MOCK_REGISTRY)
def test_research_crew_has_five_tasks():
    """Standard Research Crew has all 5 tasks registered."""
    from guide_creator_flow.crews.research_crew.research_crew import ResearchCrew
    crew = ResearchCrew().crew()
    assert len(crew.tasks) == 5


@patch("guide_creator_flow.crews.research_crew.research_crew.TOOL_REGISTRY", MOCK_REGISTRY)
def test_research_crew_memory_disabled():
    """Research Crew memory is disabled."""
    from guide_creator_flow.crews.research_crew.research_crew import ResearchCrew
    crew = ResearchCrew().crew()
    assert crew.memory is False


# ---------------------------------------------------------------------------
# Research Crew — crew_for_sources (dynamic)
# ---------------------------------------------------------------------------

@patch("guide_creator_flow.crews.research_crew.research_crew.TOOL_REGISTRY", MOCK_REGISTRY)
def test_crew_for_sources_youtube_only():
    """crew_for_sources with only youtube_links activates youtube_analyst + director."""
    from guide_creator_flow.crews.research_crew.research_crew import ResearchCrew
    crew = ResearchCrew().crew_for_sources(
        youtube_links=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        webpage_links=[],
        research_paper_links=[],
        document_paths=[],
    )
    assert isinstance(crew, Crew)
    assert len(crew.tasks) == 2


@patch("guide_creator_flow.crews.research_crew.research_crew.TOOL_REGISTRY", MOCK_REGISTRY)
def test_crew_for_sources_web_only():
    """crew_for_sources with only webpage_links activates web_researcher + director."""
    from guide_creator_flow.crews.research_crew.research_crew import ResearchCrew
    crew = ResearchCrew().crew_for_sources(
        youtube_links=[],
        webpage_links=["https://example.com"],
        research_paper_links=[],
        document_paths=[],
    )
    assert isinstance(crew, Crew)
    assert len(crew.tasks) == 2


@patch("guide_creator_flow.crews.research_crew.research_crew.TOOL_REGISTRY", MOCK_REGISTRY)
def test_crew_for_sources_all_buckets():
    """crew_for_sources with all buckets non-empty includes all specialists."""
    from guide_creator_flow.crews.research_crew.research_crew import ResearchCrew
    crew = ResearchCrew().crew_for_sources(
        youtube_links=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        webpage_links=["https://example.com"],
        research_paper_links=["https://arxiv.org/abs/2301.00001"],
        document_paths=["inputs/doc.pdf"],
    )
    assert isinstance(crew, Crew)
    assert len(crew.tasks) == 5


@patch("guide_creator_flow.crews.research_crew.research_crew.TOOL_REGISTRY", MOCK_REGISTRY)
def test_crew_for_sources_compile_task_has_dynamic_context():
    """The compile task in crew_for_sources gets only the active specialist tasks as context."""
    from guide_creator_flow.crews.research_crew.research_crew import ResearchCrew
    crew = ResearchCrew().crew_for_sources(
        youtube_links=["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
        webpage_links=[],
        research_paper_links=[],
        document_paths=[],
    )
    compile_task = crew.tasks[-1]
    assert len(compile_task.context) == 1
