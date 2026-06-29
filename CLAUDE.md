# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
crewai install

# Run the flow
crewai run

# Plot the flow graph
plot

# Run with a JSON trigger payload
run_with_trigger '{"topic": "FastAPI"}'
```

All entry points are defined in `pyproject.toml` under `[project.scripts]` and map to `src/guide_creator_flow/main.py`.

## Environment

Copy `.env.example` to `.env` and fill in:

```
ANTHROPIC_API_KEY      # required — all LLM calls
FIRECRAWL_API_KEY      # required — JS-rendered page scraping
SERPER_API_KEY         # required — gap-fill web search (Enrichment Crew)
VOYAGE_API_KEY         # required — embeddings for Knowledge + Memory
DOCUMENT_INPUT_DIR     # default: inputs  — local files must be under this dir
MAX_FILE_BYTES         # default: 52428800 (50 MB)
CREWAI_STORAGE_DIR     # default: .crewai — LanceDB storage root
```

No OpenAI dependency anywhere in this project. All LLM calls use Anthropic Claude. Embeddings use VoyageAI (`voyage-3`).

## Architecture

The project is a **CrewAI Flow** (`guide_creator_flow`) that orchestrates three specialised Crews to produce a beginner-friendly getting-started guide from any mix of source URLs and local files, then hands off to a student chatbot grounded in the same material.

The flow runs three crews in sequence:
- **`ResearchCrew`** — hierarchical process, dynamic agent activation per source type (YouTube, web, arXiv, local files)
- **`EnrichmentCrew`** — sequential, gap-fill web search, runs only when research quality score < 6
- **`WritingCrew`** — sequential, four-step pipeline: outline → draft → beginner review → edit

After guide generation, **`StudentChatbotFlow`** (`chatbot.py`) provides a conversational interface grounded exclusively in the generated guide and source material.

### Key design decisions

- **`@CrewBase` pattern** — all three crews use `@agent`, `@task`, `@crew` decorators; agent/task config lives in `config/agents.yaml` and `config/tasks.yaml` loaded via `self.agents_config[key]` / `self.tasks_config[key]`.
- **`TOOL_REGISTRY`** (`tool_registry.py`) — maps string names to instantiated tool objects. Research Crew `@agent` methods wire tools from here at runtime; tools cannot be listed directly in `agents.yaml` because `@CrewBase` would try to resolve them through its own registry.
- **`YoutubeTranscriptTool`** (`tools/youtube_transcript_tool.py`) — custom `BaseTool` wrapping `youtube-transcript-api`. Used instead of `YoutubeVideoSearchTool` because the latter requires OpenAI embeddings.
- **`FileReadTool`** instead of `PDFSearchTool`/`TXTSearchTool` — those require OpenAI embeddings; `FileReadTool` reads content directly. Semantic retrieval is handled by the Knowledge system in the chatbot.
- **Dynamic crew assembly** — `ResearchCrew.crew_for_sources()` builds the crew at runtime with only the specialists whose source bucket is non-empty, preventing hollow outputs from polluting the research report.
- **Quality gate** — `research_quality_scorer_tool.py` scores the research report on 5 criteria (2 pts each). Score ≥ 6 routes directly to Writing Crew; score < 6 routes through Enrichment Crew first.
- **VoyageAI embeddings** — passed as `embedder={"provider": "voyageai", "config": {"model": "voyage-3"}}` to both `Crew` and `Memory` to avoid LanceDB conflicts.
- **`@persist` on terminal step only** — applied to `save_outputs` in the flow, not class-wide.

### Current state

The three crew `.py` files and their `config/` YAMLs are default CrewAI scaffolds — agents and tasks are not yet implemented. `main.py` contains a placeholder `ContentFlow` pending replacement with `GuideGeneratorFlow` + `GuideFlowState`. `tools/topic_inference_tool.py`, `tools/research_quality_scorer_tool.py`, and `chatbot.py` are not yet implemented.
