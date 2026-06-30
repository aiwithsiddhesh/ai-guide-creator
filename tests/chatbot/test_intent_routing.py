"""Tests for intent routing — deterministic keyword matching, no LLM."""

import pytest

from guide_creator_flow.chatbot import route_intent


def test_route_end_keywords():
    for phrase in ["bye", "exit", "quit", "done", "thanks"]:
        assert route_intent(phrase) == "end", f"Expected 'end' for '{phrase}'"


def test_route_end_keywords_case_insensitive():
    assert route_intent("Bye") == "end"
    assert route_intent("QUIT") == "end"


def test_route_end_in_sentence():
    assert route_intent("I'm done for today, thanks!") == "end"


def test_route_example_keywords():
    for phrase in ["example", "show me", "code", "snippet"]:
        assert route_intent(phrase) == "example", f"Expected 'example' for '{phrase}'"


def test_route_example_in_sentence():
    assert route_intent("Can you give me a code example?") == "example"


def test_route_clarify_keywords():
    for phrase in ["simpler", "confused", "explain again", "don't understand"]:
        assert route_intent(phrase) == "clarify", f"Expected 'clarify' for '{phrase}'"


def test_route_clarify_in_sentence():
    assert route_intent("I'm confused about this part") == "clarify"


def test_route_default():
    assert route_intent("How do I install FastAPI?") == "question"
    assert route_intent("What is dependency injection?") == "question"
    assert route_intent("") == "question"
    assert route_intent("Tell me about path operations") == "question"
