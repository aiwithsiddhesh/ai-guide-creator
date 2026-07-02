from pathlib import Path

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

_BEGINNER_GUIDE_STYLE_SKILL = str(
    (Path(__file__).parent.parent.parent / "skills" / "beginner-guide-style").resolve()
)


@CrewBase
class WritingCrew:
    """Writing Crew — sequential four-step pipeline: outline → draft → review → edit."""

    # ------------------------------------------------------------------
    # Agents — no tools, all pure reasoning
    # ------------------------------------------------------------------

    @agent
    def content_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config["content_strategist"],
            skills=[_BEGINNER_GUIDE_STYLE_SKILL],
            verbose=True,
        )

    @agent
    def technical_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["technical_writer"],
            skills=[_BEGINNER_GUIDE_STYLE_SKILL],
            verbose=True,
        )

    @agent
    def beginner_reviewer(self) -> Agent:
        return Agent(
            config=self.agents_config["beginner_reviewer"],
            verbose=True,
        )

    @agent
    def content_editor(self) -> Agent:
        return Agent(
            config=self.agents_config["content_editor"],
            skills=[_BEGINNER_GUIDE_STYLE_SKILL],
            verbose=True,
        )

    # ------------------------------------------------------------------
    # Tasks — context wiring matches the plan exactly
    # ------------------------------------------------------------------

    @task
    def create_outline(self) -> Task:
        return Task(config=self.tasks_config["create_outline"])

    @task
    def write_draft(self) -> Task:
        return Task(config=self.tasks_config["write_draft"])

    @task
    def review_draft(self) -> Task:
        # context: write_draft only — create_outline deliberately excluded
        # so the reviewer sees only what a real beginner sees
        return Task(config=self.tasks_config["review_draft"])

    @task
    def edit_and_publish(self) -> Task:
        return Task(config=self.tasks_config["edit_and_publish"])

    # ------------------------------------------------------------------
    # Crew — memory=True so the editor has full history
    # ------------------------------------------------------------------

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=True,
        )
