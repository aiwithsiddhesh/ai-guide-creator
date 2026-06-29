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
```

## Usage

```bash
# Run the guide generation flow
crewai run

# Run with a JSON input payload
run_with_trigger '{"topic": "FastAPI"}'

# Plot the flow graph
plot
```

Output is written to `outputs/<run_id>/`:
- `getting_started_guide.md` — the generated guide
- `research_report.md` — reusable research; can be passed directly to the chatbot
- `metadata.json` — topic, source types, quality score, word count, error log

## How it works

Three crews run in sequence:

1. **Research Crew** — fetches and extracts content from all provided sources. Only the specialists needed for the given source types are activated (YouTube, web pages, arXiv papers, local files).
2. **Enrichment Crew** — runs targeted gap-fill web searches if the research quality score is below threshold. Skipped otherwise.
3. **Writing Crew** — produces the guide through a four-step pipeline: outline → full draft → beginner review → final edit.

After the guide is generated, launch the student chatbot:

```python
from guide_creator_flow.chatbot import launch_chatbot
launch_chatbot("<run_id>")
```

The chatbot answers questions grounded in the guide and original sources only. It cites which section or source each answer comes from, and says so explicitly when a question is not covered by the material.
