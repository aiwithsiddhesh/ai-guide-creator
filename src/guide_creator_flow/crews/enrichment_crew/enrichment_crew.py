from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from guide_creator_flow.tool_registry import TOOL_REGISTRY


@CrewBase
class EnrichmentCrew:
    """Enrichment Crew — sequential, gap-fill web search, runs only when quality score < 6."""

    @agent
    def web_search_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["web_search_agent"],
            tools=[
                TOOL_REGISTRY["serper_search"],
                TOOL_REGISTRY["scrape_website"],
                TOOL_REGISTRY["firecrawl_scrape"],
            ],
            verbose=True,
        )

    @task
    def gap_fill_task(self) -> Task:
        return Task(config=self.tasks_config["gap_fill_task"])

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,
        )
