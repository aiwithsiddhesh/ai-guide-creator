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

# Run all tests
uv run pytest

# Run a specific test file or single test
uv run pytest tests/crews/test_crew_wiring.py
uv run pytest tests/flow/test_flow_nodes.py
uv run pytest -k test_crew_for_sources_youtube_only

# LLM output quality scoring (requires OPENAI_API_KEY in .env — evaluator only)
crewai test --n_iterations 3 --model gpt-4o-mini
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

No OpenAI dependency at runtime. All LLM calls use Anthropic Claude. Embeddings use VoyageAI (`voyage-3`). `OPENAI_API_KEY` is only needed for `crewai test` (evaluator only).

## Architecture

The project is a **CrewAI Flow** (`guide_creator_flow`) that orchestrates three specialised Crews to produce a beginner-friendly getting-started guide from any mix of source URLs and local files, then hands off to a student chatbot grounded in the same material.

### Flow orchestration (`main.py`)

`GuideGeneratorFlow` with `GuideFlowState` runs 7 nodes in sequence:

```
validate_inputs (@start) → "ready"
    └─▶ run_research_crew
            └─▶ scrub_report
                    └─▶ evaluate_research → "sufficient" | "insufficient"
                            ├─▶ [< 6] run_enrichment_crew → "enriched"
                            │                └─▶ run_writing_crew
                            └─▶ [≥ 6] run_writing_crew
                                            └─▶ save_outputs (@persist)
```

`save_outputs` writes `outputs/<run_id>/getting_started_guide.md`, `research_report.md`, and `metadata.json`. `@persist` is applied to this terminal step only.

### Crews

- **`ResearchCrew`** — hierarchical process, dynamic agent activation per source type (YouTube, web, arXiv, local files). Called via `crew_for_sources()`, not the standard `crew()`.
- **`EnrichmentCrew`** — sequential, gap-fill web search, runs only when research quality score < 6.
- **`WritingCrew`** — sequential, four-step pipeline: outline → draft → beginner review → edit.

After guide generation, **`StudentChatbotFlow`** (`chatbot.py`) provides a conversational interface grounded exclusively in the generated guide and source material. Not yet implemented.

### Key design decisions

- **`TOOL_REGISTRY`** (`tool_registry.py`) — lazy `_ToolRegistry` class; tools stored as classes, instantiated on first `__getitem__` access, cached. Importing the module never triggers API key validation. Research and Enrichment Crew `@agent` methods wire tools from here at runtime; tools cannot be listed directly in `agents.yaml` because `@CrewBase` would try to resolve them through its own registry. Crew wiring tests patch `TOOL_REGISTRY` with `MagicMock(spec=BaseTool)` values — `spec=BaseTool` is required for Pydantic's `isinstance` check in `Agent` to pass.
- **`YoutubeTranscriptTool`** (`tools/youtube_transcript_tool.py`) — custom `BaseTool` wrapping `youtube-transcript-api`. Used instead of `YoutubeVideoSearchTool` because the latter requires OpenAI embeddings.
- **`FileReadTool`** instead of `PDFSearchTool`/`TXTSearchTool` — those require OpenAI embeddings; `FileReadTool` reads content directly. Semantic retrieval is handled by the Knowledge system in the chatbot.
- **Dynamic crew assembly** — `ResearchCrew.crew_for_sources()` builds the crew at runtime with only the specialists whose source bucket is non-empty. The `_task()` helper strips the `agent` and `context` keys from the YAML dict before constructing each `Task` (passing them both as YAML string and as a kwarg raises `TypeError`).
- **Quality gate** — `research_quality_scorer_tool.py` scores the research report on 5 criteria (2 pts each) using regex (no LLM). Score ≥ 6 routes directly to Writing Crew; score < 6 routes through Enrichment Crew first. The standalone `score_report()` function is used directly in flow tests; the `BaseTool` wrapper exposes it to agents if needed.
- **`topic_inference_tool.py`** — plain Python function `infer_topic(urls, file_paths) -> str`. No LLM call. Extracts project name from domain roots and filenames; skips generic hosting domains and TLDs. Returns `""` if inference fails — the research director derives the topic from source content in that case.
- **`scrub_report` node** — strips prompt injection patterns from scraped content before it reaches any downstream crew. Patterns matched by `_INJECTION_PATTERN` in `main.py`.
- **VoyageAI embeddings** — passed as `embedder={"provider": "voyageai", "config": {"model": "voyage-3"}}` to both `Crew` and `Memory` to avoid LanceDB conflicts.
- **`@persist` on terminal step only** — applied to `save_outputs` in the flow, not class-wide. To resume a failed run after research completed: `GuideGeneratorFlow().kickoff(restore_from_state_id="<uuid>")`.

### Current state

- **`ResearchCrew`** — fully implemented: 5 agents with per-agent LLMs, 5 tasks, `crew_for_sources()` dynamic assembly, tools wired from `TOOL_REGISTRY`.
- **`EnrichmentCrew`** — fully implemented: 1 agent (`web_search_agent`, haiku), 1 task (`gap_fill_task`), sequential, `memory=False`.
- **`WritingCrew`** — fully implemented: 4 agents (strategist, writer, reviewer with `system_template`, editor), 4 tasks with explicit context wiring, sequential, `memory=True`, `output_file` on `edit_and_publish`.
- **`GuideGeneratorFlow`** (`main.py`) — fully implemented: `GuideFlowState`, 7 flow nodes, SSRF/path-traversal/file-size security checks, topic inference, quality gate routing, enrichment append, output file writing.
- **`tools/topic_inference_tool.py`** — fully implemented: pure function, no LLM.
- **`tools/research_quality_scorer_tool.py`** — fully implemented: `BaseTool` + standalone `score_report()`, 5-criterion regex rubric.
- **`chatbot.py`** — not yet implemented.
