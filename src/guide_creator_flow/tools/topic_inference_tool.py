import re
from urllib.parse import urlparse

_GENERIC_DOMAINS = frozenset({
    "github", "arxiv", "docs", "medium", "stackoverflow",
    "reddit", "wikipedia", "youtube", "youtu", "twitter",
    "x", "linkedin", "substack", "notion", "confluence",
    "gitlab", "bitbucket", "npmjs", "pypi", "hub",
    # common TLDs to ignore
    "com", "org", "net", "io", "dev", "ai", "co", "edu", "gov",
})

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def infer_topic(urls: list[str], file_paths: list[str]) -> str:
    """Return the most likely topic name from URLs and file paths, or '' if unclear."""
    candidates: list[str] = []

    for url in urls:
        try:
            host = urlparse(url).hostname or ""
        except Exception:
            continue
        # strip www / cdn prefixes
        parts = host.lower().split(".")
        parts = [p for p in parts if p not in ("www", "cdn", "api", "static")]
        # first non-generic, non-TLD part is the candidate
        for part in parts:
            if part not in _GENERIC_DOMAINS and len(part) > 2:
                candidates.append(part)
                break

    for path in file_paths:
        stem = re.split(r"[/\\]", path)[-1]
        stem = stem.rsplit(".", 1)[0]
        slug = _SLUG_RE.sub("-", stem.lower()).strip("-")
        if slug and slug not in _GENERIC_DOMAINS and len(slug) > 2:
            candidates.append(slug)

    if not candidates:
        return ""

    # Return the most common candidate; ties broken by first occurrence
    ranked = sorted(set(candidates), key=lambda c: (-candidates.count(c), candidates.index(c)))
    return ranked[0]
