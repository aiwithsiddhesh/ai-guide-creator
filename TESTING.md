# Testing

This project tests all deterministic logic exhaustively. LLM-generated content quality is treated as a separately-evaluated concern — it is not asserted on in CI, because the content of a language model's output is not deterministic and varies with model version and prompt drift.

## Test layout

| Directory | What it covers |
|---|---|
| `tests/tools/` | Pure-function logic: `research_quality_scorer_tool.py` (regex rubric, 5 criteria), `topic_inference_tool.py` (domain/filename extraction), `youtube_transcript_tool.py` (transcript fetching and formatting). No LLM involved — fully deterministic, asserted directly. |
| `tests/chatbot/` | `route_intent()` keyword dispatch — deterministic keyword matching, no LLM. |
| `tests/crews/` | Crew *wiring*: correct agents, tasks, process type, memory settings, and dynamic agent activation per source bucket (`crew_for_sources`). Verified without invoking any LLM by patching `TOOL_REGISTRY` with `MagicMock(spec=BaseTool)` values. |
| `tests/flow/` | Flow node logic: input validation (SSRF, path-traversal, file-size guards), output persistence (`metadata.json` completeness), and full routing across the flow sequence (`validate_inputs → run_research_crew → scrub_report → evaluate_research → [run_enrichment_crew] → run_writing_crew → save_outputs`) with all crew boundaries mocked. |

## What's intentionally not covered by automated tests

**Actual LLM output quality and content correctness** — whether the generated guide is accurate, well-structured, and beginner-friendly — is not asserted on in CI.

This is evaluated separately via the crewAI test harness:

```bash
crewai test --n_iterations 3 --model gpt-4o-mini
```

This requires `OPENAI_API_KEY` (evaluator only — the runtime uses Anthropic) and is not part of the default CI run. See `.github/workflows/ci.yml` for a non-blocking optional step that runs it when the secret is present.

## Running the tests

```bash
# Full suite
uv run pytest

# Single file
uv run pytest tests/flow/test_flow_end_to_end.py
```

No API keys required.
