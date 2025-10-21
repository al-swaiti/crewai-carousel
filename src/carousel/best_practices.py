"""
Helpers for querying the Carousel research agent outside of the full crew run.

The visual interface can call into this module to fetch best-practice insights
without triggering the rest of the pipeline (visual design, HTML, PDF, etc.).
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Sequence

from crewai import Crew, Process, Task

from carousel.crew import Carousel


def fetch_best_practices(
    topic: str,
    slides: int = 5,
    aspect_ratio: str = "16:9",
    audience_persona: str = "General executive audience",
    *,
    verbose: bool = False,
) -> Sequence[Dict[str, Any]]:
    """
    Run only the research task from the Carousel crew and return its structured output.

    Parameters
    ----------
    topic:
        The subject to research.
    slides:
        The number of insights to request from the researcher.
    aspect_ratio:
        Passed through for contextual grounding so the agent can suggest fitting visuals.
    audience_persona:
        Persona that guides tone and framing.
    verbose:
        When True, surface CrewAI logging for debugging.
    """
    carousel = Carousel()

    research_agent = carousel.researcher()
    task_config = deepcopy(carousel.tasks_config["research_task"])

    research_task = Task(
        config=task_config,
        agent=research_agent,
        human_input=False,
        verbose=verbose,
    )

    research_crew = Crew(
        agents=[research_agent],
        tasks=[research_task],
        process=Process.sequential,
        verbose=verbose,
    )

    inputs = {
        "topic_content": topic,
        "pages_numbers": slides,
        "aspect_ratio": aspect_ratio,
        "audience_persona": audience_persona,
    }

    result = research_crew.kickoff(inputs=inputs)
    if isinstance(result, list):
        return result

    if isinstance(result, dict) and "output" in result:
        return result["output"]  # type: ignore[return-value]

    return [result] if isinstance(result, dict) else [{"output": result}]
