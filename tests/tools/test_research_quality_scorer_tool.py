"""Tests for research_quality_scorer_tool — deterministic regex scoring."""

from guide_creator_flow.tools.research_quality_scorer_tool import score_report

_FULL_REPORT = """
## What is FastAPI

FastAPI is a modern web framework that allows you to build APIs with Python.
It is designed to solve the problem of slow API development.

## Installation

Install FastAPI using pip:

```bash
pip install fastapi uvicorn
```

## Core Concepts

1. Path operations
2. Request validation
3. Dependency injection

## Code Example

```python
from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}
```

## Sources

- https://fastapi.tiangolo.com/
- https://github.com/tiangolo/fastapi
"""

_EMPTY_REPORT = ""


def test_score_10_all_criteria():
    result = score_report(_FULL_REPORT)
    assert result.score == 10
    assert result.gaps == []


def test_score_0_empty_report():
    result = score_report(_EMPTY_REPORT)
    assert result.score == 0
    assert len(result.gaps) == 5


def test_criterion_1_what_is():
    report = "FastAPI is a modern web framework that allows rapid development."
    result = score_report(report)
    # only criterion 1 can possibly pass (no install, no code, no 3 concepts, no sources)
    assert result.score == 2
    assert "what the topic is" not in " ".join(result.gaps)


def test_criterion_2_install():
    report = "Install it:\n```\npip install fastapi\n```"
    result = score_report(report)
    # criterion 2 passes (install keyword + code fence), criterion 3 also passes (≥2 fences)
    matched_gaps = " ".join(result.gaps)
    assert "installation" not in matched_gaps


def test_criterion_3_code_example():
    report = "Here is code:\n```python\nprint('hello')\n```"
    result = score_report(report)
    matched_gaps = " ".join(result.gaps)
    assert "code example" not in matched_gaps


def test_criterion_4_three_concepts_via_h2():
    report = "## Concept A\ntext\n## Concept B\ntext\n## Concept C\ntext"
    result = score_report(report)
    matched_gaps = " ".join(result.gaps)
    assert "core concepts" not in matched_gaps


def test_criterion_4_three_concepts_via_numbered_list():
    report = "1. First\n2. Second\n3. Third"
    result = score_report(report)
    matched_gaps = " ".join(result.gaps)
    assert "core concepts" not in matched_gaps


def test_criterion_5_sources_section():
    report = "## Sources\n\n- https://example.com"
    result = score_report(report)
    matched_gaps = " ".join(result.gaps)
    assert "Sources" not in matched_gaps


def test_gaps_list_labels():
    result = score_report(_EMPTY_REPORT)
    gap_text = " ".join(result.gaps)
    assert "what the topic is" in gap_text
    assert "installation" in gap_text
    assert "code example" in gap_text
    assert "core concepts" in gap_text
    assert "Sources" in gap_text
