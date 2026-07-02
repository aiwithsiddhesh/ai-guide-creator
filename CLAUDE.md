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

# Launch the student chatbot for a completed run
chat <run_id>

# Run all tests (no API keys required)
uv run pytest

# Run a specific test file or single test
uv run pytest tests/crews/test_crew_wiring.py
uv run pytest tests/flow/test_flow_end_to_end.py
uv run pytest tests/tools/test_citation_guardrail_tool.py
uv run pytest -k test_crew_for_sources_youtube_only

# Lint / format (ruff, also runs via pre-commit)
uv run ruff check .
uv run ruff format .

# LLM output quality scoring (requires OPENAI_API_KEY in .env — evaluator only, non-blocking in CI)
crewai test --n_iterations 3 --model gpt-4o-mini
```

All entry points are defined in `pyproject.toml` under `[project.scripts]` and map to `src/guide_creator_flow/main.py` (`kickoff`/`run_crew`, `plot`, `run_with_trigger`) or `src/guide_creator_flow/chatbot.py` (`chat`). See `TESTING.md` for what each test directory covers and what is intentionally left to the LLM-judge eval instead of CI.

## Environment

Copy `.env.example` to `.env` and fill in:

```
ANTHROPIC_API_KEY      # required — all LLM calls
FIRECRAWL_API_KEY      # required — JS-rendered page scraping
SERPER_API_KEY         # required — gap-fill web search (Enrichment Crew)
VOYAGE_API_KEY         # required — embeddings for Knowledge + Memory
DOCUMENT_INPUT_DIR     # default: documents  — local files must be under this dir
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

After guide generation, **`StudentChatbotFlow`** (`chatbot.py`) provides a terminal chat session grounded exclusively in the generated guide and source material, routing each message to `QACrew` by intent.

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
- **`ConversationalFlow` unavailable** — `crewai.experimental.conversational` does not exist in `crewai==1.14.4`. `StudentChatbotFlow` uses standard `Flow` with a `chat()` REPL that calls `kickoff()` per turn and manages `state.messages` manually.
- **Knowledge isolation per run** — `launch_chatbot()` sets `CREWAI_STORAGE_DIR=./outputs/<run_id>/.crewai` before instantiating `StudentChatbotFlow` so each guide run gets its own LanceDB store.
- **Knowledge sources loaded once** — `QACrew` receives `knowledge_sources` in `__init__` and reuses them across all turns; do not reload inside handlers (triggers re-embedding).
- **`route_intent()`** — plain keyword matching in `chatbot.py`; tested independently in `tests/chatbot/test_intent_routing.py`. Priority order: end → example → clarify → question (default).
- **Research Crew agent-capability flags** (`research_crew/config/agents.yaml`) — `max_rpm` on `web_researcher` (10) and `youtube_analyst` (15) to avoid 429s from Firecrawl/YouTube during hierarchical fan-out; `max_execution_time` (seconds) on all 4 specialists so a stuck scrape/transcript call times out instead of stalling the crew; `respect_context_window: true` on `research_director` and `academic_analyst`, which synthesize the largest context; `multimodal: true` on `document_analyst` for diagrams/screenshots in PDFs (note: `multimodal` is deprecated in `crewai==1.14.4`, slated for removal in v2.0 in favor of passing files natively); `inject_date: true` on `research_director` for date-grounded synthesis language. Verified in `tests/crews/test_crew_wiring.py::test_research_crew_agent_capability_flags`.
- **Citation guardrail** (`tools/citation_guardrail_tool.py`) — `check_citations()` is wired as `guardrail=` on `compile_research_report` (both the static `@task` and the `crew_for_sources()` dynamic build). Deterministic, no LLM: splits the report into `##` sections and rejects (returns `(False, reason)`, triggering a CrewAI retry) unless every non-heading, non-code-fence line in `## Core Concepts` and `## Code Examples` carries a URL, a `(Source: ...)`/`(Src: ...)` tag, or a local file path.
- **Typed compile-task output** — `compile_research_report` also sets `output_pydantic=ResearchReportOutput` (`report: str`, `sources: list[str]`, defined in `research_crew.py`), matching the CrewAI production-architecture guidance to type task outputs consumed elsewhere in the flow. `run_research_crew` in `main.py` reads `result.pydantic.report` / `.sources` (not `result.raw`) and populates `state.source_citations`. The guardrail validates the raw string first; `output_pydantic` conversion runs after, so both apply together without conflict.
- **CrewAI Skills** (`skills/*/SKILL.md`) — three markdown skills enforce style/fidelity/citation rules by convention rather than code: `beginner-guide-style` (define terms on first use, annotate every code block, outlines are prose-free contracts — applies to `WritingCrew`), `source-extraction-fidelity` (quote code verbatim, preserve exact benchmark figures, flag unreadable sources — applies to `ResearchCrew`), `grounded-citation-answering` (never answer from training data, always cite section/source — applies to `QACrew`). `WritingCrew` and `ResearchCrew` reference their skill's absolute path via a module-level `_BEGINNER_GUIDE_STYLE_SKILL` / equivalent constant built with `Path`.
- **`planning=True` on `ResearchCrew` and `WritingCrew`** — both set `planning=True` with a dedicated `planning_llm=LLM(model="anthropic/claude-sonnet-4-6")` on their `Crew(...)` construction, so CrewAI generates a step-by-step plan before executing tasks. `EnrichmentCrew` and `QACrew` do not use planning (single-agent/single-task, low value).
- **`reasoning: true`** — set on `research_director` (`research_crew/config/agents.yaml`) and `content_strategist` (`writing_crew/config/agents.yaml`), the two agents responsible for synthesis/strategy rather than mechanical extraction or prose generation.
- **Typed Knowledge sources in chatbot** — `_load_knowledge_sources()` in `chatbot.py` uses `TextFileKnowledgeSource` for the guide and research report, `JSONKnowledgeSource` for `metadata.json`, and `PDFKnowledgeSource` for original PDF inputs (all take `file_paths=[...]`, a list of `Path`), replacing an earlier approach that read file contents into `StringKnowledgeSource`.
- **Delegation** (`allow_delegation`) — explicit on every `ResearchCrew` agent rather than relying on CrewAI's default. All 4 specialists (`youtube_analyst`, `web_researcher`, `academic_analyst`, `document_analyst`) are leaf workers with `allow_delegation: false`. `research_director` is also `allow_delegation: false` — it is not the hierarchical-process manager; it only executes `compile_research_report` and receives specialist outputs as task `context`. The actual delegator in `Process.hierarchical` is CrewAI's own internal manager agent, driven by `manager_llm=LLM(model="anthropic/claude-sonnet-4-6")` (no `manager_agent` is set, so no user-defined agent performs delegation). `WritingCrew` is pure `Process.sequential` with zero delegation: `content_editor` always resolves reviewer-flagged problems directly (documenting unresolved ones under "## Known Gaps") rather than delegating rewrites back to `technical_writer` — chosen because the pipeline's context wiring is one-directional (outline → draft → review → edit) and a delegation loop back to an earlier stage would break that linear, auditable structure for a case (major structural rewrites) that the beginner-reviewer's problem list is expected to catch before drafting completes.

