from crewai import Agent, Crew, LLM, Process, Task
from crewai.project import CrewBase, agent, crew, task

from guide_creator_flow.tool_registry import TOOL_REGISTRY


@CrewBase
class ResearchCrew:
    """Research Crew — hierarchical, dynamic agent activation per source type."""

    # ------------------------------------------------------------------
    # Agents
    # ------------------------------------------------------------------

    @agent
    def research_director(self) -> Agent:
        return Agent(
            config=self.agents_config["research_director"],
            verbose=True,
        )

    @agent
    def youtube_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["youtube_analyst"],
            tools=[TOOL_REGISTRY["youtube_transcript"]],
            verbose=True,
        )

    @agent
    def web_researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["web_researcher"],
            tools=[
                TOOL_REGISTRY["scrape_website"],
                TOOL_REGISTRY["firecrawl_scrape"],
            ],
            verbose=True,
        )

    @agent
    def academic_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["academic_analyst"],
            tools=[TOOL_REGISTRY["arxiv_paper"]],
            verbose=True,
        )

    @agent
    def document_analyst(self) -> Agent:
        return Agent(
            config=self.agents_config["document_analyst"],
            tools=[
                TOOL_REGISTRY["file_read"],
                TOOL_REGISTRY["firecrawl_scrape"],
            ],
            verbose=True,
        )

    # ------------------------------------------------------------------
    # Tasks
    # ------------------------------------------------------------------

    @task
    def analyse_youtube_sources(self) -> Task:
        return Task(config=self.tasks_config["analyse_youtube_sources"])

    @task
    def scrape_web_sources(self) -> Task:
        return Task(config=self.tasks_config["scrape_web_sources"])

    @task
    def analyse_research_papers(self) -> Task:
        return Task(config=self.tasks_config["analyse_research_papers"])

    @task
    def process_documents(self) -> Task:
        return Task(config=self.tasks_config["process_documents"])

    @task
    def compile_research_report(self) -> Task:
        return Task(config=self.tasks_config["compile_research_report"])

    # ------------------------------------------------------------------
    # Standard crew (all agents/tasks — used for crewai test + standalone)
    # ------------------------------------------------------------------

    @crew
    def crew(self) -> Crew:
        """Standard crew with all agents and tasks. Used for standalone testing."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.hierarchical,
            manager_llm=LLM(model="anthropic/claude-sonnet-4-6"),
            verbose=True,
            memory=False,
        )

    # ------------------------------------------------------------------
    # Dynamic crew — only activates specialists for non-empty source buckets
    # ------------------------------------------------------------------

    def crew_for_sources(
        self,
        youtube_links: list[str],
        webpage_links: list[str],
        research_paper_links: list[str],
        document_paths: list[str],
    ) -> Crew:
        """Build a crew at runtime with only the specialists whose source bucket is non-empty.

        The `context` key is stripped from the compile_research_report YAML dict and replaced
        with a dynamic list of only the tasks that actually ran, so the manager never receives
        empty specialist reports.
        """
        active_agents: list[Agent] = []
        active_tasks: list[Task] = []
        compile_context: list[Task] = []

        def _task(key: str, agent_instance: Agent) -> Task:
            """Build a Task from YAML config, overriding the agent string with an instance."""
            cfg = {k: v for k, v in self.tasks_config[key].items() if k != "agent"}
            return Task(**cfg, agent=agent_instance)

        if youtube_links:
            agent_instance = self.youtube_analyst()
            t = _task("analyse_youtube_sources", agent_instance)
            active_agents.append(agent_instance)
            active_tasks.append(t)
            compile_context.append(t)

        if webpage_links:
            agent_instance = self.web_researcher()
            t = _task("scrape_web_sources", agent_instance)
            active_agents.append(agent_instance)
            active_tasks.append(t)
            compile_context.append(t)

        if research_paper_links:
            agent_instance = self.academic_analyst()
            t = _task("analyse_research_papers", agent_instance)
            active_agents.append(agent_instance)
            active_tasks.append(t)
            compile_context.append(t)

        if document_paths:
            agent_instance = self.document_analyst()
            t = _task("process_documents", agent_instance)
            active_agents.append(agent_instance)
            active_tasks.append(t)
            compile_context.append(t)

        # Strip static `context` and `agent` from YAML before constructing compile task
        compile_cfg = {
            k: v
            for k, v in self.tasks_config["compile_research_report"].items()
            if k not in ("context", "agent")
        }
        compile_task = Task(
            **compile_cfg,
            agent=self.research_director(),
            context=compile_context,
        )
        active_tasks.append(compile_task)

        return Crew(
            agents=active_agents,
            tasks=active_tasks,
            process=Process.hierarchical,
            manager_llm=LLM(model="anthropic/claude-sonnet-4-6"),
            verbose=True,
            memory=False,
        )
