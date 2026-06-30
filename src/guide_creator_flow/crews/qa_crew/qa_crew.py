from crewai import Agent, Crew, Process, Task
from crewai.crews import CrewOutput
from crewai.knowledge.source.base_knowledge_source import BaseKnowledgeSource
from crewai.knowledge.knowledge_config import KnowledgeConfig
from crewai.project import CrewBase, agent, crew, task

_EMBEDDER = {"provider": "voyageai", "config": {"model": "voyage-3"}}


@CrewBase
class QACrew:
    """Single-agent sequential crew that answers student questions from knowledge sources."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    def __init__(self, knowledge_sources: list[BaseKnowledgeSource], **kwargs):
        self._knowledge_sources = knowledge_sources
        # @CrewBase wraps __init__; do not call super().__init__() — it is handled by the decorator.

    @agent
    def tutor_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["tutor_agent"],
            knowledge_sources=self._knowledge_sources,
            knowledge_config=KnowledgeConfig(results_limit=10, score_threshold=0.4),
            embedder=_EMBEDDER,
        )

    @task
    def answer_question(self) -> Task:
        return Task(config=self.tasks_config["answer_question"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            memory=True,
            embedder=_EMBEDDER,
            verbose=True,
        )
