import re
from typing import Type

from pydantic import BaseModel, Field
from crewai.tools import BaseTool


class ResearchScoreInput(BaseModel):
    report: str = Field(..., description="The research report text to score.")


class ResearchScoreOutput(BaseModel):
    score: int
    gaps: list[str]


_INSTALL_RE = re.compile(
    r"\b(install|pip install|npm install|yarn add|brew install|apt-get|setup\.py|pyproject\.toml|requirements\.txt)\b",
    re.IGNORECASE,
)
_CODE_FENCE_RE = re.compile(r"```")
_H2_RE = re.compile(r"^##\s+\S", re.MULTILINE)
_NUMBERED_LIST_RE = re.compile(r"^\d+\.", re.MULTILINE)
_URL_RE = re.compile(r"https?://\S+")
_SOURCES_SECTION_RE = re.compile(r"^##\s+Sources?\b", re.MULTILINE | re.IGNORECASE)
_WHAT_IS_RE = re.compile(
    r"\b(what is|what are|is a|is an|are a|allows|enables|designed to|built for|used for|solves|problem)\b",
    re.IGNORECASE,
)


class ResearchQualityScorerTool(BaseTool):
    name: str = "Research Quality Scorer"
    description: str = (
        "Scores a research report on five 2-point criteria and returns the total score "
        "and a list of gap descriptions for any criteria that were not met."
    )
    args_schema: Type[BaseModel] = ResearchScoreInput

    def _run(self, report: str) -> str:
        result = score_report(report)
        return f"score={result.score} gaps={result.gaps}"

    def score(self, report: str) -> ResearchScoreOutput:
        return score_report(report)


def score_report(report: str) -> ResearchScoreOutput:
    score = 0
    gaps: list[str] = []

    # Criterion 1 — explains what the topic is and what problem it solves
    if _WHAT_IS_RE.search(report):
        score += 2
    else:
        gaps.append("missing explanation of what the topic is and what problem it solves")

    # Criterion 2 — contains installation or setup information
    if _INSTALL_RE.search(report) and _CODE_FENCE_RE.search(report):
        score += 2
    else:
        gaps.append("missing installation or setup information")

    # Criterion 3 — contains at least one working code example (≥1 code fence pair)
    if len(_CODE_FENCE_RE.findall(report)) >= 2:
        score += 2
    else:
        gaps.append("missing at least one working code example")

    # Criterion 4 — explains at least 3 core concepts (H2 headers or numbered list items)
    h2_count = len(_H2_RE.findall(report))
    numbered_count = len(_NUMBERED_LIST_RE.findall(report))
    if h2_count >= 3 or numbered_count >= 3:
        score += 2
    else:
        gaps.append("missing explanation of at least 3 core concepts")

    # Criterion 5 — sources cited (## Sources section + at least one URL)
    if _SOURCES_SECTION_RE.search(report) and _URL_RE.search(report):
        score += 2
    else:
        gaps.append("missing a ## Sources section with cited URLs")

    return ResearchScoreOutput(score=score, gaps=gaps)
