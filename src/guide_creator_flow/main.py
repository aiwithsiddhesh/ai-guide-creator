#!/usr/bin/env python
import json
import re
import socket
import ipaddress
from datetime import datetime
from pathlib import Path

import requests
from pydantic import BaseModel

from crewai.flow import Flow, listen, or_, persist, router, start

from guide_creator_flow.crews.research_crew.research_crew import ResearchCrew
from guide_creator_flow.crews.enrichment_crew.enrichment_crew import EnrichmentCrew
from guide_creator_flow.crews.writing_crew.writing_crew import WritingCrew
from guide_creator_flow.tools.topic_inference_tool import infer_topic
from guide_creator_flow.tools.research_quality_scorer_tool import ResearchQualityScorerTool


# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

_PRIVATE_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]

_INJECTION_PATTERN = re.compile(
    r"(ignore previous instructions?|forget (all )?previous|"
    r"you are now|act as|disregard (all )?prior|"
    r"system:\s*you|<\|system\|>|<\|user\|>)",
    re.IGNORECASE,
)


def _is_private_ip(hostname: str) -> bool:
    try:
        addr = ipaddress.ip_address(socket.gethostbyname(hostname))
        return any(addr in net for net in _PRIVATE_RANGES)
    except Exception:
        return False


def _scrub(text: str) -> str:
    return _INJECTION_PATTERN.sub("[REDACTED]", text)


def _append_to_report(existing: str, header: str, content: str) -> str:
    return existing + f"\n\n## {header}\n\n{content}"


def _topic_slug(topic: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")[:30] or "unknown"


# ---------------------------------------------------------------------------
# Flow State
# ---------------------------------------------------------------------------

class GuideFlowState(BaseModel):
    # inputs
    youtube_links: list[str] = []
    webpage_links: list[str] = []
    research_paper_links: list[str] = []
    document_paths: list[str] = []
    topic_hint: str = ""

    # derived
    source_types: list[str] = []

    # research outputs
    research_report: str = ""
    source_citations: list[str] = []
    research_quality_score: int = 0
    research_gaps: list[str] = []

    # writing outputs
    final_guide: str = ""
    guide_word_count: int = 0

    # control
    run_id: str = ""
    error_log: list[str] = []


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------

class GuideGeneratorFlow(Flow[GuideFlowState]):

    @start()
    def validate_inputs(self):
        """Sanitise inputs, check reachability, infer topic, set run_id."""
        document_input_dir = Path(
            __import__("os").environ.get("DOCUMENT_INPUT_DIR", "inputs")
        )
        max_file_bytes = int(
            __import__("os").environ.get("MAX_FILE_BYTES", 52428800)
        )

        # --- URL reachability & SSRF check ---
        safe_youtube, safe_web, safe_papers = [], [], []
        from urllib.parse import urlparse
        for bucket_in, bucket_out, label in [
            (self.state.youtube_links, safe_youtube, "youtube"),
            (self.state.webpage_links, safe_web, "web"),
            (self.state.research_paper_links, safe_papers, "paper"),
        ]:
            for url in bucket_in:
                try:
                    hostname = urlparse(url).hostname or ""
                    if _is_private_ip(hostname):
                        self.state.error_log.append(
                            f"SSRF: rejected private IP URL {url}"
                        )
                        continue
                    # Any HTTP response (including 4xx/5xx) means the host is reachable.
                    # Only a network-level exception (timeout, DNS failure) means unreachable.
                    requests.head(url, timeout=5, allow_redirects=True)
                except requests.exceptions.ConnectionError as exc:
                    self.state.error_log.append(
                        f"unreachable URL dropped: {url} ({exc})"
                    )
                    continue
                except requests.exceptions.Timeout:
                    self.state.error_log.append(
                        f"unreachable URL dropped (timeout): {url}"
                    )
                    continue
                except Exception:
                    pass  # non-network errors (SSL quirks, etc.) — treat URL as reachable
                bucket_out.append(url)
                if label not in self.state.source_types:
                    self.state.source_types.append(label)

        self.state.youtube_links = safe_youtube
        self.state.webpage_links = safe_web
        self.state.research_paper_links = safe_papers

        # --- Document path validation ---
        safe_docs = []
        for path_str in self.state.document_paths:
            p = Path(path_str)
            try:
                p.resolve().relative_to(document_input_dir.resolve())
            except ValueError:
                self.state.error_log.append(
                    f"path traversal rejected: {path_str}"
                )
                continue
            if not p.exists():
                self.state.error_log.append(f"file not found: {path_str}")
                continue
            if p.stat().st_size > max_file_bytes:
                self.state.error_log.append(
                    f"file too large (>{max_file_bytes} bytes): {path_str}"
                )
                continue
            safe_docs.append(path_str)
            if "document" not in self.state.source_types:
                self.state.source_types.append("document")

        self.state.document_paths = safe_docs

        # --- Guard: at least one source must survive validation ---
        if not any([
            self.state.youtube_links,
            self.state.webpage_links,
            self.state.research_paper_links,
            self.state.document_paths,
        ]):
            raise ValueError(
                "No valid sources remain after validation. "
                f"Errors: {self.state.error_log}"
            )

        # --- Topic inference ---
        if not self.state.topic_hint:
            all_urls = (
                self.state.youtube_links
                + self.state.webpage_links
                + self.state.research_paper_links
            )
            self.state.topic_hint = infer_topic(all_urls, self.state.document_paths)

        # --- run_id ---
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = _topic_slug(self.state.topic_hint)
        self.state.run_id = f"{ts}_{slug}"

    @listen(validate_inputs)
    def run_research_crew(self):
        """Run the dynamically assembled Research Crew."""
        crew = ResearchCrew().crew_for_sources(
            youtube_links=self.state.youtube_links,
            webpage_links=self.state.webpage_links,
            research_paper_links=self.state.research_paper_links,
            document_paths=self.state.document_paths,
        )
        result = crew.kickoff(inputs={
            "topic_hint": self.state.topic_hint,
            "youtube_links": self.state.youtube_links,
            "webpage_links": self.state.webpage_links,
            "research_paper_links": self.state.research_paper_links,
            "document_paths": self.state.document_paths,
        })
        self.state.research_report = result.raw

    @listen(run_research_crew)
    def scrub_report(self):
        """Strip prompt injection patterns from scraped content."""
        self.state.research_report = _scrub(self.state.research_report)

    @router(scrub_report)
    def evaluate_research(self):
        """Score research quality; return routing signal."""
        scorer = ResearchQualityScorerTool()
        output = scorer.score(self.state.research_report)
        self.state.research_quality_score = output.score
        self.state.research_gaps = output.gaps

        if output.score >= 6:
            return "sufficient"
        return "insufficient"

    @listen("insufficient")
    def run_enrichment_crew(self):
        """Gap-fill with web search when quality score < 6."""
        result = EnrichmentCrew().crew().kickoff(inputs={
            "topic_hint": self.state.topic_hint,
            "gaps": "\n".join(f"- {g}" for g in self.state.research_gaps),
        })
        self.state.research_report = _append_to_report(
            self.state.research_report,
            "Supplementary Research (Gap-Fill)",
            result.raw,
        )

    @listen(or_("sufficient", run_enrichment_crew))
    def run_writing_crew(self):
        """Run the Writing Crew to produce the final guide."""
        result = WritingCrew().crew().kickoff(inputs={
            "topic_hint": self.state.topic_hint,
            "research_report": self.state.research_report,
        })
        self.state.final_guide = result.raw
        self.state.guide_word_count = len(self.state.final_guide.split())

    @persist()
    @listen(run_writing_crew)
    def save_outputs(self):
        """Write all output files to outputs/<run_id>/."""
        out_dir = Path("outputs") / self.state.run_id
        out_dir.mkdir(parents=True, exist_ok=True)

        (out_dir / "getting_started_guide.md").write_text(
            self.state.final_guide, encoding="utf-8"
        )
        (out_dir / "research_report.md").write_text(
            self.state.research_report, encoding="utf-8"
        )

        import json
        metadata = {
            "run_id": self.state.run_id,
            "topic": self.state.topic_hint,
            "source_types": self.state.source_types,
            "quality_score": self.state.research_quality_score,
            "word_count": self.state.guide_word_count,
            "error_log": self.state.error_log,
            "state_id": str(self.state.id) if hasattr(self.state, "id") else "",
        }
        (out_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2), encoding="utf-8"
        )

        print(f"\nOutputs written to {out_dir}/")
        print(f"  Guide: {self.state.guide_word_count} words")
        print(f"  Quality score: {self.state.research_quality_score}/10")
        if self.state.error_log:
            print(f"  Errors: {len(self.state.error_log)} (see metadata.json)")


