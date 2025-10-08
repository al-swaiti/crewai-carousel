from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import CodeInterpreterTool, ScrapeWebsiteTool, FileWriterTool
from carousel.tools.imagen_tool import Imagen4Tool
from carousel.tools.llm import GeminiWithGoogleSearch
from carousel.tools.pdf_tool import PDFConversionTool
import os

# Instantiate the custom LLM for agents that need web search
grounded_llm = GeminiWithGoogleSearch()

# Instantiate the Plotly documentation scraping tool
plotly_scraper = ScrapeWebsiteTool(
    website_url="https://plotly.com/python/"
)

@CrewBase
class Carousel():
    """Carousel crew"""
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config['researcher'],
            llm=grounded_llm,
            verbose=True
        )

    @agent
    def visual_designer(self) -> Agent:
        return Agent(
            config=self.agents_config['visual_designer'],
            tools=[
                CodeInterpreterTool(), 
                Imagen4Tool(),
                plotly_scraper
            ],
            verbose=True
        )

    @agent
    def content_strategist(self) -> Agent:
        return Agent(
            config=self.agents_config['content_strategist'],
            verbose=True
        )

    @agent
    def html_designer(self) -> Agent:
        return Agent(
            config=self.agents_config['html_designer'],
            tools=[FileWriterTool()],
            llm=grounded_llm,
            verbose=True
        )

    @agent
    def pdf_converter(self) -> Agent:
        return Agent(
            config=self.agents_config['pdf_converter'],
            tools=[PDFConversionTool()],
            verbose=True
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config['research_task'],
            agent=self.researcher()
        )

    @task
    def visual_design_task(self) -> Task:
        return Task(
            config=self.tasks_config['visual_design_task'],
            context=[self.research_task()],
            agent=self.visual_designer()
        )

    @task
    def content_structuring_task(self) -> Task:
        return Task(
            config=self.tasks_config['content_structuring_task'],
            context=[self.visual_design_task()],
            agent=self.content_strategist()
        )

    @task
    def html_design_task(self) -> Task:
        return Task(
            config=self.tasks_config['html_design_task'],
            context=[self.content_structuring_task()],
            agent=self.html_designer(),
            output_file='report.html'
        )

    @task
    def pdf_conversion_task(self) -> Task:
        return Task(
            config=self.tasks_config['pdf_conversion_task'],
            context=[self.html_design_task()],
            agent=self.pdf_converter(),
            output_file='report.pdf'
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Carousel crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            memory=False,
            embedder={
                "provider": "google-generativeai",
                "config": {
                    "model": "models/text-embedding-004",
                    "api_key": os.environ.get("GEMINI_API_KEY"),
                },
            },
            
        )