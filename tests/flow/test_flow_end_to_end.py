"""End-to-end flow routing tests — all crew boundaries mocked, no LLM calls."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from guide_creator_flow.main import GuideGeneratorFlow
from guide_creator_flow.tools.research_quality_scorer_tool import ResearchScoreOutput


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

_FAKE_RESEARCH = "Research report content."
_FAKE_ENRICHMENT = "Supplementary findings."
_FAKE_GUIDE = "# Getting Started\n\nFinal guide content."


def _crew_instance_mock(raw: str) -> MagicMock:
    """
    Return a mock that looks like an instantiated crewAI Crew.
    mock.kickoff(...) -> MagicMock(raw=raw)
    mock.crew_for_sources(...) -> self  (so run_research_crew gets the same mock back)
    """
    m = MagicMock()
    m.kickoff.return_value = MagicMock(raw=raw)
    m.crew_for_sources.return_value = m
    m.crew.return_value = m
    return m


def _setup_flow(tmp_path: Path, monkeypatch) -> GuideGeneratorFlow:
    """
    Prepare a flow with one valid local document under a tmp DOCUMENT_INPUT_DIR.
    Chdir into tmp_path so save_outputs writes there.
    """
    monkeypatch.chdir(tmp_path)
    doc_dir = tmp_path / "inputs"
    doc_dir.mkdir()
    fake_doc = doc_dir / "source.txt"
    fake_doc.write_text("source content")
    monkeypatch.setenv("DOCUMENT_INPUT_DIR", str(doc_dir))

    flow = GuideGeneratorFlow()
    flow.state.document_paths = [str(fake_doc)]
    return flow


# ---------------------------------------------------------------------------
# Test 1 — sufficient quality: Enrichment Crew must NOT be called
# ---------------------------------------------------------------------------

def test_full_flow_sufficient_quality_skips_enrichment(tmp_path, monkeypatch):
    flow = _setup_flow(tmp_path, monkeypatch)

    research_mock = _crew_instance_mock(_FAKE_RESEARCH)
    enrichment_mock = _crew_instance_mock(_FAKE_ENRICHMENT)
    writing_mock = _crew_instance_mock(_FAKE_GUIDE)

    sufficient_score = ResearchScoreOutput(score=8, gaps=[])

    with (
        patch("guide_creator_flow.main.ResearchCrew", return_value=research_mock),
        patch("guide_creator_flow.main.EnrichmentCrew", return_value=enrichment_mock),
        patch("guide_creator_flow.main.WritingCrew", return_value=writing_mock),
        patch(
            "guide_creator_flow.main.ResearchQualityScorerTool.score",
            return_value=sufficient_score,
        ),
    ):
        flow.validate_inputs()
        flow.run_research_crew()
        flow.scrub_report()
        route = flow.evaluate_research()

        assert route == "sufficient"
        assert flow.state.research_quality_score == 8
        assert flow.state.research_report == _FAKE_RESEARCH

        # Sufficient branch — skip enrichment, go straight to writing
        flow.run_writing_crew()
        flow.save_outputs()

    # Enrichment kickoff must never have fired
    enrichment_mock.kickoff.assert_not_called()

    assert flow.state.final_guide == _FAKE_GUIDE
    assert flow.state.guide_word_count > 0

    out_dir = tmp_path / "outputs" / flow.state.run_id
    assert (out_dir / "getting_started_guide.md").exists()
    assert (out_dir / "metadata.json").exists()


# ---------------------------------------------------------------------------
# Test 2 — insufficient quality: Enrichment Crew MUST be called once
# ---------------------------------------------------------------------------

def test_full_flow_insufficient_quality_runs_enrichment(tmp_path, monkeypatch):
    flow = _setup_flow(tmp_path, monkeypatch)

    research_mock = _crew_instance_mock(_FAKE_RESEARCH)
    enrichment_mock = _crew_instance_mock(_FAKE_ENRICHMENT)
    writing_mock = _crew_instance_mock(_FAKE_GUIDE)

    gap = "missing installation or setup information"
    insufficient_score = ResearchScoreOutput(score=4, gaps=[gap])

    with (
        patch("guide_creator_flow.main.ResearchCrew", return_value=research_mock),
        patch("guide_creator_flow.main.EnrichmentCrew", return_value=enrichment_mock),
        patch("guide_creator_flow.main.WritingCrew", return_value=writing_mock),
        patch(
            "guide_creator_flow.main.ResearchQualityScorerTool.score",
            return_value=insufficient_score,
        ),
    ):
        flow.validate_inputs()
        flow.run_research_crew()
        flow.scrub_report()
        route = flow.evaluate_research()

        assert route == "insufficient"
        assert flow.state.research_quality_score == 4
        assert flow.state.research_gaps == [gap]

        flow.run_enrichment_crew()

        # Enrichment kickoff called once; gaps input derived from state.research_gaps
        enrichment_mock.kickoff.assert_called_once()
        call_inputs = enrichment_mock.kickoff.call_args[1]["inputs"]
        assert f"- {gap}" in call_inputs["gaps"]

        # _append_to_report splices the supplementary section into the report
        assert "## Supplementary Research (Gap-Fill)" in flow.state.research_report
        assert _FAKE_ENRICHMENT in flow.state.research_report

        flow.run_writing_crew()
        flow.save_outputs()

    assert flow.state.final_guide == _FAKE_GUIDE

    out_dir = tmp_path / "outputs" / flow.state.run_id
    assert (out_dir / "getting_started_guide.md").exists()
    assert (out_dir / "metadata.json").exists()
