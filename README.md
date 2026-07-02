# Guide Creator Flow

A CrewAI Flow that turns raw sources — YouTube videos, documentation pages, arXiv papers, local PDFs — into a publication-ready, beginner-friendly Markdown guide. After generation, a conversational student chatbot answers questions grounded exclusively in the generated guide and source material.

## Requirements

- Python >=3.10, <3.14
- [uv](https://docs.astral.sh/uv/) for dependency management

## Installation

```bash
pip install uv
crewai install
```

## Configuration

Copy `.env.example` to `.env` and fill in your API keys:

```
ANTHROPIC_API_KEY=     # all LLM calls
FIRECRAWL_API_KEY=     # JS-rendered page scraping
SERPER_API_KEY=        # gap-fill web search
VOYAGE_API_KEY=        # embeddings for knowledge and memory
OPENAI_API_KEY=        # crewai test evaluator only — not used at runtime

DOCUMENT_INPUT_DIR=documents    # local files must be under this directory
MAX_FILE_BYTES=52428800         # 50 MB default — files above this are rejected
CREWAI_STORAGE_DIR=.crewai      # LanceDB storage root for knowledge and memory
```

## Usage

```bash
# Run the guide generation flow
crewai run

# Run with a JSON input payload
run_with_trigger '{"topic": "FastAPI"}'

# Example payload using the shipped sample file under documents/
run_with_trigger '{"topic_hint": "FastAPI", "document_paths": ["documents/sample_notes.md"]}'

# Launch the student chatbot for a completed run
chat <run_id>

# Plot the flow graph
plot
```

Output is written to `outputs/<run_id>/`:
- `getting_started_guide.md` — the generated guide
- `research_report.md` — reusable research; can be passed directly to the chatbot
- `metadata.json` — topic, source types, quality score, word count, error log, document paths

## Testing

See [TESTING.md](TESTING.md) for the test strategy and how to run the suite.

## How it works

Three crews run in sequence:

1. **Research Crew** — fetches and extracts content from all provided sources. Only the specialists needed for the given source types are activated (YouTube, web pages, arXiv papers, local files).
2. **Enrichment Crew** — runs targeted gap-fill web searches if the research quality score is below threshold. Skipped otherwise. The quality score is a cheap regex heuristic (pattern-matches for explanations, install steps, code examples, etc.), not a semantic quality check — it can miss legitimately good research that's phrased differently, or pass shallow research that happens to match the patterns.
3. **Writing Crew** — produces the guide through a four-step pipeline: outline → full draft → beginner review → final edit.

After the guide is generated, a student chatbot can be launched against the same material:

```
chat <run_id>
```

The chatbot is powered by a fourth crew, the **QA Crew** — a single tutor agent with knowledge sources loaded from the generated guide, the research report, and any original PDF inputs. It answers questions grounded in the guide and original sources only, cites which section or source each answer comes from, and says so explicitly when a question is not covered by the material. Each turn is routed by intent (question / clarify / example / end) before being passed to the QA Crew.
