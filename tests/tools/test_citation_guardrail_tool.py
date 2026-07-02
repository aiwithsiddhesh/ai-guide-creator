"""Tests for citation_guardrail_tool — structural citation enforcement on the
research_director's compile_research_report task output."""

from crewai.tasks.task_output import TaskOutput

from guide_creator_flow.tools.citation_guardrail_tool import check_citations


def _output(raw: str) -> TaskOutput:
    return TaskOutput(description="compile research report", raw=raw, agent="Research Director")


_UNCITED_REPORT = """
## Overview

FastAPI is a modern web framework for building APIs with Python.

## Installation & Setup

Install FastAPI using pip:

```bash
pip install fastapi uvicorn
```

## Core Concepts

### Path Operations

Path operations let you define routes with decorators.

### Dependency Injection

Dependency injection lets you share logic across path operations cleanly.

## Code Examples

```python
from fastapi import FastAPI
app = FastAPI()
```

## Sources

- https://fastapi.tiangolo.com/

## Sources Not Accessible

(none)
"""

_CITED_REPORT = """
## Overview

FastAPI is a modern web framework for building APIs with Python.

## Installation & Setup

Install FastAPI using pip:

```bash
pip install fastapi uvicorn
```

## Core Concepts

### Path Operations

Path operations let you define routes with decorators. (Source: https://fastapi.tiangolo.com/tutorial/)

### Dependency Injection

Dependency injection lets you share logic across path operations cleanly. (Source: https://fastapi.tiangolo.com/tutorial/dependencies/)

## Code Examples

```python
from fastapi import FastAPI
app = FastAPI()
```
(Source: https://fastapi.tiangolo.com/)

## Sources

- https://fastapi.tiangolo.com/
- https://fastapi.tiangolo.com/tutorial/

## Sources Not Accessible

(none)
"""


def test_rejects_uncited_claims_in_core_concepts_and_code_examples():
    passed, reason = check_citations(_output(_UNCITED_REPORT))
    assert passed is False
    assert "Core Concepts" in reason
    assert "Code Examples" in reason


def test_accepts_fully_cited_report():
    passed, result = check_citations(_output(_CITED_REPORT))
    assert passed is True
    assert result == _CITED_REPORT


def test_rejects_when_core_concepts_section_missing():
    report = "## Overview\nSome text.\n\n## Code Examples\n```python\nprint(1)\n```\n(Source: https://example.com)\n"
    passed, reason = check_citations(_output(report))
    assert passed is False
    assert "Core Concepts" in reason


def test_rejects_when_code_examples_section_missing():
    report = "## Overview\nSome text.\n\n## Core Concepts\n### A\nSome claim. (Source: https://example.com)\n"
    passed, reason = check_citations(_output(report))
    assert passed is False
    assert "Code Examples" in reason


def test_file_path_counts_as_citation():
    report = (
        "## Core Concepts\n"
        "### A\n"
        "Explained in inputs/notes.md.\n\n"
        "## Code Examples\n"
        "```python\nprint(1)\n```\n"
        "See inputs/notes.md for context.\n"
    )
    passed, _ = check_citations(_output(report))
    assert passed is True
