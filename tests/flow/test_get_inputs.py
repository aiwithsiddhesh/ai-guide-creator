"""Tests for get_inputs() pre-validation — no real I/O, mocked input()."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from guide_creator_flow.main import get_inputs, _parse_csv, _URL_RE


# ---------------------------------------------------------------------------
# _parse_csv helper
# ---------------------------------------------------------------------------

def test_parse_csv_strips_whitespace():
    assert _parse_csv("  a , b , c  ") == ["a", "b", "c"]


def test_parse_csv_ignores_empty_entries():
    assert _parse_csv(",, a ,,") == ["a"]


def test_parse_csv_empty_string():
    assert _parse_csv("") == []


# ---------------------------------------------------------------------------
# _URL_RE
# ---------------------------------------------------------------------------

def test_url_re_accepts_http():
    assert _URL_RE.match("http://example.com/path")


def test_url_re_accepts_https():
    assert _URL_RE.match("https://fastapi.tiangolo.com/")


def test_url_re_rejects_missing_scheme():
    assert not _URL_RE.match("example.com")


def test_url_re_rejects_ftp():
    assert not _URL_RE.match("ftp://example.com")


# ---------------------------------------------------------------------------
# get_inputs() — via mocked input()
# ---------------------------------------------------------------------------

def _make_inputs(*responses):
    """Return a side_effect list for patching builtins.input."""
    return list(responses)


def test_get_inputs_valid_url():
    responses = [
        "https://youtube.com/watch?v=abc",  # youtube
        "",                                 # web
        "",                                 # papers
        "",                                 # docs
        "FastAPI",                          # topic hint
    ]
    with patch("builtins.input", side_effect=responses):
        result = get_inputs()
    assert result["youtube_links"] == ["https://youtube.com/watch?v=abc"]
    assert result["webpage_links"] == []
    assert result["topic_hint"] == "FastAPI"


def test_get_inputs_skips_invalid_urls(capsys):
    responses = [
        "",                    # youtube
        "not-a-url, https://example.com",  # web — one bad, one good
        "",                    # papers
        "",                    # docs
        "",                    # topic hint
    ]
    with patch("builtins.input", side_effect=responses):
        result = get_inputs()
    assert result["webpage_links"] == ["https://example.com"]
    captured = capsys.readouterr()
    assert "invalid URL" in captured.out


def test_get_inputs_skips_missing_files(tmp_path, capsys):
    responses = [
        "",                          # youtube
        "",                          # web
        "",                          # papers
        f"/nonexistent/file.pdf, {tmp_path}",  # docs — one missing, one dir (exists)
        "",                          # topic hint
    ]
    # tmp_path itself exists as a directory — enough to pass the exists() check
    with patch("builtins.input", side_effect=responses):
        result = get_inputs()
    assert str(tmp_path) in result["document_paths"]
    assert "/nonexistent/file.pdf" not in result["document_paths"]
    captured = capsys.readouterr()
    assert "file not found" in captured.out


def test_get_inputs_raises_when_no_sources():
    responses = ["", "", "", "", ""]
    with patch("builtins.input", side_effect=responses):
        with pytest.raises(ValueError, match="At least one source"):
            get_inputs()