# ---------------------------------------------------------------------------
# Input layer
# ---------------------------------------------------------------------------

_URL_RE = re.compile(r"^https?://[^\s]+$")


def _parse_csv(raw: str) -> list[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def get_inputs() -> dict:
    """Interactive prompt that collects and pre-validates all flow inputs."""
    print("\n=== Guide Creator — Input Collection ===\n")

    # YouTube links
    raw = input("YouTube video URLs (comma-separated, or press Enter to skip):\n> ").strip()
    youtube_links = []
    for url in _parse_csv(raw):
        if _URL_RE.match(url):
            youtube_links.append(url)
        else:
            print(f"  [skip] invalid URL: {url}")

    # Web page links
    raw = input("\nWeb page URLs (comma-separated, or press Enter to skip):\n> ").strip()
    webpage_links = []
    for url in _parse_csv(raw):
        if _URL_RE.match(url):
            webpage_links.append(url)
        else:
            print(f"  [skip] invalid URL: {url}")

    # Research paper links (arXiv)
    raw = input("\nResearch paper URLs (comma-separated, or press Enter to skip):\n> ").strip()
    research_paper_links = []
    for url in _parse_csv(raw):
        if _URL_RE.match(url):
            research_paper_links.append(url)
        else:
            print(f"  [skip] invalid URL: {url}")

    # Local document paths
    raw = input("\nLocal file paths (comma-separated, or press Enter to skip):\n> ").strip()
    document_paths = []
    for path_str in _parse_csv(raw):
        if Path(path_str).exists():
            document_paths.append(path_str)
        else:
            print(f"  [skip] file not found: {path_str}")

    # Topic hint
    topic_hint = input(
        "\nTopic hint (optional — leave blank for auto-inference):\n> "
    ).strip()

    if not any([youtube_links, webpage_links, research_paper_links, document_paths]):
        raise ValueError("At least one source (URL or file) is required.")

    return {
        "youtube_links": youtube_links,
        "webpage_links": webpage_links,
        "research_paper_links": research_paper_links,
        "document_paths": document_paths,
        "topic_hint": topic_hint,
    }


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

def kickoff():
    inputs = get_inputs()
    GuideGeneratorFlow().kickoff(inputs)


def plot():
    GuideGeneratorFlow().plot()


def run_with_trigger():
    import sys

    if len(sys.argv) < 2:
        raise Exception("No trigger payload provided. Please provide JSON payload as argument.")

    try:
        payload = json.loads(sys.argv[1])
    except json.JSONDecodeError:
        raise Exception("Invalid JSON payload")

    flow = GuideGeneratorFlow()
    return flow.kickoff(payload)


if __name__ == "__main__":
    kickoff()
