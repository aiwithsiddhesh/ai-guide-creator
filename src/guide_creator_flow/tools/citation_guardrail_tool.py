import re

from crewai.tasks.task_output import TaskOutput

_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_URL_RE = re.compile(r"https?://\S+")
_SOURCE_TAG_RE = re.compile(r"\((?:source|src)[:\-][^)]+\)", re.IGNORECASE)
_FILE_PATH_RE = re.compile(r"[\w./\\-]+\.(?:pdf|md|txt|docx?|csv|json|ya?ml)\b", re.IGNORECASE)

# Sections whose claims must each carry a traceable citation.
_CITED_SECTIONS = ("Core Concepts", "Code Examples")


def _has_citation(text: str) -> bool:
    return bool(
        _URL_RE.search(text) or _SOURCE_TAG_RE.search(text) or _FILE_PATH_RE.search(text)
    )


def _split_sections(report: str) -> dict[str, str]:
    """Split a report into {heading title: section body} by H2 headings."""
    matches = list(_SECTION_RE.finditer(report))
    sections: dict[str, str] = {}
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(report)
        sections[title] = report[start:end].strip()
    return sections


def check_citations(output: TaskOutput) -> tuple[bool, str]:
    """Reject a research report unless every claim in the cited sections carries a citation.

    A "claim" is any non-blank line that isn't itself a heading. Each such line must
    contain a URL, a `(Source: ...)`/`(Src: ...)` tag, or a local file path — otherwise
    it cannot be traced back to ## Sources, violating the report's own citation rule.
    """
    report = output.raw
    sections = _split_sections(report)

    missing_sections = [name for name in _CITED_SECTIONS if name not in sections]
    if missing_sections:
        return (
            False,
            "Report is missing required section(s): "
            + ", ".join(f"## {name}" for name in missing_sections)
            + ". Add them before the report can be accepted.",
        )

    uncited_claims: list[str] = []
    for section_name in _CITED_SECTIONS:
        body = sections[section_name]
        in_code_block = False
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code_block = not in_code_block
                continue
            if not stripped or stripped.startswith("#") or in_code_block:
                continue
            if not _has_citation(stripped):
                uncited_claims.append(f"[{section_name}] {stripped[:120]}")

    if uncited_claims:
        listed = "\n".join(f"- {claim}" for claim in uncited_claims[:10])
        more = f"\n(+{len(uncited_claims) - 10} more)" if len(uncited_claims) > 10 else ""
        return (
            False,
            "Every claim in ## Core Concepts and ## Code Examples must carry a citation "
            "(a source URL, a `(Source: ...)` tag, or a file path). The following lines "
            f"have no citation:\n{listed}{more}\n"
            "Add an explicit source reference to each of these lines and resubmit.",
        )

    return (True, report)
