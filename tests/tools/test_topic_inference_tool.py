"""Tests for topic_inference_tool — pure function, no mocking needed."""

from guide_creator_flow.tools.topic_inference_tool import infer_topic


def test_extracts_from_domain():
    result = infer_topic(["https://fastapi.tiangolo.com/tutorial/"], [])
    assert result == "fastapi"


def test_extracts_from_docs_subdomain():
    result = infer_topic(["https://docs.djangoproject.com/en/5.0/"], [])
    assert result == "djangoproject"


def test_skips_generic_domain_github():
    result = infer_topic(["https://github.com/some/repo"], [])
    assert result == ""


def test_skips_generic_domain_arxiv():
    result = infer_topic(["https://arxiv.org/abs/2301.00001"], [])
    assert result == ""


def test_returns_empty_on_failure():
    result = infer_topic([], [])
    assert result == ""


def test_extracts_from_file_path():
    result = infer_topic([], ["inputs/langchain_tutorial.pdf"])
    assert result == "langchain-tutorial"


def test_most_common_wins():
    # fastapi appears twice, pydantic once
    urls = [
        "https://fastapi.tiangolo.com/",
        "https://fastapi.tiangolo.com/tutorial/",
        "https://docs.pydantic.dev/",
    ]
    result = infer_topic(urls, [])
    assert result == "fastapi"
