#!/usr/bin/env python
"""Student Chatbot — conversational interface grounded in guide and source material."""

import os
from pathlib import Path

from pydantic import BaseModel

from crewai.flow import Flow, listen, router, start
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource
from crewai.knowledge.source.pdf_knowledge_source import PDFKnowledgeSource

from guide_creator_flow.crews.qa_crew.qa_crew import QACrew


# ---------------------------------------------------------------------------
# Intent routing
# ---------------------------------------------------------------------------

_END_KEYWORDS = frozenset({"bye", "exit", "quit", "done", "thanks"})
_EXAMPLE_KEYWORDS = frozenset({"example", "show me", "code", "snippet"})
_CLARIFY_KEYWORDS = frozenset({"simpler", "confused", "explain again", "don't understand"})


def route_intent(message: str) -> str:
    """Return intent label based on keyword matching."""
    lower = message.lower().strip()
    if any(kw in lower for kw in _END_KEYWORDS):
        return "end"
    if any(kw in lower for kw in _EXAMPLE_KEYWORDS):
        return "example"
    if any(kw in lower for kw in _CLARIFY_KEYWORDS):
        return "clarify"
    return "question"


# ---------------------------------------------------------------------------
# Chatbot state
# ---------------------------------------------------------------------------

class _Message(BaseModel):
    role: str
    content: str


class ChatbotState(BaseModel):
    run_id: str = ""
    topic: str = ""
    source_types: list[str] = []
    messages: list[_Message] = []
    last_user_message: str = ""
    last_intent: str = ""
    reply: str = ""


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------

class StudentChatbotFlow(Flow[ChatbotState]):
    """One-turn flow: receives a student message, routes by intent, calls QACrew."""

    def __init__(self, knowledge_sources: list, **kwargs):
        super().__init__(**kwargs)
        # Knowledge sources loaded once; reused across all turns
        self._qa_crew = QACrew(knowledge_sources=knowledge_sources)

    # ------------------------------------------------------------------
    # Entry point for each turn
    # ------------------------------------------------------------------

    @start()
    def receive_message(self):
        """Entry node — intent is already set on state before kickoff."""
        pass

    @router(receive_message)
    def route_intent_node(self):
        """Route to the correct handler based on last_intent."""
        return self.state.last_intent

    # ------------------------------------------------------------------
    # Intent handlers
    # ------------------------------------------------------------------

    @listen("question")
    def handle_question(self):
        question = self.state.last_user_message
        self._run_qa(question)

    @listen("clarify")
    def handle_clarify(self):
        question = f"Please re-explain more simply: {self.state.last_user_message}"
        self._run_qa(question)

    @listen("example")
    def handle_example(self):
        question = f"Show a concrete code example for: {self.state.last_user_message}"
        self._run_qa(question)

    @listen("end")
    def handle_end(self):
        self.state.reply = (
            f"Thanks for studying {self.state.topic or 'the guide'}! "
            "Good luck — feel free to come back any time."
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _run_qa(self, question: str):
        history = self._format_history()
        result = self._qa_crew.crew().kickoff(inputs={
            "topic": self.state.topic or "the topic",
            "question": question,
            "history": history,
        })
        self.state.reply = result.raw

    def _format_history(self) -> str:
        last_10 = self.state.messages[-10:]
        return "\n".join(f"{m.role.upper()}: {m.content}" for m in last_10) or "(none)"

    def _append_message(self, role: str, content: str):
        self.state.messages.append(_Message(role=role, content=content))

    # ------------------------------------------------------------------
    # REPL
    # ------------------------------------------------------------------

    def chat(self):
        """Terminal REPL — blocks until the user says goodbye."""
        topic_label = self.state.topic or "the guide"
        print(f"\n=== Student Chatbot — {topic_label} ===")
        print("Ask questions about the guide. Type 'bye' to exit.\n")

        while True:
            try:
                user_input = input("You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nSession ended.")
                break

            if not user_input:
                continue

            intent = route_intent(user_input)
            self._append_message("user", user_input)

            self.state.last_user_message = user_input
            self.state.last_intent = intent
            self.state.reply = ""

            self.kickoff()

            reply = self.state.reply
            self._append_message("assistant", reply)
            print(f"\nTutor: {reply}\n")

            if intent == "end":
                break


# ---------------------------------------------------------------------------
# Knowledge source factory
# ---------------------------------------------------------------------------

def _load_knowledge_sources(run_id: str) -> list:
    out_dir = Path("outputs") / run_id
    sources = []

    guide_path = out_dir / "getting_started_guide.md"
    if guide_path.exists():
        sources.append(StringKnowledgeSource(
            content=guide_path.read_text(encoding="utf-8"),
            metadata={"source": "getting_started_guide.md"},
        ))

    report_path = out_dir / "research_report.md"
    if report_path.exists():
        sources.append(StringKnowledgeSource(
            content=report_path.read_text(encoding="utf-8"),
            metadata={"source": "research_report.md"},
        ))

    # PDF files from original document_paths recorded in metadata
    import json
    metadata_path = out_dir / "metadata.json"
    if metadata_path.exists():
        meta = json.loads(metadata_path.read_text(encoding="utf-8"))
        for path_str in meta.get("document_paths", []):
            p = Path(path_str)
            if p.exists() and p.suffix.lower() == ".pdf":
                sources.append(PDFKnowledgeSource(file_path=str(p)))

    return sources


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def launch_chatbot_cli():
    """CLI entry point — reads run_id from argv and starts the chat REPL."""
    import sys

    if len(sys.argv) < 2:
        raise Exception(
            "No run_id provided. Usage: chat <run_id>  "
            "(run_id is the outputs/<run_id> folder name from a prior 'crewai run')"
        )
    run_id = sys.argv[1]
    launch_chatbot(run_id)


def launch_chatbot(run_id: str):
    """Load knowledge from outputs/<run_id>/ and start the terminal chat session."""
    # Isolate knowledge store per run
    os.environ["CREWAI_STORAGE_DIR"] = f"./outputs/{run_id}/.crewai"

    out_dir = Path("outputs") / run_id
    topic = ""
    import json
    metadata_path = out_dir / "metadata.json"
    if metadata_path.exists():
        meta = json.loads(metadata_path.read_text(encoding="utf-8"))
        topic = meta.get("topic", "")

    knowledge_sources = _load_knowledge_sources(run_id)
    if not knowledge_sources:
        raise FileNotFoundError(
            f"No guide or report found in outputs/{run_id}/. "
            "Run the guide generation flow first."
        )

    flow = StudentChatbotFlow(knowledge_sources=knowledge_sources)
    flow.state.run_id = run_id
    flow.state.topic = topic

    try:
        flow.chat()
    finally:
        pass  # finalize_session_traces() not available in crewai==1.14.4