### Current state

- **`ResearchCrew`** — fully implemented: 5 agents with per-agent LLMs, 5 tasks, `crew_for_sources()` dynamic assembly, tools wired from `TOOL_REGISTRY`, `compile_research_report` has both `guardrail=check_citations` and `output_pydantic=ResearchReportOutput`.
- **`EnrichmentCrew`** — fully implemented: 1 agent (`web_search_agent`, haiku), 1 task (`gap_fill_task`), sequential, `memory=False`.
- **`WritingCrew`** — fully implemented: 4 agents (strategist, writer, reviewer with `system_template`, editor), 4 tasks with explicit context wiring, sequential, `memory=True`, `output_file` on `edit_and_publish`.
- **`GuideGeneratorFlow`** (`main.py`) — fully implemented: `GuideFlowState`, 7 flow nodes, SSRF/path-traversal/file-size security checks, topic inference, quality gate routing, enrichment append, output file writing. `get_inputs()` interactive prompt wired into `kickoff()`.
- **`get_inputs()`** (`main.py`) — interactive prompt: comma-separated URLs validated with `_URL_RE` regex, file paths verified with `Path.exists()`, optional topic hint, raises `ValueError` if no sources provided.
- **`tools/topic_inference_tool.py`** — fully implemented: pure function, no LLM.
- **`tools/research_quality_scorer_tool.py`** — fully implemented: `BaseTool` + standalone `score_report()`, 5-criterion regex rubric.
- **`chatbot.py`** — fully implemented: `StudentChatbotFlow(Flow[ChatbotState])`, `route_intent()` keyword dispatch (end/example/clarify/question), `QACrew` with knowledge+memory, `launch_chatbot(run_id)` entry point, `chat()` REPL. `ConversationalFlow` not available in `crewai==1.14.4`; implemented via standard `Flow` with a manual REPL loop.
- **`crews/qa_crew/`** — fully implemented: `tutor_agent` (claude-sonnet-4-6), `answer_question` task, sequential crew with VoyageAI embedder and `Memory`.
- **`skills/`** — fully implemented: 3 CrewAI Skills (`beginner-guide-style`, `source-extraction-fidelity`, `grounded-citation-answering`) referenced by `WritingCrew` and `ResearchCrew` via file path.
